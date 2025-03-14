import sqlite3
import re
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime
import csv
import pandas as pd
from tkinter import filedialog
import openpyxl
from fpdf import FPDF  # For PDF generation
import markdown  # For Markdown generation

from app_logging import logger
from database_operations import get_config, can_delete_student, add_student_to_db, fetch_student_by_mssv, update_student_in_db, delete_student_from_db, get_valid_options, delete_category, export_student_status, perform_advanced_search
from database_initialization import conn, cursor
from validation import validate_student_data

# Constants
VERSION = "4.0.0"
BUILD_DATE = "21/02/2025"  # Update this when building new versions
VALID_GENDERS = ["Nam", "Nữ", "Khác"]  # Static gender options

def create_treeview(parent, columns, headings):
    """Create a TreeView widget with scrollbars."""
    tree = ttk.Treeview(parent, columns=columns, show='headings')
    vsb = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(parent, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    tree.grid(column=0, row=0, sticky='nsew')
    vsb.grid(column=1, row=0, sticky='ns')
    hsb.grid(column=0, row=1, sticky='ew')
    parent.grid_columnconfigure(0, weight=1)
    parent.grid_rowconfigure(0, weight=1)
    for col, heading in headings.items():
        tree.heading(col, text=heading)
        tree.column(col, width=100)
    return tree

def log_status_change(mssv, old_status, new_status):
    """Log status changes for a student."""
    logger.info(f"Status change for {mssv}: {old_status} -> {new_status}")
    # Placeholder for notification logic (e.g., email, SMS)

def send_notification(mssv, message):
    """Send notifications to a student based on their registered preferences."""
    cursor.execute("SELECT email, phone, notification_preferences FROM students WHERE mssv = ?", (mssv,))
    student = cursor.fetchone()
    if not student:
        logger.warning(f"Notification failed - Student not found: {mssv}")
        return

    email, phone, preferences = student
    preferences = preferences.split(",") if preferences else []

    if "email" in preferences and email:
        logger.info(f"Sending email to {email}: {message}")
        # Placeholder for email sending logic

    if "sms" in preferences and phone:
        logger.info(f"Sending SMS to {phone}: {message}")
        # Placeholder for SMS sending logic

    if "zalo" in preferences:
        logger.info(f"Sending Zalo message to {mssv}: {message}")
        # Placeholder for Zalo API integration

def get_current_valid_options():
    """Retrieve all current valid options for dynamic fields."""
    return {
        'faculty': get_valid_options('faculty'),
        'status': get_valid_options('status'),
        'program': get_valid_options('program')
    }

def display_student_info_frame(parent, student):
    """Display student information in a new frame."""
    # Clear previous student info if exists
    for widget in parent.winfo_children():
        widget.destroy()

    # Create new frame for student info
    student_info_frame = tk.LabelFrame(parent, text="Thông tin sinh viên")
    student_info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    # Create two columns for information display
    left_frame = tk.Frame(student_info_frame)
    right_frame = tk.Frame(student_info_frame)
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

    return student_info_frame


def refresh_tree(tree, cursor):
    """Refresh the TreeView with the latest data from the database."""
    # Clear existing items in the TreeView
    for item in tree.get_children():
        tree.delete(item)

    # Fetch all students from the database
    cursor.execute('''
        SELECT mssv, name, dob, gender, faculty, course, program, status
        FROM students
    ''')
    rows = cursor.fetchall()

    # Insert rows into the TreeView
    for row in rows:
        tree.insert('', 'end', values=row)

    logger.info("TreeView refreshed successfully.")





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
        tk.Button(self.current_frame, text="Xuất Giấy Xác Nhận", command=self.show_export_confirmation).pack(pady=10)

    def create_results_tree(self):
        """Create a TreeView widget to display search results."""
        tree_frame = tk.Frame(self.current_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Define columns and headings
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
        
        # Convert columns.keys() to a list
        self.tree = create_treeview(tree_frame, list(columns.keys()), columns)
        self.tree.bind('<Double-1>', self.show_selected_student)

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
            self.student_info_frame = display_student_info_frame(self.main_container, student)

    def advanced_search(self):
        """Perform an advanced search based on faculty and name."""
        # Ensure the tree is initialized
        if not hasattr(self, 'tree') or self.tree is None:
            messagebox.showerror("Lỗi", "Danh sách kết quả chưa được khởi tạo! Vui lòng mở chức năng tìm kiếm trước.")
            return

        faculty = self.faculty_search.get().strip()
        name = self.name_search.get().strip()

        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        results, error_message = perform_advanced_search(faculty, name, cursor)

        if error_message:
            messagebox.showwarning("Cảnh báo", error_message)
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

    def search_student(self):
        mssv = self.search_entry.get().strip()
        if not mssv:
            messagebox.showerror("Lỗi", "Vui lòng nhập MSSV!")
            return
            
        student = fetch_student_by_mssv(mssv, cursor)
        if student:
            self.student_info_frame = display_student_info_frame(self.main_container, student)
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
        error = validate_student_data(data)
        if error:
            logger.warning(f"Update failed - {error}")
            messagebox.showerror("Lỗi", error)
            return

        try:
            update_student_in_db(mssv, data, cursor, conn)
            logger.info(f"Updated student: {mssv} - {data['Họ Tên']}")
            messagebox.showinfo("Thành công", "Cập nhật thông tin sinh viên thành công!")
            
            for entry in self.update_entries.values():
                entry.delete(0, tk.END)
        except sqlite3.Error as e:
            logger.error(f"Database error while updating student {mssv}: {str(e)}")
            messagebox.showerror("Lỗi", f"Lỗi khi cập nhật: {str(e)}")

    def add_student(self):
        data = {key: entry.get().strip() for key, entry in self.entries.items()}
        error = validate_student_data(data)
        if error:
            logger.warning(f"Invalid student data: {error}")
            messagebox.showerror("Lỗi", error)
            return

        try:
            add_student_to_db(data, cursor, conn)
            logger.info(f"Added new student: {data['MSSV']} - {data['Họ Tên']}")
            messagebox.showinfo("Thành công", "Thêm sinh viên thành công!")
            
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
            
        student = fetch_student_by_mssv(mssv, cursor)
        if not student:
            logger.warning(f"Delete attempted - Student not found: {mssv}")
            messagebox.showerror("Lỗi", "Không tìm thấy sinh viên!")
            return
            
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa sinh viên này?"):
            try:
                delete_student_from_db(mssv, cursor, conn)
                logger.info(f"Deleted student: {mssv} - {student[2]}")
                messagebox.showinfo("Thành công", "Xóa sinh viên thành công!")
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
            delete_category(category, value)
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

    def refresh_tree(self):
        """Refresh the TreeView with the latest data from the database."""
        if not hasattr(self, 'tree') or self.tree is None:
            logger.warning("TreeView is not initialized. Cannot refresh.")
            return

        refresh_tree(self.tree, cursor)

    def import_data(self, format_type):
        """Import student data from a CSV or Excel file."""
        filename = filedialog.askopenfilename(
            filetypes=[('CSV files', '*.csv')] if format_type == 'csv' else [('Excel files', '*.xlsx')]
        )
        if not filename:
            return

        logger.info(f"Importing data from {filename}")
        try:
            if format_type == 'csv':
                df = pd.read_csv(filename, dtype={'phone': str})  # Ensure phone is read as a string
            else:
                df = pd.read_excel(filename, dtype={'phone': str})  # Ensure phone is read as a string

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
                    "Số điện thoại": str(row['phone']),  # Ensure phone is treated as a string
                    "Tình trạng": str(row['status'])
                }

                error = validate_student_data(data)
                if error:
                    error_count += 1
                    messagebox.showerror("Lỗi", error)
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

    def show_export_confirmation(self):
        """Show export confirmation dialog."""
        mssv = self.search_entry.get().strip()
        if not mssv:
            messagebox.showerror("Lỗi", "Vui lòng nhập MSSV!")
            return

        export_frame = tk.Toplevel(self.root)
        export_frame.title("Xuất Giấy Xác Nhận")
        export_frame.geometry("300x150")

        tk.Label(export_frame, text="Chọn định dạng xuất:").pack(pady=10)
        tk.Button(export_frame, text="Xuất HTML", command=lambda: export_student_status(mssv, "html")).pack(pady=5)
        tk.Button(export_frame, text="Xuất PDF", command=lambda: export_student_status(mssv, "pdf")).pack(pady=5)

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