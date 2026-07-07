import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import json

def connect(project_id: str, credentials_json: dict):
    credentials = service_account.Credentials.from_service_account_info(
        credentials_json,
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    client = bigquery.Client(
        project=project_id,
        credentials=credentials
    )
    return client

def list_tables(project_id: str, credentials_json: dict, dataset: str) -> list:
    client = connect(project_id, credentials_json)
    tables = client.list_tables(f"{project_id}.{dataset}")
    return [table.table_id for table in tables]

def list_datasets(project_id: str, credentials_json: dict) -> list:
    client = connect(project_id, credentials_json)
    datasets = client.list_datasets()
    return [dataset.dataset_id for dataset in datasets]

def fetch_table(project_id: str, credentials_json: dict, dataset: str, table: str, limit: int = 1000) -> pd.DataFrame:
    client = connect(project_id, credentials_json)
    query = f"SELECT * FROM `{project_id}.{dataset}.{table}` LIMIT {limit}"
    df = client.query(query).to_dataframe()
    return df