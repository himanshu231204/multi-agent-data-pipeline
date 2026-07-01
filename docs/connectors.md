# Database Connectors

> Connect your data warehouse or database directly to the pipeline — no CSV export needed.

---

## Quick Start

```python
from src.connectors.postgres import connect, list_tables, fetch_table

# 1. Connect
conn = connect(host="db.example.com", port=5432, database="analytics", user="admin", password="secret")

# 2. Discover tables
tables = list_tables(host="db.example.com", port=5432, database="analytics", user="admin", password="secret")
print(tables)  # ['users', 'orders', 'products']

# 3. Fetch into pipeline
df = fetch_table(host="db.example.com", port=5432, database="analytics", user="admin", password="secret", table="orders", limit=500)
```

The returned `df` (pandas DataFrame) can be passed directly into the CSV pipeline for cleaning, validation, and summarisation.

---

## Common Interface

Every connector exports exactly **3 functions** with the same contract:

| Function | Signature | Returns |
|----------|-----------|---------|
| `connect()` | Connection-specific params | Database connection object |
| `list_tables()` | Same params as `connect()` | `list[str]` — table names in the public/default schema |
| `fetch_table()` | Same params as `connect()` + `table: str`, `limit: int = 1000` | `pd.DataFrame` |

**Guarantees:**
- `list_tables()` returns tables from the `public` schema (Postgres, Redshift) or equivalent default namespace
- `fetch_table()` caps rows at `limit` (default 1000) to prevent memory blowouts
- Each call opens and closes its own connection — no connection pooling or state management required
- On any failure, the connector raises the underlying library's exception (caught upstream by the pipeline guardrails)

---

## Connectors

### 1. Databricks

**File:** `src/connectors/databricks.py`  
**Package:** `databricks-sdk==0.112.0`  
**Driver:** `databricks.sql` (ODBC-compatible)

#### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `host` | `str` | Yes | Workspace URL (e.g. `https://dbc-xxxx.cloud.databricks.com`) |
| `token` | `str` | Yes | Personal Access Token |
| `http_path` | `str` | Yes | SQL endpoint HTTP path (e.g. `/sql/1.0/endpoints/xxxxx`) |

#### Example

```python
from src.connectors.databricks import connect, list_tables, fetch_table

workspace_url = "https://dbc-12345abc.cloud.databricks.com"
token = "dapi1234567890abcdef"
http_path = "/sql/1.0/endpoints/abc123"

# Discover tables
tables = list_tables(workspace_url, token, http_path)
print(tables)  # ['sales', 'customers', 'inventory']

# Fetch data
df = fetch_table(workspace_url, token, http_path, table="sales", limit=500)
```

#### Security Notes

- Use a **Personal Access Token** with minimum required permissions (`SELECT` on target tables)
- Tokens are passed as function arguments — never stored at rest by the connector
- HTTPS enforced on port 443 by default

---

### 2. Snowflake

**File:** `src/connectors/snowflake_conn.py`  
**Package:** `snowflake-connector-python==4.6.0`

#### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `account` | `str` | Yes | Snowflake account identifier (e.g. `xy12345.us-east-1`) |
| `user` | `str` | Yes | Username |
| `password` | `str` | Yes | Password |
| `database` | `str` | Yes | Database name |
| `schema` | `str` | Yes | Schema name (typically `PUBLIC`) |

#### Example

```python
from src.connectors.snowflake_conn import connect, list_tables, fetch_table

account = "xy12345.us-east-1"
user = "analyst"
password = "s3cret"
database = "PROD_DB"
schema = "PUBLIC"

# Discover tables
tables = list_tables(account, user, password, database, schema)
print(tables)  # ['TRANSACTIONS', 'USERS', 'PRODUCTS']

# Fetch data
df = fetch_table(account, user, password, database, schema, table="TRANSACTIONS", limit=1000)
```

#### Security Notes

- Uses native username/password auth — works with Snowflake's built-in auth policies
- Table names are fully qualified as `DATABASE.SCHEMA.TABLE` in queries
- Consider using Snowflake key-pair auth for production (requires modifying the connector)

---

### 3. PostgreSQL

