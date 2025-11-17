import os
from typing import Optional, List, Any

import streamlit as st
import pandas as pd

from db import (
    get_connection, list_tables, fetch_table, describe_table, 
    list_procedures, list_routines, call_procedure, call_routine, insert_record, update_record,
    delete_record, get_record_by_id, get_procedure_info
)

# Set the browser tab title for the app. Keep the existing icon (do not change page_icon).
st.set_page_config(page_title="Hostel Management System")


def sidebar_connect():
    st.sidebar.header('Database connection')
    host = st.sidebar.text_input('Host', value=os.getenv('DB_HOST', 'localhost'))
    port = st.sidebar.text_input('Port', value=os.getenv('DB_PORT', '3306'))
    user = st.sidebar.text_input('User', value=os.getenv('DB_USER', 'root'))
    password = st.sidebar.text_input('Password', type='password', value=os.getenv('DB_PASSWORD', ''))
    database = st.sidebar.text_input('Database', value=os.getenv('DB_DATABASE', ''))

    if 'db_config' not in st.session_state:
        st.session_state.db_config = None

    if st.sidebar.button('Connect'):
        st.session_state.db_config = {'host': host, 'port': int(port), 'user': user, 'password': password, 'database': database}

    return st.session_state.db_config


def show_tables(conn):
    st.header('Tables')
    try:
        tables = list_tables(conn)
    except Exception as e:
        st.error(f'Error listing tables: {e}')
        return

    table = st.selectbox('Select table', options=[''] + tables)
    if table:
        cols, rows = fetch_table(conn, table, limit=500)
        st.subheader('Schema')
        desc = describe_table(conn, table)
        st.dataframe(pd.DataFrame(desc, columns=['Field', 'Type', 'Null', 'Key', 'Default', 'Extra']))
        st.subheader('Preview')
        df = pd.DataFrame(rows, columns=cols)
        st.dataframe(df)





def show_procedures(conn, database: Optional[str]):
    st.header('Stored Procedures & Functions')
    
    # Let user choose between procedures and functions
    selection = st.radio('Show:', ['Procedures', 'Functions'], horizontal=True)
    
    # Convert selection to database type format
    routine_type = 'PROCEDURE' if selection == 'Procedures' else 'FUNCTION'
    
    try:
        routines = list_routines(conn, routine_type, schema=database)
        if not routines:
            st.info(f'No stored {selection.lower()} found in the database.')
            return
    except Exception as e:
        st.error(f'Error fetching {selection.lower()}: {e}')
        return

    routine_name = st.selectbox(f'Select {selection.lower()[:-1]}', options=[''] + routines)
    if routine_name:
        try:
            # Get routine information with correct type
            params, description = get_procedure_info(conn, routine_name, database, routine_type)
            
            # Show parameter information
            if params:
                st.markdown("**Parameters Required:**")
                param_info = []
                for param_name, param_mode, param_type in params:
                    # Skip return parameters for functions
                    if routine_type == 'FUNCTION' and param_mode is None:
                        continue
                    param_info.append(f"- **{param_name}** ({param_mode}): {param_type}")
                st.markdown("\n".join(param_info))
                
                # Create input fields for each parameter
                args = []
                for param_name, param_mode, param_type in params:
                    # Skip return parameters for functions
                    if routine_type == 'FUNCTION' and param_mode is None:
                        continue
                    if 'INT' in param_type.upper():
                        value = st.number_input(f"{param_name} ({param_type})", step=1)
                        args.append(str(int(value)))
                    elif 'DECIMAL' in param_type.upper() or 'FLOAT' in param_type.upper():
                        value = st.number_input(f"{param_name} ({param_type})", step=0.01)
                        args.append(str(float(value)))
                    else:
                        value = st.text_input(f"{param_name} ({param_type})")
                        args.append(value)
            else:
                st.info(f"This {selection.lower()[:-1]} doesn't require any parameters.")
                args = []
            
            st.markdown("---")
            if st.button(f'Execute {selection.lower()[:-1]}'):
                try:
                    results = call_routine(conn, routine_name, args, routine_type)
                    if not results:
                        st.success(f'{selection.lower()[:-1].capitalize()} executed successfully (no result sets).')
                    else:
                        for i, r in enumerate(results):
                            if routine_type == 'FUNCTION':
                                st.markdown(f"**Return value:** {r[0][0]}")
                            else:
                                st.subheader(f'Result set {i+1}')
                                if r:  # Check if the result set is not empty
                                    st.dataframe(pd.DataFrame(r))
                                else:
                                    st.info("This result set is empty.")
                except Exception as e:
                    st.error(f'Error executing {selection.lower()[:-1]}: {e}')
        except Exception as e:
            st.error(f'Error getting {selection.lower()[:-1]} information: {e}')


