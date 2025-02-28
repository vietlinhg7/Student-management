import sqlite3
import re
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime
import csv
import pandas as pd
from tkinter import filedialog
import openpyxl
import logging
import os

# Add after imports
VERSION = "3.0.0"
BUILD_DATE = "21/02/2025"  # Update this when building new versions

# Create logs directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/student_manager_{datetime.now().strftime("%Y%m%d")}.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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

# Create settings table for dynamic options
cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        category TEXT,
        value TEXT,
        UNIQUE(category, value)
    )
''')

# Add after database connection
cursor.execute('''
    CREATE TABLE IF NOT EXISTS config (
        key TEXT PRIMARY KEY,
        value TEXT,
        description TEXT
    )
''')

# Initialize default values if table is empty
def init_default_settings():
    default_values = {
        'faculty': ["Khoa Luật", "Khoa Tiếng Anh thương mại", "Khoa Tiếng Nhật", "Khoa Tiếng Pháp"],
        'status': ["Đang học", "Đã tốt nghiệp", "Đã thôi học", "Tạm dừng học"],
        'program': ["Cử nhân", "Thạc sĩ", "Tiến sĩ"]
    }
    
    cursor.execute("SELECT COUNT(*) FROM settings")
    if cursor.fetchone()[0] == 0:
        for category, values in default_values.items():
            for value in values:
                cursor.execute("INSERT INTO settings (category, value) VALUES (?, ?)", 
                             (category, value))
        conn.commit()

init_default_settings()

# Add default config values if empty
def init_default_config():
    default_config = {
        'allowed_email_domains': '@student.university.edu.vn',
        'phone_pattern': r'^(\+84|0)[3|5|7|8|9][0-9]{8}$',
        'deletion_window_minutes': '30',
        'status_transitions': '''
            {
                "Đang học": ["Bảo lưu", "Tốt nghiệp", "Đình chỉ"],
                "Bảo lưu": ["Đang học", "Đình chỉ"],
                "Đình chỉ": [],
                "Tốt nghiệp": []
            }
        ''',
        'enable_rules': 'true',
        'school_name': 'Trường Đại học ABC'
    }
    
    cursor.execute("SELECT COUNT(*) FROM config")
    if cursor.fetchone()[0] == 0:
        for key, value in default_config.items():
            cursor.execute(
                "INSERT INTO config (key, value) VALUES (?, ?)", 
                (key, value)
            )
        conn.commit()

init_default_config()

# Replace the constants with functions to get values from database
def get_valid_options(category):
    cursor.execute("SELECT value FROM settings WHERE category = ?", (category,))
    return [row[0] for row in cursor.fetchall()]

# Constants
VALID_GENDERS = ["Nam", "Nữ", "Khác"]  # This remains static

# Function to get current valid options
def get_current_valid_options():
    return {
        'faculty': get_valid_options('faculty'),
        'status': get_valid_options('status'),
        'program': get_valid_options('program')
    }

# Validation functions
def get_config(key, default=None):
    cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
    result = cursor.fetchone()
    return result[0] if result else default

def is_valid_email(email):
    allowed_domains = get_config('allowed_email_domains', '@student.university.edu.vn')
    if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
        return False
    return any(email.endswith(domain.strip()) for domain in allowed_domains.split(','))

def is_valid_phone(phone):
    pattern = get_config('phone_pattern', r'^(\+84|0)[3|5|7|8|9][0-9]{8}$')
    return re.match(pattern, phone) is not None

def is_valid_status_transition(old_status, new_status):
    if get_config('enable_rules', 'true').lower() != 'true':
        return True
        
    import json
    transitions = json.loads(get_config('status_transitions', '{}'))
    allowed = transitions.get(old_status, [])
    return new_status in allowed

def is_valid_date(date_str):
    try:
        datetime.strptime(date_str, '%d/%m/%Y')
        return True
    except ValueError:
        return False

def log_status_change(mssv, old_status, new_status):
    logger.info(f"Status change for {mssv}: {old_status} -> {new_status}")
    # Here you would add code to send notifications
    # For example:
    # send_email_notification(mssv, old_status, new_status)
    # send_sms_notification(mssv, old_status, new_status)

def can_delete_student(mssv):
    if get_config('enable_rules', 'true').lower() != 'true':
        return True
        
    deletion_window = int(get_config('deletion_window_minutes', '30'))
    cursor.execute("""
        SELECT created_at FROM students 
        WHERE mssv = ? AND 
        datetime(created_at) >= datetime('now', ?) 
    """, (mssv, f'-{deletion_window} minutes'))
    return cursor.fetchone() is not None

class StudentApp:
    def __init__(self, root):
        logger.info(f"Starting Student Management Application v{VERSION} (Build: {BUILD_DATE})")
        self.root = root
        school_name = get_config('school_name', 'Trường Đại học ABC')
        self.root.title(f"{school_name} - Quản Lý Sinh Viên - v{VERSION}")
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
        
        # Main buttons frame
        main_btns = tk.Frame(self.btn_frame)
        main_btns.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        buttons = [
            ("Thêm Sinh Viên", self.show_add_student),
            ("Xóa Sinh Viên", self.show_delete_student),
            ("Cập Nhật Sinh Viên", self.show_update_student),
            ("Tìm Kiếm Sinh Viên", self.show_search_student),
            ("Quản lý Danh mục", self.show_manage_options),
            ("Nhập/Xuất Dữ liệu", self.show_import_export),
            ("Cấu hình hệ thống", self.show_config_management)
        ]
        
        for i, (text, command) in enumerate(buttons):
            btn = tk.Button(main_btns, text=text, command=command, width=15)
            btn.pack(side=tk.LEFT, padx=5)
        
        # Version info button (right-aligned)
        version_btn = tk.Button(self.btn_frame, text="v" + VERSION, 
                              command=self.show_version_info,
                              width=8, relief=tk.FLAT)
        version_btn.pack(side=tk.RIGHT, padx=5)

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
        
        # Add search by MSSV
        tk.Label(search_frame, text="MSSV:").pack(side=tk.LEFT, padx=5)
        self.search_entry = tk.Entry(search_frame)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Button(search_frame, text="Tìm theo MSSV", 
                 command=self.search_student).pack(side=tk.LEFT, padx=5)
        
        # Add advanced search frame
        advanced_frame = tk.Frame(self.current_frame)
        advanced_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Add faculty search
        tk.Label(advanced_frame, text="Khoa:").pack(side=tk.LEFT, padx=5)
        self.faculty_search = ttk.Combobox(advanced_frame, values=get_valid_options('faculty'))
        self.faculty_search.pack(side=tk.LEFT, padx=5)
        
        # Add name search
        tk.Label(advanced_frame, text="Tên SV:").pack(side=tk.LEFT, padx=5)
        self.name_search = tk.Entry(advanced_frame)
        self.name_search.pack(side=tk.LEFT, padx=5)
        
        tk.Button(advanced_frame, text="Tìm kiếm nâng cao", 
                 command=self.advanced_search).pack(side=tk.LEFT, padx=5)
        
        # Add treeview to display results
        self.create_results_tree()

    def create_results_tree(self):
        # Create treeview frame
        tree_frame = tk.Frame(self.current_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create treeview with scrollbar
        self.tree = ttk.Treeview(tree_frame, columns=(
            "mssv", "name", "dob", "gender", "faculty", "course",
            "program", "status"
        ), show='headings')
        
        # Add scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid layout
        self.tree.grid(column=0, row=0, sticky='nsew')
        vsb.grid(column=1, row=0, sticky='ns')
        hsb.grid(column=0, row=1, sticky='ew')
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)
        
        # Configure columns
        columns = {
            "mssv": "MSSV",
            "name": "Họ Tên",
            "dob": "Ngày sinh",
            "gender": "Giới tính",
            "faculty": "Khoa",
            "course": "Khóa",
            "program": "Chương trình",
            "status": "Tình trạng"
        }
        
        for col, heading in columns.items():
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=100)
        
        # Bind double-click event to show full student info
        self.tree.bind('<Double-1>', self.show_selected_student)

    def advanced_search(self):
        faculty = self.faculty_search.get().strip()
        name = self.name_search.get().strip()
        
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if not faculty and not name:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập ít nhất một điều kiện tìm kiếm!")
            return
        
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
            messagebox.showinfo("Thông báo", "Không tìm thấy kết quả nào!")
            return
        
        # Display results in treeview
        for student in results:
            self.tree.insert('', 'end', values=(
                student[1],  # mssv
                student[2],  # name
                student[3],  # dob
                student[4],  # gender
                student[5],  # faculty
                student[6],  # course
                student[7],  # program
                student[11]  # status
            ))

    def show_selected_student(self, event):
        selected_item = self.tree.selection()
        if not selected_item:
            return
        
        # Get MSSV from selected item
        mssv = self.tree.item(selected_item[0])['values'][0]
        
        # Fetch and display full student info
        cursor.execute("SELECT * FROM students WHERE mssv = ?", (mssv,))
        student = cursor.fetchone()
        if student:
            self.display_student_info(student)

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
        
        current_options = get_current_valid_options()
        
        # Left column fields
        left_fields = [
            ("MSSV", None),
            ("Họ Tên", None),
            ("Ngày sinh", "dd/mm/yyyy"),
            ("Giới tính", VALID_GENDERS),
            ("Khoa", current_options['faculty']),
            ("Khóa", None)
        ]

        # Right column fields
        right_fields = [
            ("Chương trình", current_options['program']),
            ("Địa chỉ", None),
            ("Email", None),
            ("Số điện thoại", None),
            ("Tình trạng", current_options['status'])
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
        
        current_options = get_current_valid_options()
        
        # Left column fields
        left_fields = [
            ("Họ Tên", None),
            ("Ngày sinh", "dd/mm/yyyy"),
            ("Giới tính", VALID_GENDERS),
            ("Khoa", current_options['faculty']),
            ("Khóa", None)
        ]

        # Right column fields
        right_fields = [
            ("Chương trình", current_options['program']),
            ("Địa chỉ", None),
            ("Email", None),
            ("Số điện thoại", None),
            ("Tình trạng", current_options['status'])
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
            logger.warning(f"Update failed - Empty name for MSSV: {mssv}")
            messagebox.showerror("Lỗi", "Họ Tên không được để trống!")
            return
        if not is_valid_date(data["Ngày sinh"]):
            messagebox.showerror("Lỗi", "Ngày sinh không hợp lệ! Định dạng: dd/mm/yyyy")
            return
        if data["Khoa"] not in get_valid_options('faculty'):
            messagebox.showerror("Lỗi", "Khoa không hợp lệ!")
            return
        if data["Tình trạng"] not in get_valid_options('status'):
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
            logger.info(f"Updated student: {mssv} - {data['Họ Tên']}")
            messagebox.showinfo("Thành công", "Cập nhật thông tin sinh viên thành công!")
            self.refresh_tree()
            
            # Clear entries
            for entry in self.update_entries.values():
                entry.delete(0, tk.END)
                
        except sqlite3.Error as e:
            logger.error(f"Database error while updating student {mssv}: {str(e)}")
            messagebox.showerror("Lỗi", f"Lỗi khi cập nhật: {str(e)}")
        
        tk.Button(self.current_frame, text="Tìm Kiếm", command=self.search_student).pack(side=tk.LEFT, padx=5)

    def validate_input(self, data):
        if not data["MSSV"] or not data["Họ Tên"]:
            return "MSSV và Họ Tên không được để trống!"
        if not is_valid_date(data["Ngày sinh"]):
            return "Ngày sinh không hợp lệ! Định dạng: dd/mm/yyyy"
        if data["Khoa"] not in get_valid_options('faculty'):
            return "Khoa không hợp lệ!"
        if data["Tình trạng"] not in get_valid_options('status'):
            return "Tình trạng không hợp lệ!"
        if data["Chương trình"] and data["Chương trình"] not in get_valid_options('program'):
            return "Chương trình không hợp lệ!"
        if not is_valid_email(data["Email"]):
            return "Email không hợp lệ!"
        if not is_valid_phone(data["Số điện thoại"]):
            return "Số điện thoại không hợp lệ (10-11 số)!"
        return None

    def add_student(self):
        data = {key: entry.get().strip() for key, entry in self.entries.items()}
        
        error = self.validate_input(data)
        if error:
            logger.warning(f"Invalid student data: {error}")
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
            logger.info(f"Added new student: {data['MSSV']} - {data['Họ Tên']}")
            messagebox.showinfo("Thành công", "Thêm sinh viên thành công!")
            self.refresh_tree()
            
            for entry in self.entries.values():
                entry.delete(0, tk.END)
                
        except sqlite3.IntegrityError:
            logger.error(f"Failed to add student - Duplicate MSSV: {data['MSSV']}")
            messagebox.showerror("Lỗi", "MSSV đã tồn tại!")
    
    def delete_student(self):
        mssv = self.mssv_delete_entry.get().strip()
        if not mssv:
            logger.warning("Delete attempted without MSSV")
            messagebox.showerror("Lỗi", "Vui lòng nhập MSSV!")
            return
            
        cursor.execute("SELECT name FROM students WHERE mssv = ?", (mssv,))
        student = cursor.fetchone()
        if not student:
            logger.warning(f"Delete attempted - Student not found: {mssv}")
            messagebox.showerror("Lỗi", "Không tìm thấy sinh viên!")
            return
            
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa sinh viên này?"):
            try:
                cursor.execute("DELETE FROM students WHERE mssv = ?", (mssv,))
                conn.commit()
                logger.info(f"Deleted student: {mssv} - {student[0]}")
                messagebox.showinfo("Thành công", "Xóa sinh viên thành công!")
                self.refresh_tree()
                self.mssv_delete_entry.delete(0, tk.END)
            except sqlite3.Error as e:
                logger.error(f"Error deleting student {mssv}: {str(e)}")
                messagebox.showerror("Lỗi", f"Lỗi khi xóa: {str(e)}")

    def show_manage_options(self):
        self.clear_frame()
        self.current_frame = tk.LabelFrame(self.main_container, text="Quản lý Danh mục")
        self.current_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        categories = {
            'faculty': 'Khoa',
            'status': 'Tình trạng',
            'program': 'Chương trình'
        }
        
        for i, (category, title) in enumerate(categories.items()):
            frame = tk.LabelFrame(self.current_frame, text=title)
            frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Create listbox to show current values
            listbox = tk.Listbox(frame, height=5)
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Load current values
            for value in get_valid_options(category):
                listbox.insert(tk.END, value)
            
            btn_frame = tk.Frame(frame)
            btn_frame.pack(side=tk.LEFT, padx=5)
            
            entry = tk.Entry(btn_frame)
            entry.pack(pady=2)
            
            tk.Button(btn_frame, text="Thêm", 
                     command=lambda c=category, e=entry, lb=listbox: self.add_option(c, e, lb)
                    ).pack(fill=tk.X, pady=2)
            tk.Button(btn_frame, text="Xóa", 
                     command=lambda c=category, lb=listbox: self.delete_option(c, lb)
                    ).pack(fill=tk.X, pady=2)

    def add_option(self, category, entry, listbox):
        value = entry.get().strip()
        if not value:
            messagebox.showerror("Lỗi", "Vui lòng nhập giá trị!")
            return
        
        try:
            cursor.execute("INSERT INTO settings (category, value) VALUES (?, ?)", 
                          (category, value))
            conn.commit()
            listbox.insert(tk.END, value)
            entry.delete(0, tk.END)
            
            # Update the comboboxes in add/update forms
            self._update_comboboxes(category)
            
        except sqlite3.IntegrityError:
            messagebox.showerror("Lỗi", "Giá trị này đã tồn tại!")

    def delete_option(self, category, listbox):
        selection = listbox.curselection()
        if not selection:
            messagebox.showerror("Lỗi", "Vui lòng chọn giá trị cần xóa!")
            return
        
        value = listbox.get(selection[0])
        if messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa '{value}'?"):
            cursor.execute("DELETE FROM settings WHERE category = ? AND value = ?", 
                          (category, value))
            conn.commit()
            listbox.delete(selection[0])
            
            # Update the comboboxes in add/update forms
            self._update_comboboxes(category)

    def _update_comboboxes(self, category):
        """Update comboboxes with new values after adding/deleting options"""
        new_values = get_valid_options(category)
        
        # Update add form comboboxes if they exist
        if hasattr(self, 'entries'):
            category_map = {
                'faculty': 'Khoa',
                'status': 'Tình trạng',
                'program': 'Chương trình'
            }
            field_name = category_map.get(category)
            if field_name and field_name in self.entries:
                self.entries[field_name]['values'] = new_values
        
        # Update update form comboboxes if they exist
        if hasattr(self, 'update_entries'):
            field_name = category_map.get(category)
            if field_name and field_name in self.update_entries:
                self.update_entries[field_name]['values'] = new_values

    def show_import_export(self):
        self.clear_frame()
        self.current_frame = tk.LabelFrame(self.main_container, text="Nhập/Xuất Dữ Liệu")
        self.current_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Import section
        import_frame = tk.LabelFrame(self.current_frame, text="Nhập dữ liệu")
        import_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(import_frame, text="Nhập từ CSV", 
                 command=lambda: self.import_data('csv')).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(import_frame, text="Nhập từ Excel", 
                 command=lambda: self.import_data('excel')).pack(side=tk.LEFT, padx=5, pady=5)
        
        # Export section
        export_frame = tk.LabelFrame(self.current_frame, text="Xuất dữ liệu")
        export_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(export_frame, text="Xuất ra CSV", 
                 command=lambda: self.export_data('csv')).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(export_frame, text="Xuất ra Excel", 
                 command=lambda: self.export_data('excel')).pack(side=tk.LEFT, padx=5, pady=5)

    def import_data(self, format_type):
        filename = filedialog.askopenfilename(
            filetypes=[('CSV files', '*.csv')] if format_type == 'csv' else [('Excel files', '*.xlsx')]
        )
        if not filename:
            return
            
        logger.info(f"Importing data from {filename}")
        try:
            if format_type == 'csv':
                df = pd.read_csv(filename)
            else:
                df = pd.read_excel(filename)
                
            # Validate column names
            required_columns = [
                'mssv', 'name', 'dob', 'gender', 'faculty', 'course',
                'program', 'address', 'email', 'phone', 'status'
            ]
            
            if not all(col in df.columns for col in required_columns):
                messagebox.showerror("Lỗi", "File không đúng định dạng! Thiếu cột bắt buộc.")
                return
                
            # Validate and import data
            success_count = 0
            error_count = 0
            
            for _, row in df.iterrows():
                data = {
                    "MSSV": str(row['mssv']),
                    "Họ Tên": str(row['name']),
                    "Ngày sinh": str(row['dob']),
                    "Giới tính": str(row['gender']),
                    "Khoa": str(row['faculty']),
                    "Khóa": str(row['course']),
                    "Chương trình": str(row['program']),
                    "Địa chỉ": str(row['address']),
                    "Email": str(row['email']),
                    "Số điện thoại": str(row['phone']),
                    "Tình trạng": str(row['status'])
                }
                
                error = self.validate_input(data)
                if error:
                    error_count += 1
                    continue
                    
                try:
                    cursor.execute('''
                        INSERT INTO students (mssv, name, dob, gender, faculty, course,
                                            program, address, email, phone, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        data["MSSV"], data["Họ Tên"], data["Ngày sinh"], data["Giới tính"],
                        data["Khoa"], data["Khóa"], data["Chương trình"], data["Địa chỉ"],
                        data["Email"], data["Số điện thoại"], data["Tình trạng"]
                    ))
                    success_count += 1
                except sqlite3.IntegrityError:
                    error_count += 1
                    
            conn.commit()
            logger.info(f"Import completed: {success_count} successful, {error_count} failed")
            messagebox.showinfo("Thành công", 
                              f"Đã nhập {success_count} sinh viên!\nLỗi: {error_count} sinh viên")
            self.refresh_tree()
            
        except Exception as e:
            logger.error(f"Error during import: {str(e)}")
            messagebox.showerror("Lỗi", f"Lỗi khi đọc file: {str(e)}")

    def export_data(self, format_type):
        filename = filedialog.asksaveasfilename(
            filetypes=[('CSV files', '*.csv')] if format_type == 'csv' else [('Excel files', '*.xlsx')]
        )
        if not filename:
            return
            
        logger.info(f"Exporting data to {filename}")
        try:
            cursor.execute('''
                SELECT mssv, name, dob, gender, faculty, course,
                       program, address, email, phone, status
                FROM students
            ''')
            rows = cursor.fetchall()
            
            if not rows:
                messagebox.showinfo("Thông báo", "Không có dữ liệu để xuất!")
                return
                
            # Convert to DataFrame
            df = pd.DataFrame(rows, columns=[
                'mssv', 'name', 'dob', 'gender', 'faculty', 'course',
                'program', 'address', 'email', 'phone', 'status'
            ])
            
            # Export based on format
            if format_type == 'csv':
                df.to_csv(filename, index=False, encoding='utf-8-sig')
            else:
                df.to_excel(filename, index=False)
                
            logger.info(f"Export completed successfully to {filename}")
            messagebox.showinfo("Thành công", "Xuất dữ liệu thành công!")
            
        except Exception as e:
            logger.error(f"Error during export: {str(e)}")
            messagebox.showerror("Lỗi", f"Lỗi khi xuất file: {str(e)}")

    def show_version_info(self):
        """Show version information dialog"""
        version_text = f"""Quản Lý Sinh Viên
Version: {VERSION}
Build Date: {BUILD_DATE}
    """
        messagebox.showinfo("Thông tin phiên bản", version_text)

    def show_config_management(self):
        self.clear_frame()
        self.current_frame = tk.LabelFrame(self.main_container, text="Cấu hình hệ thống")
        self.current_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create scrollable frame
        canvas = tk.Canvas(self.current_frame)
        scrollbar = ttk.Scrollbar(self.current_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Add config entries
        cursor.execute("SELECT key, value FROM config")
        self.config_entries = {}
        
        for i, (key, value) in enumerate(cursor.fetchall()):
            frame = ttk.Frame(scrollable_frame)
            frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(frame, text=f"{key}:").pack(side=tk.LEFT, padx=5)
            entry = ttk.Entry(frame, width=50)
            entry.insert(0, value)
            entry.pack(side=tk.LEFT, padx=5)
            self.config_entries[key] = entry
        
        # Save button
        ttk.Button(scrollable_frame, text="Lưu cấu hình", 
                   command=self.save_config).pack(pady=10)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def save_config(self):
        try:
            for key, entry in self.config_entries.items():
                cursor.execute(
                    "UPDATE config SET value = ? WHERE key = ?",
                    (entry.get(), key)
                )
            conn.commit()
            messagebox.showinfo("Thành công", "Đã lưu cấu hình!")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi khi lưu cấu hình: {str(e)}")

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

if __name__:
    main()