**File:** `src/connectors/postgres.py`  
**Package:** `psycopg2-binary==2.9.12`  
**Default Port:** `5432`

#### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `host` | `str` | Yes | Database hostname or IP |
| `port` | `int` | Yes | Port number (default `5432`) |
| `database` | `str` | Yes | Database name |
| `user` | `str` | Yes | Username |
| `password` | `str` | Yes | Password |

#### Example

```python
from src.connectors.postgres import connect, list_tables, fetch_table

host = "db.example.com"
port = 5432
database = "analytics"
user = "readonly"
password = "password123"

# Discover tables
tables = list_tables(host, port, database, user, password)
print(tables)  # ['users', 'orders', 'products']

# Fetch data
df = fetch_table(host, port, database, user, password, table="orders", limit=500)
```

#### Security Notes

- Only lists tables in the `public` schema
- Use a **read-only** database user for pipeline connections
- SSL not enforced by default — add `sslmode="require"` to `psycopg2.connect()` for production

---

### 4. MySQL

**File:** `src/connectors/mysql.py`  
**Package:** `mysql-connector-python==9.7.0`  
**Default Port:** `3306`

#### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `host` | `str` | Yes | Database hostname or IP |
| `port` | `int` | Yes | Port number (default `3306`) |
| `database` | `str` | Yes | Database/schema name |
| `user` | `str` | Yes | Username |
| `password` | `str` | Yes | Password |

#### Example

```python
from src.connectors.mysql import connect, list_tables, fetch_table

host = "db.example.com"
port = 3306
database = "shop"
user = "reader"
password = "password123"

# Discover tables
tables = list_tables(host, port, database, user, password)
print(tables)  # ['customers', 'orders', 'products']

# Fetch data
df = fetch_table(host, port, database, user, password, table="customers", limit=2000)
```

#### Security Notes

- Uses `SHOW TABLES` — lists tables in the current database/schema
- Use a **read-only** MySQL user with `SELECT` privileges only
- SSL not enforced by default — add `ssl_disabled=False` and provide cert paths for production

---

### 5. BigQuery

**File:** `src/connectors/bigquery.py`  
**Package:** `google-cloud-bigquery==3.41.0`  
**Auth:** Service Account JSON (uploaded via Streamlit file uploader)

#### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `project_id` | `str` | Yes | GCP project ID |
| `credentials_json` | `dict` | Yes | Service account JSON as a dictionary (loaded from uploaded file) |
| `dataset` | `str` | Yes | BigQuery dataset name |

#### Example

```python
import json
from src.connectors.bigquery import connect, list_tables, fetch_table

project_id = "my-gcp-project"
dataset = "analytics"

# Load service account JSON
with open("service-account.json") as f:
    credentials_json = json.load(f)

# Discover tables
tables = list_tables(project_id, credentials_json, dataset)
print(tables)  # ['events', 'users', 'page_views']

# Fetch data
df = fetch_table(project_id, credentials_json, dataset, table="events", limit=1000)
```

#### Security Notes

- Service account JSON is uploaded at runtime via Streamlit — never persisted to disk by the connector
- Requires `BigQuery Data Viewer` role minimum
- Uses backtick-quoted identifiers: `` `project.dataset.table` ``
- Includes `list_datasets()` helper to discover available datasets

---

### 6. DuckDB

**File:** `src/connectors/duckdb_conn.py`  
**Package:** `duckdb==1.5.3`  
**Auth:** None — local file-based

#### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `database` | `str` | Yes | Path to DuckDB file (e.g. `data.duckdb`) or `:memory:` for in-memory |

#### Example

```python
from src.connectors.duckdb_conn import connect, list_tables, fetch_table

database = "analytics.duckdb"

# Discover tables
tables = list_tables(database)
print(tables)  # ['sales', 'customers']

# Fetch data
df = fetch_table(database, table="sales", limit=500)

# In-memory mode
df = fetch_table(":memory:", table="my_table", limit=100)
```

#### Security Notes

- No authentication — purely local file access
- Use `:memory:` for ephemeral analysis (data lost when connection closes)
- Ideal for quick prototyping and testing without a remote database

---

### 7. Redshift