def calculate_age_group(age: int) -> str:
    if age <= 10:
        return "0-10"
    elif age <= 17:
        return "11-17"
    elif age <= 22:
        return "18-22"
    elif age <= 35:
        return "23-35"
    else:
        return "36-above"

def show_crud(conn):
    st.header('CRUD Operations')
    
    # Select table first
    tables = list_tables(conn)
    table = st.selectbox('Select table', options=[''] + tables, key='crud_table')
    
    if not table:
        return
        
    # Get table structure
    desc = describe_table(conn, table)
    columns = [row[0] for row in desc]
    pk_col = next((row[0] for row in desc if 'PRI' in row[3]), columns[0])
    
    # CRUD Operations selector
    operation = st.selectbox('Operation', ['Create', 'Read', 'Update', 'Delete'])
    
    if operation == 'Create':
        st.subheader('Create New Record')
        # Create form for inserting new record
        with st.form('insert_form'):
            data = {}
            age_value = None
            
            for col, details in zip(columns, desc):
                # Skip auto-increment fields
                if 'auto_increment' in str(details[5]).lower():
                    continue

                field_type = str(details[1]).lower()
                col_lower = col.lower()

                # Special handling: student.age / student.age_group
                if table == 'student' and col_lower == 'age':
                    age_value = st.number_input(f'{col} ({field_type})', min_value=0, max_value=120, step=1)
                    data[col] = int(age_value)
                    continue
                if table == 'student' and col_lower == 'age_group':
                    # computed automatically
                    continue

                # Dropdowns for fields with limited options
                if table == 'room' and col_lower == 'type':
                    val = st.selectbox(f'{col} ({field_type})', options=['single', 'double', 'triple'])
                    data[col] = val
                    continue
                if table == 'fees' and col_lower == 'status':
                    val = st.selectbox(f'{col} ({field_type})', options=['pending', 'paid'])
                    data[col] = val
                    continue

                # Date / datetime fields -> use date_input and store ISO format
                if 'date' in field_type or col_lower in ('date', 'dob', 'birthdate', 'created_at', 'start_date', 'end_date'):
                    d = st.date_input(f'{col} ({field_type}) — format: YYYY-MM-DD')
                    # store ISO date string
                    data[col] = d.isoformat()
                    continue

                # Numeric types
                if 'int' in field_type:
                    data[col] = int(st.number_input(f'{col} ({field_type})', step=1))
                    continue
                if 'decimal' in field_type or 'float' in field_type:
                    data[col] = float(st.number_input(f'{col} ({field_type})', step=0.01))
                    continue

                # Fallback to text
                data[col] = st.text_input(f'{col} ({field_type})')
            
            if st.form_submit_button('Insert Record'):
                try:
                    # Set age_group automatically for student table
                    if table == 'student' and age_value is not None:
                        data['age_group'] = calculate_age_group(age_value)
                    
                    new_id = insert_record(conn, table, data)
                    st.success(f'Record inserted successfully! ID: {new_id}')
                except Exception as e:
                    st.error(f'Error inserting record: {e}')
    
    elif operation == 'Read':
        st.subheader('View Records')
        cols, rows = fetch_table(conn, table, limit=1000)
        df = pd.DataFrame(rows, columns=cols)
        st.dataframe(df)
        
    elif operation == 'Update':
        st.subheader('Update Record')
        # First select record to update
        cols, rows = fetch_table(conn, table, limit=1000)
        df = pd.DataFrame(rows, columns=cols)
        st.dataframe(df)
        
        # Step 1: Form to get the record ID
        with st.form('select_record_form'):
            record_id = st.text_input(f'Enter {pk_col} of record to update')
            submit_get_record = st.form_submit_button('Get Record')
        
        # Step 2: If we have a record ID and user clicked to get it, show update form
        if record_id and submit_get_record:
            record = get_record_by_id(conn, table, pk_col, record_id)
            if record:
                with st.form('update_record_form'):
                    data = {}
                    age_value = None
                    
                    for col, val, details in zip(columns, record, desc):
                        if col != pk_col:  # Don't update primary key
                            field_type = str(details[1]).lower()
                            col_lower = col.lower()

                            # student age handling
                            if table == 'student' and col_lower == 'age':
                                age_value = st.number_input(f'{col} ({field_type})', 
                                                            value=int(val) if val not in (None, '') else 0,
                                                            min_value=0, max_value=120, step=1)
                                data[col] = int(age_value)
                                continue
                            if table == 'student' and col_lower == 'age_group':
                                # Show computed age group, don't include in data to update
                                if age_value is None:
                                    try:
                                        age_value = int(next((record[i] for i, c in enumerate(columns) if c.lower() == 'age'), None))
                                    except Exception:
                                        age_value = None
                                st.text(f'Age Group: {calculate_age_group(age_value) if age_value is not None else "N/A"}')
                                continue

                            # Dropdowns for specific tables/fields
                            if table == 'room' and col_lower == 'type':
                                options = ['single', 'double', 'triple']
                                current = str(val).lower() if val is not None else options[0]
                                index = options.index(current) if current in options else 0
                                data[col] = st.selectbox(f'{col} ({field_type})', options=options, index=index)
                                continue
                            if table == 'fees' and col_lower == 'status':
                                options = ['pending', 'paid']
                                current = str(val).lower() if val is not None else options[0]
                                index = options.index(current) if current in options else 0
                                data[col] = st.selectbox(f'{col} ({field_type})', options=options, index=index)
                                continue

                            # Dates -> date_input with prefill
                            if 'date' in field_type or col_lower in ('date', 'dob', 'birthdate', 'created_at', 'start_date', 'end_date'):
                                import datetime
                                pre = None
                                try:
                                    if val is not None and val != '':
                                        pre = pd.to_datetime(val).date()
                                except Exception:
                                    pre = None
                                d = st.date_input(f'{col} ({field_type}) — format: YYYY-MM-DD', value=pre if pre is not None else datetime.date.today())
                                data[col] = d.isoformat()
                                continue

                            # Numeric
                            if 'int' in field_type:
                                data[col] = int(st.number_input(f'{col} ({field_type})', value=int(val) if val not in (None, '') else 0))
                                continue
                            if 'decimal' in field_type or 'float' in field_type:
                                data[col] = float(st.number_input(f'{col} ({field_type})', value=float(val) if val not in (None, '') else 0.0))
                                continue

                            # Fallback text
                            data[col] = st.text_input(f'{col} ({field_type})', value=str(val) if val not in (None, '') else '')
                    
                    submit_update = st.form_submit_button('Update Record')
                    if submit_update:
                        try:
                            rows_affected = update_record(conn, table, data, {pk_col: record_id})
                            st.success(f'Updated {rows_affected} record(s) successfully!')
                        except Exception as e:
                            st.error(f'Error updating record: {e}')
            else:
                st.error(f'No record found with {pk_col} = {record_id}')
    
    elif operation == 'Delete':
        st.subheader('Delete Record')
        cols, rows = fetch_table(conn, table, limit=1000)
        df = pd.DataFrame(rows, columns=cols)
        st.dataframe(df)
        
        with st.form('delete_form'):
            record_id = st.text_input(f'Enter {pk_col} of record to delete')
            if st.form_submit_button('Delete Record'):
                if record_id:
                    try:
                        rows_affected = delete_record(conn, table, {pk_col: record_id})
                        if rows_affected > 0:
                            st.success(f'Deleted {rows_affected} record(s) successfully!')
                        else:
                            st.warning(f'No records found with {pk_col} = {record_id}')
                    except Exception as e:
                        st.error(f'Error deleting record: {e}')

def main():
    # Centered single-line title (prevent wrapping) and centered subtitle
    st.markdown(
        '<h1 style="text-align:center; white-space:nowrap; margin:0.5rem 0;">DBMS Project - Hostel Management System</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p style="text-align:center; color:#6c757d; margin-top:0.25rem;">Connect to your MySQL database, browse tables, call stored procedures and use CRUD operations.</p>',
        unsafe_allow_html=True,
    )

    db_config = sidebar_connect()

    conn = None
    if db_config:
        try:
            conn = get_connection(db_config)
            st.success('Connected')
        except Exception as e:
            st.error(f'Connection error: {e}')

    if conn:
        tab = st.radio('Choose', ['Tables', 'Procedures and Functions', 'CRUD'])
        if tab == 'Tables':
            show_tables(conn)
        elif tab == 'Procedures and Functions':
            show_procedures(conn, db_config.get('database'))
        elif tab == 'CRUD':
            show_crud(conn)


if __name__ == '__main__':
    main()