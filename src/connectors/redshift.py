import psycopg2
import pandas as pd
from typing import List

def connect(host: str, port: int, database: str, user: str, password: str):
    """Establish a connection to Amazon Redshift.
    
    Args:
        host: Redshift cluster hostname or endpoint
        port: Redshift port (default is 5439)
        database: Database name
        user: Username for authentication
        password: Password for authentication
        
    Returns:
        psycopg2 connection object
    """
    conn = psycopg2.connect(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password,
        connect_timeout=10
    )
    return conn

def list_tables(host: str, port: int, database: str, user: str, password: str) -> List[str]:
    """List all tables in the 'public' schema of the Redshift database.
    
    Args:
        host: Redshift cluster hostname or endpoint
        port: Redshift port (default is 5439)
        database: Database name
        user: Username for authentication
        password: Password for authentication
        
    Returns:
        List of table names in the public schema
        
    Raises:
        psycopg2.Error: If connection or query fails
    """
    conn = connect(host, port, database, user, password)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        return tables
    finally:
        cursor.close()
        conn.close()

def fetch_table(host: str, port: int, database: str, user: str, password: str, table: str, limit: int = 1000) -> pd.DataFrame:
    """Fetch data from a Redshift table.
    
    Args:
        host: Redshift cluster hostname or endpoint
        port: Redshift port (default is 5439)
        database: Database name
        user: Username for authentication
        password: Password for authentication
        table: Table name to fetch from
        limit: Maximum number of rows to fetch (default: 1000)
        
    Returns:
        pandas DataFrame containing the table data
        
    Raises:
        psycopg2.Error: If connection or query fails
    """
    conn = connect(host, port, database, user, password)
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT * FROM {table} LIMIT {limit}")
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return pd.DataFrame(rows, columns=columns)
    finally:
        cursor.close()
        conn.close()
