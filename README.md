# Student Management System v2.0.0

## Source Code Structure

```
.
├── ex1.py       # Main application file containing GUI and database logic
├── students.db  # SQLite database file (auto-generated)
└── logs/        # Application logs directory
```

## Requirements

Ensure you have Python installed (version 3.6 or later). Required packages:

### Built-in Modules

- `sqlite3`
- `tkinter`
- `re`
- `datetime`
- `logging`
- `os`

### External Packages

Install using pip:

```bash
pip install pandas openpyxl
```

## Installation

1. Clone or download the source code
2. Navigate to the source code directory
3. Install required packages:

```bash
pip install pandas openpyxl
```

## Features

### Core Functions

- Add/Edit/Delete student records
- Search by MSSV (Student ID)
- Advanced search by faculty and name
- Dynamic category management
- Data import/export (CSV/Excel)

### New in v2.0.0

- ✨ Dynamic category management (Faculty, Program, Status)
- 🔍 Advanced search capabilities
- 📊 Import/Export data (CSV, Excel)
- 📝 Comprehensive logging system
- 🔄 Version tracking and build info

## How to Run

```bash
python ex1.py
```

## Data Management

### Database Structure

- `students.db`: Main student records
- `settings`: Dynamic category options

### Import/Export Formats

CSV/Excel columns required:

```
mssv,name,dob,gender,faculty,course,program,address,email,phone,status
```

### Logging

Log files location: `logs/student_manager_YYYYMMDD.log`
Contains:

- Timestamps
- Operation types
- Success/Error status
- Detailed error messages

## Version Info

- Version: 2.0.0
- Build Date: 21/02/2025
- Changes:
  - Added category management
  - Implemented advanced search
  - Added data import/export
  - Added logging system
