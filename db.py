import os
from typing import Optional, List, Any, Tuple

import mysql.connector
from mysql.connector import MySQLConnection, connect, Error
from dotenv import load_dotenv


load_dotenv()


def get_connection(config: Optional[dict] = None) -> MySQLConnection:
    """Return a mysql.connector connection.

    If config is None, read DB_* variables from environment.
    """
    if config is None:
        config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', '3306')),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_DATABASE', None),
            'autocommit': True,
        }
    try:
        conn = connect(**config)
        return conn
    except Error as e:
        raise


def list_tables(conn: MySQLConnection) -> List[str]:
    cur = conn.cursor()
    cur.execute('SHOW TABLES')
    rows = [r[0] for r in cur.fetchall()]
    cur.close()
    return rows


def fetch_table(conn: MySQLConnection, table: str, limit: int = 200) -> Tuple[List[str], List[Tuple[Any]]]:
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM `{table}` LIMIT {limit}")
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    cur.close()
    return cols, rows


def describe_table(conn: MySQLConnection, table: str) -> List[Tuple[str, str]]:
    cur = conn.cursor()
    cur.execute(f"DESCRIBE `{table}`")
    rows = cur.fetchall()
    cur.close()
    return rows


def get_procedure_info(conn: MySQLConnection, routine_name: str, schema: Optional[str] = None, routine_type: str = 'PROCEDURE') -> Tuple[List[Tuple[str, str, str]], str]:
    """Get procedure/function parameters and description.
    Returns tuple of (parameters, routine_definition)
    where parameters is list of (param_name, param_mode, param_type)"""
    cur = conn.cursor()
    try:
        # Get routine parameters
        if schema:
            cur.execute("""
                SELECT PARAMETER_NAME, PARAMETER_MODE, DTD_IDENTIFIER 
                FROM INFORMATION_SCHEMA.PARAMETERS 
                WHERE SPECIFIC_NAME=%s AND SPECIFIC_SCHEMA=%s AND ROUTINE_TYPE=%s
                  AND (PARAMETER_MODE IS NOT NULL OR ROUTINE_TYPE = 'PROCEDURE')  -- Skip return parameter for functions
                ORDER BY ORDINAL_POSITION""", 
                (routine_name, schema, routine_type))
        else:
            cur.execute("""
                SELECT PARAMETER_NAME, PARAMETER_MODE, DTD_IDENTIFIER 
                FROM INFORMATION_SCHEMA.PARAMETERS 
                WHERE SPECIFIC_NAME=%s AND ROUTINE_TYPE=%s
                  AND (PARAMETER_MODE IS NOT NULL OR ROUTINE_TYPE = 'PROCEDURE')  -- Skip return parameter for functions
                ORDER BY ORDINAL_POSITION""", 
                (routine_name, routine_type))
        params = cur.fetchall()
        
        # Get routine definition/comments
        if schema:
            cur.execute("""
                SELECT ROUTINE_DEFINITION, ROUTINE_COMMENT
                FROM INFORMATION_SCHEMA.ROUTINES
                WHERE ROUTINE_NAME=%s AND ROUTINE_SCHEMA=%s AND ROUTINE_TYPE=%s""",
                (routine_name, schema, routine_type))
        else:
            cur.execute("""
                SELECT ROUTINE_DEFINITION, ROUTINE_COMMENT
                FROM INFORMATION_SCHEMA.ROUTINES
                WHERE ROUTINE_NAME=%s AND ROUTINE_TYPE=%s""",
                (routine_name, routine_type))
        routine_info = cur.fetchone()
        routine_definition = routine_info[0] if routine_info else ""
        routine_comment = routine_info[1] if routine_info else ""
        
        return params, routine_comment or routine_definition
    finally:
        cur.close()

def list_routines(conn: MySQLConnection, routine_type: str = 'PROCEDURE', schema: Optional[str] = None) -> List[str]:
    """List stored procedures or functions.
    Args:
        conn: Database connection
        routine_type: 'PROCEDURE' or 'FUNCTION'
        schema: Optional database name
    Returns:
        List of routine names
    """
    cur = conn.cursor()
    if schema:
        cur.execute(
            "SELECT ROUTINE_NAME FROM INFORMATION_SCHEMA.ROUTINES WHERE ROUTINE_TYPE=%s AND ROUTINE_SCHEMA=%s",
            (routine_type, schema)
        )
    else:
        cur.execute(
            "SELECT ROUTINE_NAME FROM INFORMATION_SCHEMA.ROUTINES WHERE ROUTINE_TYPE=%s",
            (routine_type,)
        )
    rows = [r[0] for r in cur.fetchall()]
    cur.close()
    return rows

