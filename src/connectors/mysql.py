import pandas as pd
import mysql.connector

def connect(host: str, port: int, database: str, user: str, password: str):
    conn = mysql.connector.connect(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password
    )
    return conn

def list_tables(host: str, port: int, database: str, user: str, password: str) -> list:
    conn = connect(host, port, database, user, password)
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return tables

def fetch_table(host: str, port: int, database: str, user: str, password: str, table: str, limit: int = 1000) -> pd.DataFrame:
    conn = connect(host, port, database, user, password)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table} LIMIT {limit}")
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return pd.DataFrame(rows, columns=columns)