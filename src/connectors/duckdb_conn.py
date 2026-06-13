import duckdb
import pandas as pd

def connect(database: str):
    return duckdb.connect(database)

def list_tables(database: str) -> list:
    conn = connect(database)
    tables = [row[0] for row in conn.execute("SHOW TABLES").fetchall()]
    conn.close()
    return tables

def fetch_table(database: str, table: str, limit: int = 1000) -> pd.DataFrame:
    conn = connect(database)
    df = conn.execute(f"SELECT * FROM {table} LIMIT {limit}").df()
    conn.close()
    return df
