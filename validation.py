from database_operations import get_valid_options, get_config
from datetime import datetime
import re

def validate_student_data(data):
    """Validate student data before database operations."""
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

# Validation Functions
def is_valid_email(email):
    """Validate email format and domain."""
    allowed_domains = get_config('allowed_email_domains', '@student.university.edu.vn')
    if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
        return False
    return any(email.endswith(domain.strip()) for domain in allowed_domains.split(','))

def is_valid_phone(phone):
    """Validate phone number format."""
    pattern = get_config('phone_pattern', r'^(\+84|0)[3|5|7|8|9][0-9]{8}$')
    return re.match(pattern, phone) is not None

def is_valid_date(date_str):
    """Validate date format."""
    try:
        datetime.strptime(date_str, '%d/%m/%Y')
        return True
    except ValueError:
        return False