# Student Management System v4.0.0

## Overview

The **Student Management System** is a desktop application built using Python and Tkinter. It allows administrators to manage student records, including adding, updating, deleting, and searching for students. The application also supports importing/exporting data, managing dynamic categories, and configuring system settings.

## Features

### Core Functions

- **Add, Update, Delete Students**: Manage student records with fields like MSSV, name, date of birth, gender, faculty, course, program, address, email, phone, and status.
- **Search Students**: Search by MSSV or perform advanced searches using filters like faculty and name.
- **Dynamic Categories**: Manage dynamic fields such as faculties, programs, and statuses.
- **Import/Export Data**: Import student data from CSV/Excel files and export data to CSV/Excel.
- **Configuration Management**: Update system configurations such as allowed email domains, phone patterns, and more.
- **Export Student Status**: Generate student status confirmation in HTML or PDF format.

### New in v4.0.0

- Refactored database operations into `database_operations.py` for better modularity.
- Extracted advanced search logic into a reusable function.
- Improved import/export functionality with reusable database methods.
- Enhanced logging and error handling.

## Project Structure

```
Student-management/
├── database_operations.py   # Handles all database-related operations
├── database_initialization.py # Initializes the database schema and default values
├── validation.py            # Contains validation logic for student data
├── app_logging.py           # Configures logging for the application
├── main.py                  # Main application logic and UI
├── README.md                # Project documentation
└── requirements.txt         # Python dependencies
```

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/vietlinhg7/Student-management.git
   cd student-management
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python main.py
   ```

## Usage

### Adding a Student

1. Click on **"Thêm Sinh Viên"**.
2. Fill in the required fields and click **"Thêm Sinh Viên"**.

### Searching for a Student

1. Click on **"Tìm Kiếm Sinh Viên"**.
2. Enter the MSSV or use advanced search filters to find a student.

### Managing Categories

1. Click on **"Quản lý Danh mục"**.
2. Add or delete options for faculties, programs, or statuses.

### Importing/Exporting Data

1. Click on **"Nhập/Xuất Dữ liệu"**.
2. Choose to import/export data in CSV or Excel format.

### Configuration Management

1. Click on **"Cấu hình hệ thống"**.
2. Update system settings such as allowed email domains, phone patterns, and more.

## Dependencies

- Python 3.8+
- Tkinter
- SQLite3
- pandas
- openpyxl
- fpdf
- markdown

## Logging

Log files are stored in the `logs/` directory. Each log file is named `student_manager_YYYYMMDD.log` and contains:

- Timestamps
- Operation types
- Success/Error status
- Detailed error messages

## Database Structure

- **students**: Stores student records.
- **settings**: Stores dynamic category options (e.g., faculties, programs, statuses).
- **config**: Stores system configuration settings.

## Version Info

- **Version**: 4.0.0
- **Build Date**: 21/02/2025
- **Changes**:
  - Refactored database operations into reusable functions.
  - Improved modularity and maintainability.
  - Enhanced import/export functionality.
  - Added better error handling and logging.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.
