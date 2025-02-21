import sqlite3
import re
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime

# Database connection
conn = sqlite3.connect("students.db")
cursor = conn.cursor()

# Create students table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mssv TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        dob TEXT,
        gender TEXT,
        faculty TEXT,
        course TEXT,
        program TEXT,
        address TEXT,
        email TEXT,
        phone TEXT,
        status TEXT
    )
''')
conn.commit()

# Constants
VALID_FACULTIES = ["Khoa Luật", "Khoa Tiếng Anh thương mại", "Khoa Tiếng Nhật", "Khoa Tiếng Pháp"]
VALID_STATUSES = ["Đang học", "Đã tốt nghiệp", "Đã thôi học", "Tạm dừng học"]
VALID_GENDERS = ["Nam", "Nữ", "Khác"]

# Validation functions
def is_valid_email(email):
    return re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email) is not None

def is_valid_phone(phone):
    return re.match(r"^\d{10,11}$", phone) is not None

def is_valid_date(date_str):
    try:
        datetime.strptime(date_str, '%d/%m/%Y')
        return True
    except ValueError:
        return False

class StudentApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Quản Lý Sinh Viên")
        self.root.geometry("1000x600")
        
        # Create main container
        self.main_container = tk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.create_main_buttons()
        self.current_frame = None
        self.student_info_frame = None

    def create_main_buttons(self):
        self.btn_frame = tk.Frame(self.main_container)
        self.btn_frame.pack(fill=tk.X, pady=10)
        
        buttons = [
            ("Thêm Sinh Viên", self.show_add_student),
            ("Xóa Sinh Viên", self.show_delete_student),
            ("Cập Nhật Sinh Viên", self.show_update_student),
            ("Tìm Kiếm Sinh Viên", self.show_search_student)
        ]
        
        for i, (text, command) in enumerate(buttons):
            btn = tk.Button(self.btn_frame, text=text, command=command, width=15)
            btn.pack(side=tk.LEFT, padx=5)

    def display_student_info(self, student):
        # Clear previous student info if exists
        if self.student_info_frame:
            self.student_info_frame.destroy()

        # Create new frame for student info
        self.student_info_frame = tk.LabelFrame(self.main_container, text="Thông tin sinh viên")
        self.student_info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Create two columns for information display
        left_frame = tk.Frame(self.student_info_frame)
        right_frame = tk.Frame(self.student_info_frame)
        left_frame.pack(side=tk.LEFT, padx=20, pady=10, fill=tk.BOTH, expand=True)
        right_frame.pack(side=tk.LEFT, padx=20, pady=10, fill=tk.BOTH, expand=True)

        # Define fields and their values
        left_fields = [
            ("MSSV", student[1]),
            ("Họ Tên", student[2]),
            ("Ngày sinh", student[3]),
            ("Giới tính", student[4]),
            ("Khoa", student[5]),
            ("Khóa", student[6])
        ]

        right_fields = [
            ("Chương trình", student[7]),
            ("Địa chỉ", student[8]),
            ("Email", student[9]),
            ("Số điện thoại", student[10]),
            ("Tình trạng", student[11])
        ]

        # Display left column information
        for i, (label, value) in enumerate(left_fields):
            tk.Label(left_frame, text=f"{label}:", anchor="e", font=("Arial", 10, "bold")).grid(
                row=i, column=0, sticky="e", padx=5, pady=5)
            tk.Label(left_frame, text=value, anchor="w").grid(
                row=i, column=1, sticky="w", padx=5, pady=5)

        # Display right column information
        for i, (label, value) in enumerate(right_fields):
            tk.Label(right_frame, text=f"{label}:", anchor="e", font=("Arial", 10, "bold")).grid(
                row=i, column=0, sticky="e", padx=5, pady=5)
            tk.Label(right_frame, text=value, anchor="w").grid(
                row=i, column=1, sticky="w", padx=5, pady=5)

    def clear_frame(self):
        # Destroy all widgets except the button frame
        for widget in self.main_container.winfo_children():
            if widget != self.btn_frame:
                widget.destroy()
        
        self.current_frame = None
        self.student_info_frame = None

    def show_search_student(self):
        self.clear_frame()
        self.current_frame = tk.LabelFrame(self.main_container, text="Tìm Kiếm Sinh Viên")
        self.current_frame.pack(fill=tk.X, pady=10)
        
        # Create search frame
        search_frame = tk.Frame(self.current_frame)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(search_frame, text="MSSV:").pack(side=tk.LEFT, padx=5)
        self.search_entry = tk.Entry(search_frame)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Button(search_frame, text="Tìm Kiếm", command=self.search_student).pack(side=tk.LEFT, padx=5)

    def search_student(self):
        mssv = self.search_entry.get().strip()
        if not mssv:
            messagebox.showerror("Lỗi", "Vui lòng nhập MSSV!")
            return
            
        cursor.execute("SELECT * FROM students WHERE mssv = ?", (mssv,))
        student = cursor.fetchone()
        
        if student:
            self.display_student_info(student)
        else:
            messagebox.showinfo("Thông báo", "Không tìm thấy sinh viên!")
            if self.student_info_frame:
                self.student_info_frame.destroy()
    
    def show_add_student(self):
        self.clear_frame()
        self.current_frame = tk.LabelFrame(self.main_container, text="Thêm Sinh Viên Mới")
        self.current_frame.pack(fill=tk.X, pady=10)

        # Create two columns for better layout
        left_frame = tk.Frame(self.current_frame)
        right_frame = tk.Frame(self.current_frame)
        left_frame.pack(side=tk.LEFT, padx=10, pady=5)
        right_frame.pack(side=tk.LEFT, padx=10, pady=5)

        self.entries = {}
        
        # Left column fields
        left_fields = [
            ("MSSV", None),
            ("Họ Tên", None),
            ("Ngày sinh", "dd/mm/yyyy"),
            ("Giới tính", VALID_GENDERS),
            ("Khoa", VALID_FACULTIES),
            ("Khóa", None)
        ]

        # Right column fields
        right_fields = [
            ("Chương trình", None),
            ("Địa chỉ", None),
            ("Email", None),
            ("Số điện thoại", None),
            ("Tình trạng", VALID_STATUSES)
        ]

        # Create left column
        for i, (label, values) in enumerate(left_fields):
            tk.Label(left_frame, text=label + ":").grid(row=i, column=0, sticky="e", padx=5, pady=2)
            if values:
                self.entries[label] = ttk.Combobox(left_frame, values=values)
            else:
                self.entries[label] = tk.Entry(left_frame)
            self.entries[label].grid(row=i, column=1, sticky="w", padx=5, pady=2)

        # Create right column
        for i, (label, values) in enumerate(right_fields):
            tk.Label(right_frame, text=label + ":").grid(row=i, column=0, sticky="e", padx=5, pady=2)
            if values:
                self.entries[label] = ttk.Combobox(right_frame, values=values)
            else:
                self.entries[label] = tk.Entry(right_frame)
            self.entries[label].grid(row=i, column=1, sticky="w", padx=5, pady=2)

        # Add button at the bottom
        tk.Button(self.current_frame, text="Thêm Sinh Viên", command=self.add_student).pack(pady=10)

    def show_delete_student(self):
        self.clear_frame()
        self.current_frame = tk.LabelFrame(self.main_container, text="Xóa Sinh Viên")
        self.current_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(self.current_frame, text="MSSV cần xóa:").pack(side=tk.LEFT, padx=5)
        self.mssv_delete_entry = tk.Entry(self.current_frame)
        self.mssv_delete_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Button(self.current_frame, text="Xóa", command=self.delete_student).pack(side=tk.LEFT, padx=5)

    def show_update_student(self):
        self.clear_frame()
        self.current_frame = tk.LabelFrame(self.main_container, text="Cập Nhật Sinh Viên")
        self.current_frame.pack(fill=tk.X, pady=10)

        # MSSV input frame
        mssv_frame = tk.Frame(self.current_frame)
        mssv_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(mssv_frame, text="MSSV:").pack(side=tk.LEFT, padx=5)
        self.mssv_update_entry = tk.Entry(mssv_frame)
        self.mssv_update_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(mssv_frame, text="Tìm", command=self.fetch_student_for_update).pack(side=tk.LEFT, padx=5)

        # Create update fields container
        self.update_fields_frame = tk.Frame(self.current_frame)
        self.update_fields_frame.pack(fill=tk.X, pady=5)

    def fetch_student_for_update(self):
        mssv = self.mssv_update_entry.get()
        cursor.execute("SELECT * FROM students WHERE mssv = ?", (mssv,))
        student = cursor.fetchone()
        
        if not student:
            messagebox.showerror("Lỗi", "Không tìm thấy sinh viên!")
            return

        # Clear existing update fields
        for widget in self.update_fields_frame.winfo_children():
            widget.destroy()

        # Create two columns for better layout
        left_frame = tk.Frame(self.update_fields_frame)
        right_frame = tk.Frame(self.update_fields_frame)
        left_frame.pack(side=tk.LEFT, padx=10, pady=5)
        right_frame.pack(side=tk.LEFT, padx=10, pady=5)

        self.update_entries = {}
        
        # Left column fields
        left_fields = [
            ("Họ Tên", None),
            ("Ngày sinh", "dd/mm/yyyy"),
            ("Giới tính", VALID_GENDERS),
            ("Khoa", VALID_FACULTIES),
            ("Khóa", None)
        ]

        # Right column fields
        right_fields = [
            ("Chương trình", None),
            ("Địa chỉ", None),
            ("Email", None),
            ("Số điện thoại", None),
            ("Tình trạng", VALID_STATUSES)
        ]

        # Create left column
        for i, (field, values) in enumerate(left_fields):
            tk.Label(left_frame, text=field + ":").grid(row=i, column=0, sticky="e", padx=5, pady=2)
            if values:
                self.update_entries[field] = ttk.Combobox(left_frame, values=values)
            else:
                self.update_entries[field] = tk.Entry(left_frame)
            self.update_entries[field].grid(row=i, column=1, sticky="w", padx=5, pady=2)

        # Create right column
        for i, (field, values) in enumerate(right_fields):
            tk.Label(right_frame, text=field + ":").grid(row=i, column=0, sticky="e", padx=5, pady=2)
            if values:
                self.update_entries[field] = ttk.Combobox(right_frame, values=values)
            else:
                self.update_entries[field] = tk.Entry(right_frame)
            self.update_entries[field].grid(row=i, column=1, sticky="w", padx=5, pady=2)

        # Fill in current values
        field_indices = {
            "Họ Tên": 2,
            "Ngày sinh": 3,
            "Giới tính": 4,
            "Khoa": 5,
            "Khóa": 6,
            "Chương trình": 7,
            "Địa chỉ": 8,
            "Email": 9,
            "Số điện thoại": 10,
            "Tình trạng": 11
        }

        for field, idx in field_indices.items():
            self.update_entries[field].insert(0, student[idx])

        tk.Button(self.update_fields_frame, text="Cập Nhật", 
                 command=lambda: self.update_student(mssv)).pack(pady=10)

    def update_student(self, mssv):
        data = {key: entry.get().strip() for key, entry in self.update_entries.items()}
        
        # Validate input
        if not data["Họ Tên"]:
            messagebox.showerror("Lỗi", "Họ Tên không được để trống!")
            return
        if not is_valid_date(data["Ngày sinh"]):
            messagebox.showerror("Lỗi", "Ngày sinh không hợp lệ! Định dạng: dd/mm/yyyy")
            return
        if data["Khoa"] not in VALID_FACULTIES:
            messagebox.showerror("Lỗi", "Khoa không hợp lệ!")
            return
        if data["Tình trạng"] not in VALID_STATUSES:
            messagebox.showerror("Lỗi", "Tình trạng không hợp lệ!")
            return
        if not is_valid_email(data["Email"]):
            messagebox.showerror("Lỗi", "Email không hợp lệ!")
            return
        if not is_valid_phone(data["Số điện thoại"]):
            messagebox.showerror("Lỗi", "Số điện thoại không hợp lệ (10-11 số)!")
            return

        try:
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
            messagebox.showinfo("Thành công", "Cập nhật thông tin sinh viên thành công!")
            self.refresh_tree()
            
            # Clear entries
            for entry in self.update_entries.values():
                entry.delete(0, tk.END)
                
        except sqlite3.Error as e:
            messagebox.showerror("Lỗi", f"Lỗi khi cập nhật: {str(e)}")
        
        tk.Button(self.current_frame, text="Tìm Kiếm", command=self.search_student).pack(side=tk.LEFT, padx=5)

    def validate_input(self, data):
        if not data["MSSV"] or not data["Họ Tên"]:
            return "MSSV và Họ Tên không được để trống!"
        if not is_valid_date(data["Ngày sinh"]):
            return "Ngày sinh không hợp lệ! Định dạng: dd/mm/yyyy"
        if data["Khoa"] not in VALID_FACULTIES:
            return "Khoa không hợp lệ!"
        if data["Tình trạng"] not in VALID_STATUSES:
            return "Tình trạng không hợp lệ!"
        if not is_valid_email(data["Email"]):
            return "Email không hợp lệ!"
        if not is_valid_phone(data["Số điện thoại"]):
            return "Số điện thoại không hợp lệ (10-11 số)!"
        return None

    def add_student(self):
        data = {key: entry.get().strip() for key, entry in self.entries.items()}
        
        error = self.validate_input(data)
        if error:
            messagebox.showerror("Lỗi", error)
            return

        try:
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
            messagebox.showinfo("Thành công", "Thêm sinh viên thành công!")
            self.refresh_tree()
            
            # Clear entries
            for entry in self.entries.values():
                entry.delete(0, tk.END)
                
        except sqlite3.IntegrityError:
            messagebox.showerror("Lỗi", "MSSV đã tồn tại!")
    
    def delete_student(self):
        mssv = self.mssv_delete_entry.get().strip()
        if not mssv:
            messagebox.showerror("Lỗi", "Vui lòng nhập MSSV!")
            return
            
        cursor.execute("SELECT * FROM students WHERE mssv = ?", (mssv,))
        if not cursor.fetchone():
            messagebox.showerror("Lỗi", "Không tìm thấy sinh viên!")
            return
            
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa sinh viên này?"):
            cursor.execute("DELETE FROM students WHERE mssv = ?", (mssv,))
            conn.commit()
            messagebox.showinfo("Thành công", "Xóa sinh viên thành công!")
            self.refresh_tree()
            self.mssv_delete_entry.delete(0, tk.END)
    

def main():
    try:
        root = tk.Tk()
        app = StudentApp(root)
        
        # Center window on screen
        window_width = 1000
        window_height = 600
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        
        root.mainloop()
    finally:
        conn.close()

if __name__ == "__main__":
    main()