import unittest
import sqlite3
import os
from datetime import datetime, timedelta
import json
from ex1 import is_valid_email, is_valid_phone, is_valid_date, is_valid_status_transition, can_delete_student, get_config

class TestStudentManagement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test database and config"""
        cls.conn = sqlite3.connect(":memory:")
        cls.cursor = cls.conn.cursor()
        
        # Create required tables
        cls.cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mssv TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cls.cursor.execute('''
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        # Insert test config data
        test_config = {
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
            'enable_rules': 'true'
        }
        
        for key, value in test_config.items():
            cls.cursor.execute(
                "INSERT INTO config (key, value) VALUES (?, ?)", 
                (key, value)
            )
        cls.conn.commit()

    def test_email_validation(self):
        """Test email validation rules"""
        # Valid email tests
        self.assertTrue(is_valid_email("test@student.university.edu.vn"))
        
        # Invalid email tests
        invalid_emails = [
            "test@gmail.com",  # Wrong domain
            "test@",  # Incomplete email
            "@student.university.edu.vn",  # Missing username
            "test.student.university.edu.vn",  # Missing @
            ""  # Empty string
        ]
        for email in invalid_emails:
            self.assertFalse(is_valid_email(email))

    def test_phone_validation(self):
        """Test phone number validation rules"""
        # Valid phone numbers
        valid_phones = [
            "0912345678",
            "+84912345678",
            "0357777777",
            "0987654321"
        ]
        for phone in valid_phones:
            self.assertTrue(is_valid_phone(phone))
        
        # Invalid phone numbers
        invalid_phones = [
            "012345678",  # Invalid prefix
            "9876543210",  # Invalid prefix
            "084912345678",  # Invalid format
            "091234567",  # Too short
            "09123456789",  # Too long
            "",  # Empty string
            "abcdefghij"  # Non-numeric
        ]
        for phone in invalid_phones:
            self.assertFalse(is_valid_phone(phone))

    def test_date_validation(self):
        """Test date format validation"""
        # Valid dates
        valid_dates = [
            "01/01/2000",
            "31/12/2023",
            "29/02/2024"  # Leap year
        ]
        for date in valid_dates:
            self.assertTrue(is_valid_date(date))
        
        # Invalid dates
        invalid_dates = [
            "32/01/2023",  # Invalid day
            "13/13/2023",  # Invalid month
            "29/02/2023",  # Invalid leap year date
            "01-01-2023",  # Wrong format
            "2023/01/01",  # Wrong format
            "",  # Empty string
            "abc"  # Non-date string
        ]
        for date in invalid_dates:
            self.assertFalse(is_valid_date(date))

    def test_status_transitions(self):
        """Test student status transition rules"""
        # Valid transitions
        valid_transitions = [
            ("Đang học", "Bảo lưu"),
            ("Đang học", "Tốt nghiệp"),
            ("Bảo lưu", "Đang học"),
            ("Bảo lưu", "Đình chỉ")
        ]
        for old_status, new_status in valid_transitions:
            self.assertTrue(is_valid_status_transition(old_status, new_status))
        
        # Invalid transitions
        invalid_transitions = [
            ("Tốt nghiệp", "Đang học"),
            ("Đình chỉ", "Đang học"),
            ("Đang học", "Invalid Status")
        ]
        for old_status, new_status in invalid_transitions:
            self.assertFalse(is_valid_status_transition(old_status, new_status))

    def test_deletion_window(self):
        """Test student deletion time window rules"""
        # Insert test students
        current_time = datetime.now()
        test_data = [
            ("SV001", "New Student", current_time),
            ("SV002", "Old Student", current_time - timedelta(hours=1))
        ]
        
        for mssv, name, created_at in test_data:
            self.cursor.execute('''
                INSERT INTO students (mssv, name, created_at)
                VALUES (?, ?, ?)
            ''', (mssv, name, created_at))
        self.conn.commit()
        
        # Pass the test connection to the functions
        self.assertTrue(can_delete_student("SV001", self.conn))
        self.assertFalse(can_delete_student("SV002", self.conn))
        self.assertFalse(can_delete_student("SV999", self.conn))

    def test_config_management(self):
        """Test configuration management"""
        # Pass the test connection to get_config
        self.assertEqual(
            get_config('allowed_email_domains', db_connection=self.conn),
            '@student.university.edu.vn'
        )
        
        self.assertEqual(
            get_config('non_existent_key', 'default_value', self.conn),
            'default_value'
        )
        
        transitions = json.loads(get_config('status_transitions', db_connection=self.conn))
        self.assertIn("Đang học", transitions)
        self.assertIn("Bảo lưu", transitions["Đang học"])

    @classmethod
    def tearDownClass(cls):
        """Clean up test database"""
        cls.conn.close()

if __name__ == '__main__':
    unittest.main()