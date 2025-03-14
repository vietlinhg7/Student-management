import sqlite3
from tkinter import messagebox, filedialog
from database_initialization import conn, cursor
from app_logging import logger
from datetime import datetime
from fpdf import FPDF
import markdown

def with_db_connection(func):
    """Decorator to manage database connections."""
    def wrapper(*args, **kwargs):
        conn = sqlite3.connect("students.db")
        try:
            result = func(conn, *args, **kwargs)
        finally:
            conn.close()
        return result
    return wrapper

@with_db_connection
def get_config(conn, key, default=None):
    """Retrieve a configuration value from the database."""
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
    result = cursor.fetchone()
    return result[0] if result else default

@with_db_connection
def can_delete_student(conn, mssv):
    """Check if a student can be deleted within the allowed time window."""
    deletion_window = int(get_config(conn, 'deletion_window_minutes', '30'))
    cursor = conn.cursor()
    cursor.execute("""
        SELECT created_at FROM students 
        WHERE mssv = ? AND 
        datetime(created_at) >= datetime('now', ?) 
    """, (mssv, f'-{deletion_window} minutes'))
    return cursor.fetchone() is not None

def get_valid_options(category):
    """Retrieve valid options for a given category from the database."""
    cursor.execute("SELECT value FROM settings WHERE category = ?", (category,))
    return [row[0] for row in cursor.fetchall()]

def delete_category(category, value):
    """Delete a category value if no students are associated with it."""
    cursor.execute(f"SELECT COUNT(*) FROM students WHERE {category} = ?", (value,))
    if cursor.fetchone()[0] > 0:
        messagebox.showerror("Lỗi", f"Không thể xóa {category} vì có sinh viên liên quan!")
        return

    cursor.execute(f"DELETE FROM settings WHERE category = ? AND value = ?", (category, value))
    conn.commit()
    logger.info(f"Deleted {category}: {value}")
    messagebox.showinfo("Thành công", f"Đã xóa {category}: {value}")

def export_student_status(mssv, format_type):
    """Export student status confirmation in the specified format."""
    cursor.execute("SELECT * FROM students WHERE mssv = ?", (mssv,))
    student = cursor.fetchone()
    if not student:
        messagebox.showerror("Lỗi", "Không tìm thấy sinh viên!")
        return

    school_name = get_config('school_name', 'Trường Đại học ABC')
    confirmation_data = f"""
    **TRƯỜNG ĐẠI HỌC {school_name}**  
    **PHÒNG ĐÀO TẠO**  
    📍 Địa chỉ: [Địa chỉ trường]  
    📞 Điện thoại: [Số điện thoại] | 📧 Email: [Email liên hệ]  

    ### **GIẤY XÁC NHẬN TÌNH TRẠNG SINH VIÊN**  

    Trường Đại học {school_name} xác nhận:  

    **1. Thông tin sinh viên:**  
    - **Họ và tên:** {student[2]}  
    - **Mã số sinh viên:** {student[1]}  
    - **Ngày sinh:** {student[3]}  
    - **Giới tính:** {student[4]}  
    - **Khoa:** {student[5]}  
    - **Chương trình đào tạo:** {student[7]}  
    - **Khóa:** {student[6]}  

    **2. Tình trạng sinh viên hiện tại:**  
    - {student[11]}  

    📅 Ngày cấp: {datetime.now().strftime('%d/%m/%Y')}  

    🖋 **Trưởng Phòng Đào Tạo**  
    (Ký, ghi rõ họ tên, đóng dấu)
    """

    if format_type == "html":
        filename = filedialog.asksaveasfilename(defaultextension=".html", filetypes=[("HTML files", "*.html")])
        if filename:
            with open(filename, "w", encoding="utf-8") as file:
                file.write(markdown.markdown(confirmation_data))
            messagebox.showinfo("Thành công", f"Đã xuất giấy xác nhận ra {filename}")

    elif format_type == "pdf":
        filename = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if filename:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            for line in confirmation_data.split("\n"):
                pdf.cell(200, 10, txt=line, ln=True, align="L")
            pdf.output(filename)
            messagebox.showinfo("Thành công", f"Đã xuất giấy xác nhận ra {filename}")

def add_student_to_db(data, cursor, conn):
    """Add a new student to the database."""
    cursor.execute('''
        INSERT INTO students (mssv, name, dob, gender, faculty, course, program, 
                              address, email, phone, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data["MSSV"], data["Họ Tên"], data["Ngày sinh"], data["Giới tính"],
        data["Khoa"], data["Khóa"], data["Chương trình"], data["Địa chỉ"],
        data["Email"], data["Số điện thoại"], data["Tình trạng"]
    ))
    conn.commit()


def delete_student_from_db(mssv, cursor, conn):
    """Delete a student from the database."""
    cursor.execute("DELETE FROM students WHERE mssv = ?", (mssv,))
    conn.commit()


def update_student_in_db(mssv, data, cursor, conn):
    """Update a student's information in the database."""
    cursor.execute('''
        UPDATE students 
        SET name = ?, dob = ?, gender = ?, faculty = ?, course = ?,
            program = ?, address = ?, email = ?, phone = ?, status = ?
        WHERE mssv = ?
    ''', (
        data["Họ Tên"], data["Ngày sinh"], data["Giới tính"],
        data["Khoa"], data["Khóa"], data["Chương trình"],
        data["Địa chỉ"], data["Email"], data["Số điện thoại"],
        data["Tình trạng"], mssv
    ))
    conn.commit()


def fetch_student_by_mssv(mssv, cursor):
    """Fetch a student's information by MSSV."""
    cursor.execute("SELECT * FROM students WHERE mssv = ?", (mssv,))
    return cursor.fetchone()

def perform_advanced_search(faculty, name, cursor):
    """Perform an advanced search based on faculty and name."""
    if not faculty and not name:
        return [], "Vui lòng nhập ít nhất một điều kiện tìm kiếm!"

    # Build query based on search conditions
    query = "SELECT * FROM students WHERE 1=1"
    params = []

    if faculty:
        query += " AND faculty = ?"
        params.append(faculty)

    if name:
        query += " AND name LIKE ?"
        params.append(f"%{name}%")

    cursor.execute(query, params)
    results = cursor.fetchall()

    if not results:
        return [], "Không tìm thấy kết quả nào!"

    return results, None