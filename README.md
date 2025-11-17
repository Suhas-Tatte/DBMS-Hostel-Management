# Hostel Management System

A comprehensive database management system for hostel operations with an intuitive web-based interface built using Streamlit and MySQL.

## Features

- **Database Browser**: View and explore all database tables with schema information
- **CRUD Operations**: Create, read, update, and delete records with type-safe input validation
- **Stored Procedures & Functions**: Execute database procedures and functions with parameter support
- **Smart Input Handling**: 
  - Date pickers for date fields
  - Dropdown menus for enum fields
  - Automatic age group calculation for students
  - Type-specific validation for all inputs

## Database Schema

The system manages the following entities:

- **Students**: Student information with automatic age group categorization
- **Visitors**: Visitor records and visit tracking
- **Fees**: Fee management with payment status tracking
- **Hostels**: Hostel details and room management
- **Wardens**: Warden information and assignments
- **Rooms**: Room allocation and capacity management

## Prerequisites

- Python 3.7 or higher
- MySQL 8.0 or higher
- pip (Python package manager)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Suhas-Tatte/DBMS-Hostel-Management.git
cd DBMS-Hostel-Management
```

2. Install required Python packages:
```bash
pip install -r requirements.txt
```

3. Set up the MySQL database:
```bash
mysql -u root -p < mysql.sql
```

4. (Optional) Create a `.env` file for default database credentials:
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_DATABASE=hostel_management
```

## Usage

1. Start the Streamlit application:
```bash
streamlit run streamlit_app.py
```

2. Open your web browser and navigate to the URL shown in the terminal (typically `http://localhost:8501`)

3. Connect to your database using the sidebar form

4. Choose from the available operations:
   - **Tables**: Browse and view database tables
   - **Procedures and Functions**: Execute stored procedures and functions
   - **CRUD**: Perform create, read, update, and delete operations

## Project Structure

```
DBMS-Hostel-Management/
├── streamlit_app.py      # Main Streamlit web application
├── db.py                 # Database helper functions and utilities
├── mysql.sql             # Database schema and initialization
├── requirements.txt      # Python dependencies
├── .gitignore           # Git ignore rules
└── README.md            # Project documentation
```

## Technologies Used

- **Frontend**: Streamlit
- **Backend**: Python 3
- **Database**: MySQL
- **Libraries**: 
  - mysql-connector-python (Database connectivity)
  - pandas (Data manipulation)
  - python-dotenv (Environment configuration)
