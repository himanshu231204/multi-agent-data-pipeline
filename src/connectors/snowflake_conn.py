import pandas as pd
import snowflake.connector

def connect(account: str, user: str, password: str, database: str, schema: str):
    conn = snowflake.connector.connect(
        account=account,
        user=user,
        password=password,
        database=database,
        schema=schema
    )
    return conn

def list_tables(account: str, user: str, password: str, database: str, schema: str) -> list:
    conn = connect(account, user, password, database, schema)
    cursor = conn.cursor()
    cursor.execute(f"SHOW TABLES IN SCHEMA {database}.{schema}")
    tables = [row[1] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return tables

def fetch_table(account: str, user: str, password: str, database: str, schema: str, table: str, limit: int = 1000) -> pd.DataFrame:
    conn = connect(account, user, password, database, schema)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {database}.{schema}.{table} LIMIT {limit}")
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return pd.DataFrame(rows, columns=columns)