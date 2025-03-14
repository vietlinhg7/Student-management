import sqlite3

conn = sqlite3.connect("students.db")
cursor = conn.cursor()

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

cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        category TEXT,
        value TEXT,
        UNIQUE(category, value)
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS config (
        key TEXT PRIMARY KEY,
        value TEXT,
        description TEXT
    )
''')

def init_default_settings():
    """Initialize default settings in the database."""
    default_values = {
        'faculty': ["Khoa Luật", "Khoa Tiếng Anh thương mại", "Khoa Tiếng Nhật", "Khoa Tiếng Pháp"],
        'status': ["Đang học", "Đã tốt nghiệp", "Đã thôi học", "Tạm dừng học"],
        'program': ["Cử nhân", "Thạc sĩ", "Tiến sĩ"]
    }
    cursor.execute("SELECT COUNT(*) FROM settings")
    if cursor.fetchone()[0] == 0:
        for category, values in default_values.items():
            for value in values:
                cursor.execute("INSERT INTO settings (category, value) VALUES (?, ?)", (category, value))
        conn.commit()

def init_default_config():
    """Initialize default configuration values in the database."""
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
            cursor.execute("INSERT INTO config (key, value) VALUES (?, ?)", (key, value))
        conn.commit()

init_default_settings()
init_default_config()