**File:** `src/connectors/redshift.py`  
**Package:** `psycopg2-binary==2.9.12` + `boto3==1.43.18`  
**Default Port:** `5439`

#### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `host` | `str` | Yes | Redshift cluster endpoint |
| `port` | `int` | Yes | Port number (default `5439`) |
| `database` | `str` | Yes | Database name |
| `user` | `str` | Yes | Username |
| `password` | `str` | Yes | Password |

#### Example

```python
from src.connectors.redshift import connect, list_tables, fetch_table

host = "my-cluster.xxxxxx.us-west-2.redshift.amazonaws.com"
port = 5439
database = "dev"
user = "admin"
password = "password123"

# Discover tables
tables = list_tables(host, port, database, user, password)
print(tables)  # ['fact_sales', 'dim_customers', 'dim_products']

# Fetch data
df = fetch_table(host, port, database, user, password, table="fact_sales", limit=1000)
```

#### Security Notes

- Uses `psycopg2` (PostgreSQL-compatible) — Redshift's native protocol
- `connect_timeout=10` enforced to prevent hanging on unreachable clusters
- Uses `try/finally` blocks for proper cursor and connection cleanup
- Only lists tables in the `public` schema
- `boto3` included for potential S3 integration (copy/unload operations)

---

## Security Considerations

| Concern | Handling |
|---------|----------|
| **Credential storage** | Credentials are passed as function arguments only — never persisted to disk, logged, or stored in `session_state` beyond the current run |
| **BYOK pattern** | All connectors use "Bring Your Own Key" — you provide credentials, the pipeline never stores them |
| **SSL/TLS** | Databricks and BigQuery enforce HTTPS by default. Postgres, MySQL, and Redshift do **not** enforce SSL — add it explicitly for production |
| **Read-only access** | Use read-only database users where possible. Connectors only run `SELECT` and metadata queries |
| **Connection lifecycle** | Each function opens and closes its own connection — no leaked connections or connection pools |

---

## Adding a New Connector

To add support for a new database:

### 1. Create the connector file

```python
# src/connectors/your_database.py
import pandas as pd
from your_library import connect as db_connect

def connect(host: str, port: int, database: str, user: str, password: str):
    """Return a database connection object."""
    conn = db_connect(host=host, port=port, database=database, user=user, password=password)
    return conn

def list_tables(host: str, port: int, database: str, user: str, password: str) -> list:
    """Return list of table names in the default schema."""
    conn = connect(host, port, database, user, password)
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")  # Adjust query for your database
    tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return tables

def fetch_table(host: str, port: int, database: str, user: str, password: str, table: str, limit: int = 1000) -> pd.DataFrame:
    """Return table data as a pandas DataFrame, capped at `limit` rows."""
    conn = connect(host, port, database, user, password)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table} LIMIT {limit}")
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return pd.DataFrame(rows, columns=columns)
```

### 2. Follow the interface contract

| Rule | Why |
|------|-----|
| `connect()` returns a raw connection | Pipeline doesn't know or care which driver you use |
| `list_tables()` uses the same params as `connect()` | No connection objects passed around — stateless calls |
| `fetch_table()` accepts `table` and `limit` | Uniform access pattern across all connectors |
| Open/close connections per call | Prevents leaked connections and threading issues |
| Return `pd.DataFrame` | Pipeline expects pandas — no custom result types |

### 3. Add to requirements.txt

```
your-database-library==x.y.z
```

### 4. Wire into the Streamlit UI

Update `src/pages/db_page.py` to add UI fields for your connector's parameters and a dropdown to select it.

---

## Requirements Reference

| Connector | Package | Version |
|-----------|---------|---------|
| Databricks | `databricks-sdk` | `==0.112.0` |
| Snowflake | `snowflake-connector-python` | `==4.6.0` |
| PostgreSQL | `psycopg2-binary` | `==2.9.12` |
| MySQL | `mysql-connector-python` | `==9.7.0` |
| BigQuery | `google-cloud-bigquery` | `==3.41.0` |
| DuckDB | `duckdb` | `==1.5.3` |
| Redshift | `psycopg2-binary` + `boto3` | `==2.9.12` + `==1.43.18` |

Install all at once:

```bash
pip install -r requirements.txt
```