def list_procedures(conn: MySQLConnection, schema: Optional[str] = None) -> List[str]:
    """List stored procedures (backward compatibility)."""
    return list_routines(conn, 'PROCEDURE', schema)


def call_routine(conn: MySQLConnection, name: str, args: List[Any] = None, routine_type: str = 'PROCEDURE') -> List[Any]:
    """Call a stored procedure or function.
    
    Args:
        conn: Database connection
        name: Name of the procedure/function
        args: List of arguments
        routine_type: 'PROCEDURE' or 'FUNCTION'
    Returns:
        For procedures: List of result sets
        For functions: Single result (the function return value)
    """
    cur = conn.cursor()
    args = args or []
    try:
        if routine_type == 'FUNCTION':
            # For functions, we need to use SELECT func_name(args)
            placeholders = ', '.join(['%s'] * len(args))
            query = f"SELECT {name}({placeholders})"
            cur.execute(query, args)
            result = cur.fetchone()
            return [[(result[0],)]] if result else []
        else:
            # For procedures, use callproc
            cur.callproc(name, args)
            results = []
            # collect result sets
            for result in cur.stored_results():
                results.append(result.fetchall())
            return results
    finally:
        cur.close()

def call_procedure(conn: MySQLConnection, name: str, args: Optional[List[Any]] = None) -> List[Any]:
    """Legacy wrapper for call_routine with PROCEDURE type."""
    return call_routine(conn, name, args, 'PROCEDURE')

def insert_record(conn: MySQLConnection, table: str, data: dict) -> int:
    """Insert a record into a table.
    Args:
        conn: Database connection
        table: Table name
        data: Dictionary of column_name: value pairs
    Returns:
        The ID of the inserted record
    """
    columns = ', '.join(f"`{col}`" for col in data.keys())
    placeholders = ', '.join(['%s'] * len(data))
    query = f"INSERT INTO `{table}` ({columns}) VALUES ({placeholders})"
    
    cur = conn.cursor()
    try:
        cur.execute(query, list(data.values()))
        conn.commit()
        return cur.lastrowid
    finally:
        cur.close()

def update_record(conn: MySQLConnection, table: str, data: dict, where: dict) -> int:
    """Update records in a table.
    Args:
        conn: Database connection
        table: Table name
        data: Dictionary of column_name: new_value pairs
        where: Dictionary of column_name: value pairs for WHERE clause
    Returns:
        Number of rows affected
    """
    set_clause = ', '.join(f"`{col}` = %s" for col in data.keys())
    where_clause = ' AND '.join(f"`{col}` = %s" for col in where.keys())
    query = f"UPDATE `{table}` SET {set_clause} WHERE {where_clause}"
    
    cur = conn.cursor()
    try:
        cur.execute(query, list(data.values()) + list(where.values()))
        conn.commit()
        return cur.rowcount
    finally:
        cur.close()

def delete_record(conn: MySQLConnection, table: str, where: dict) -> int:
    """Delete records from a table.
    Args:
        conn: Database connection
        table: Table name
        where: Dictionary of column_name: value pairs for WHERE clause
    Returns:
        Number of rows affected
    """
    where_clause = ' AND '.join(f"`{col}` = %s" for col in where.keys())
    query = f"DELETE FROM `{table}` WHERE {where_clause}"
    
    cur = conn.cursor()
    try:
        cur.execute(query, list(where.values()))
        conn.commit()
        return cur.rowcount
    finally:
        cur.close()

def get_record_by_id(conn: MySQLConnection, table: str, id_column: str, id_value: Any) -> Optional[Tuple]:
    """Get a single record by its ID.
    Args:
        conn: Database connection
        table: Table name
        id_column: Name of the ID column
        id_value: Value of the ID to look up
    Returns:
        Record tuple or None if not found
    """
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT * FROM `{table}` WHERE `{id_column}` = %s", (id_value,))
        return cur.fetchone()
    finally:
        cur.close()
