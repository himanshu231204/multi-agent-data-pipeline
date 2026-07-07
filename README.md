<div align="center">

<img src="logo.png" alt="Britcore.AI" width="300"/>

<br/>
<br/>

# Multi-Agent Data Pipeline

### 11 specialised AI agents that autonomously process any CSV, PDF or database in real time

<br/>

[![Version](https://img.shields.io/badge/version-1.2.0-brightgreen?style=flat-square)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-Streamlit-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://multi-agent-pipeline-demo.streamlit.app)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-red?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Stars](https://img.shields.io/github/stars/harshitboots/multi-agent-data-pipeline?style=flat-square&color=yellow)](https://github.com/harshitboots/multi-agent-data-pipeline/stargazers)
[![Forks](https://img.shields.io/github/forks/harshitboots/multi-agent-data-pipeline?style=flat-square&color=blue)](https://github.com/harshitboots/multi-agent-data-pipeline/network)

<br/>

## 🌐 [Try it Live → multi-agent-pipeline-demo.streamlit.app](https://multi-agent-pipeline-demo.streamlit.app)

> No install. No API key needed in Basic mode. Open in browser and run.

<br/>

**[🚀 Quick Start](#quick-start) · [⚡ What's New in v1.2](#whats-new-in-v12) · [🔀 Router Engine](#router-engine) · [📄 PDF Intelligence](#pdf-intelligence-pipeline) · [📡 Observability](#observability-dashboard) · [🔌 Connectors](#data-sources) · [🤝 Contributing](#contributing)**

<br/>

> *Upload a messy CSV, drop in any PDF, or connect your database —*
> *watch 11 AI agents autonomously clean, anonymise, validate, transform,*
> *detect risks, extract entities and summarise your data in real time.*

</div>

---

## What's New in v1.2

> **v1.2.0 — June 2026** · [Full changelog](#changelog)

| Feature | Detail |
|---------|--------|
| **PDF Intelligence Report** | Download the full 5-section analysis as a formatted PDF — not JSON. Cover page, entities, risk badges, action items, executive summary |
| **VPN / Proxy Block** | Automatic VPN and hosting IP detection via ip-api.com. Blocked users see a full-screen denial page |
| **Anonymous Run Tracking** | SHA-256 IP + User-Agent fingerprint persisted to SQLite. 2 free runs survive page refresh — no signup required |
| **Compare Runs Dashboard** | New first tab — side-by-side baseline vs router for both CSV and PDF pipelines. Cost savings in GBP and %, latency delta |
| **PDF Mode Selector** | With Router (Haiku + Sonnet) vs Without Router (all Sonnet) toggle — mirrors CSV pipeline behaviour |
| **Result Persistence** | PDF and CSV results survive navigation to the dashboard and back. Cleared on browser refresh only |
| **Streamlit Cloud Ready** | Reads API key from `st.secrets` in cloud, `.env` locally — zero config change required |
| **Dashboard Preview Card** | Hero section shows a locked dashboard preview until 2 runs are complete |

---

## The Problem

Every data team has the same nightmare.

You get a CSV from a stakeholder. It has:
- Dates in 3 different formats
- Missing customer IDs on 20% of rows
- A price of £999.99 that should be £9.99
- Column names that change every month
- No documentation. No schema. No context.

You spend **3 hours** writing cleaning scripts.  
Then the next file arrives and breaks everything.

You get a PDF contract. Buried inside:
- 47 action items scattered across 12 pages
- PII data that shouldn't be in that document
- Legal clauses that need flagging
- Deadlines with no single owner

You spend **2 hours** reading, highlighting, and writing a summary.

**There has to be a better way.**

---

## The Solution

Instead of writing rules, deploy agents.

Each agent has a single job, its own reasoning, and structured JSON output.  
The Router Engine assigns the cheapest model that can handle each task.  
Every run is traced, costed, and persisted for full observability.

```
                    Your data (CSV · PDF · Database)
                                  ↓
                    ┌─────────────────────────┐
                    │  🔒 Access Control Layer  │
                    │  VPN block · IP fingerprint · Credit gate  │
                    └─────────────┬───────────┘
                                  ↓
                    ┌─────────────────────────┐
                    │   🧭 Router Engine        │  ← classifies task complexity
                    │   With Router / Without   │  ← mode toggle
                    └──────┬──────────┬────────┘
                           │          │
              ┌────────────▼──┐  ┌────▼──────────────┐
              │ CSV Pipeline   │  │  PDF Pipeline      │
              │ 6 Agents       │  │  5 Agents          │
              │ Haiku + Sonnet │  │  Haiku → Sonnet    │
              └────────┬───────┘  └────────┬───────────┘
                       │                   │
              ┌────────▼───────────────────▼──────┐
              │  🔬 Observability & Telemetry       │
              │  RunTracer · Cost GBP · Guardrails  │
              └────────────────┬──────────────────┘
                               │
              ┌────────────────▼──────────────────┐
              │  💾 SQLite  (Run History · anon_visitors)  │
              └────────────────┬──────────────────┘
                               │
       ┌───────────────────────▼───────────────────────┐
       │  📤 Output                                      │
       │  Dashboard (Compare · Monitor · Cost · Guards)  │
       │  PDF Intelligence Report Download               │
       └────────────────────────────────────────────────┘
```

No config files. No rigid schemas. No rules to write and maintain.

---

## Quick Start

### Prerequisites

- Python 3.10+
- An Anthropic API key — get one free at [console.anthropic.com](https://console.anthropic.com)

### 1. Clone the repo

```bash
git clone https://github.com/harshitboots/multi-agent-data-pipeline.git
cd multi-agent-data-pipeline
```

### 2. Create virtual environment

```bash
python -m venv venv

# Mac / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your API key

```bash
# Create a .env file
echo ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxx > .env
```

### 5. Run the app

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501)  
Observability Dashboard: [http://localhost:8501/observability](http://localhost:8501/observability)

---

## Router Engine

The Router Engine is the intelligence layer between your data and the agents. It inspects each agent's task complexity and assigns the cheapest model that can handle it — no quality drop.

### Routing table

| Agent | Without Router | With Router | Reason |
|-------|---------------|-------------|--------|
| Cleaner | Sonnet | **Haiku** | Mechanical formatting — no reasoning needed |
| PII Anonymiser | Sonnet | **Haiku** | Pattern-based detection |
| Transformer | Sonnet | **Haiku** | Column derivation — structured, deterministic |
| Anomaly Detector | Sonnet | **Sonnet** | Statistical reasoning — needs quality |
| Validator | Sonnet | **Sonnet** | Schema judgment — needs quality |
| Summariser | Sonnet | **Sonnet** | Business insights — full quality required |

### Cost per run (demo CSV, 15 rows)

| Mode | Cost (GBP) | Latency |
|------|-----------|---------|
| Without Router — all Sonnet | ~£0.27 | ~14s |
| **With Router — routed** | **~£0.08** | **~5s** |
| **Saving** | **~70%** | **~63%** |

Run both modes → the **Compare Runs** dashboard tab auto-populates with the full breakdown.

---

## CSV Agent Pipeline

Six specialised agents process your CSV in sequence. The Router assigns Haiku or Sonnet per agent based on task complexity.

#### 🧹 Agent 1 — Cleaner (Haiku)
Identifies and fixes data quality issues before anything else runs.

```json
{
  "issues_fixed": [
    "Inconsistent date formats — standardised to YYYY-MM-DD",
    "Missing product names — flagged 1 row"
  ],
  "rows_affected": 6,
  "cleaned_columns": ["date", "product_name", "store_id"]
}
```

#### 🔒 Agent 2 — PII Anonymiser (Haiku)
Scans every row for emails, phone numbers, card numbers and postcodes — masks before any downstream agent sees the data.

```json
{
  "pii_found": ["Row 4: email", "Row 9: phone", "Row 12: card_number"],
  "rows_affected": 3,
  "pii_types_detected": ["card_number", "email", "phone"],
  "anonymised_preview": "j***@***.com · **** **** **** 1234"
}
```

#### 🛡️ Agent 3 — Validator (Sonnet)
Checks schema correctness, data types, constraints and completeness.

```json
{
  "schema_ok": true,
  "violations": ["Missing customer_id in row 8", "Negative unit_price in row 11"],
  "passed_checks": ["All transaction IDs unique", "Quantity values positive"],
  "completeness_score": 91.1
}
```

#### ⚡ Agent 4 — Transformer (Haiku)
Standardises, normalises and derives new columns.

```json
{
  "transformations_applied": ["Dates → ISO 8601", "Product names → title case"],
  "new_columns": ["year", "month", "day_of_week", "price_band", "is_weekend"],
  "rows_transformed": 15
}
```

#### 📡 Agent 5 — Anomaly Detector (Sonnet)
Finds statistical outliers, impossible values and suspicious patterns.

```json
{
  "anomalies": ["TXN007: total £999.99 — expected ~£51.96", "TXN011: negative price"],
  "anomaly_count": 7,
  "anomaly_score": 8.5,
  "flagged_rows": [7, 11]
}
```

#### 📊 Agent 6 — Summariser (Sonnet)
Business-readable summary with key stats and recommendations.

```json
{
  "summary": "Dataset contains 15 retail transactions across 5 categories...",
  "key_stats": { "Total Revenue": "£413.56", "Top Category": "Skincare" },
  "recommendations": ["Investigate TXN007 — possible data entry error"]
}
```

---

## PDF Intelligence Pipeline

Five sequential agents turn any PDF into structured intelligence. Upload a contract, report, invoice, or policy — get a full analysis in under 30 seconds.

| Agent | Model | Output |
|-------|-------|--------|
| **📄 PDF Parser** | Haiku | Document type, language, quality score, key topics |
| **🔍 Entity Extractor** | Haiku | People, organisations, locations, dates, amounts, emails |
| **⚠️ Risk Detector** | Sonnet | PII flags, GDPR risks, legal/financial red flags, risk score |
| **✅ Action Extractor** | Sonnet | Todos, decisions, deadlines, owners, priority actions |
| **📊 PDF Summariser** | Sonnet | Executive summary, key stats, recommendations |

### PDF Intelligence Report

After the pipeline runs, download a branded **PDF report** with:

- **Cover page** — document metadata, model used per agent, generation timestamp
- **Section 1** — Document Overview (type, language, quality, topics)
- **Section 2** — Entities Extracted (two-column layout per entity type)
- **Section 3** — Risk Analysis (coloured risk badge, PII flag, compliance risks)
- **Section 4** — Action Items & Decisions (priority actions in red, deadlines in amber)
- **Section 5** — Executive Summary (full summary text, key stats, recommendations)

The report uses navy/purple branding with per-section colour coding — ready to share directly with stakeholders.

### PDF modes

| Mode | Parser | Entity | Risk | Action | Summary |
|------|--------|--------|------|--------|---------|
| With Router | Haiku | Haiku | Sonnet | Sonnet | Sonnet |
| Without Router | Sonnet | Sonnet | Sonnet | Sonnet | Sonnet |

---

## Observability Dashboard

Every pipeline run is logged to `pipeline_runs.db` (SQLite, auto-created, gitignored).  
Open the dashboard at [http://localhost:8501/observability](http://localhost:8501/observability).

### 7 tabs

| Tab | What you see |
|-----|-------------|
| **⚖️ Compare Runs** | Side-by-side baseline vs router — cost GBP, latency ms, parse success rate, savings summary |
| **📡 Live Monitor** | Last run — agent waterfall with latency bars, cost per agent, full prompt + raw response inspector |
| **📋 Run History** | All runs in a table — click any run to drill into per-agent spans |
| **💰 Cost Analytics** | Spend over time, Haiku vs Sonnet breakdown, cost by mode |
| **🎯 Agent Performance** | Reliability %, avg latency, avg cost, parse failure rate — per agent across all runs |
| **🛡️ Guardrails Log** | Every guardrail event with severity, value vs threshold, action taken |
| **⚙️ Settings** | Configure guardrail thresholds — budget cap, timeout, PII limits |

### Compare Runs tab

After running both **With Router** and **Without Router**:

- Two cards side by side — coloured border (green = router, grey = baseline)
- Per-agent span table with latency bar visualisation
- Savings summary: cost difference in GBP, percentage saved, latency delta in ms
- If only one run exists — full detail view + nudge to run the other mode

### Guardrails

```python
from src.observability.guardrails import GuardrailEngine

guardrails = GuardrailEngine(
    budget_cap_gbp=0.50,     # stop run if cost exceeds this
    agent_timeout_s=30,       # skip agent if it hangs
    min_completeness=60.0,    # warn if validator score drops below this
    max_pii_rows=0,           # warn on any PII detected
    max_parse_failures=3,     # abort if this many agents fail JSON parse
    anomaly_score_warn=9.0,   # warn if anomaly score exceeds this
)
```

---

## Access Control

### VPN / Proxy Block

All VPN, proxy and hosting IPs are blocked at startup.  
Detection uses [ip-api.com](https://ip-api.com) — checks `proxy` and `hosting` fields.  
Private/localhost IPs (`127.0.0.1`, `192.168.x.x`, `10.x.x.x`) are always allowed for local dev.

### Free Access & BYOK

No signup required for the first 2 runs.

| Tier | Runs | How |
|------|------|-----|
| **Anonymous** | 2 free runs | Automatic — no account needed |
| **Star bonus** | +1 run | Star this repo — verified live via GitHub API |
| **BYOK** | Unlimited | Paste your own `sk-ant-...` key in the sidebar |
| **GitHub** | Tracked | Enter your GitHub username for cross-session credit |

**Anonymous run tracking** uses a SHA-256 hash of your IP address + User-Agent.  
The hash is stored in SQLite — never the raw IP. Runs persist across page refreshes.

**BYOK security:** your API key is stored in `st.session_state` only — never written to SQLite, files or logs. It disappears when you close the browser tab.

---

## Architecture

```
multi-agent-data-pipeline/
├── app.py                        # Main Streamlit UI — router, BYOK, VPN block, PDF pipeline
├── pages/
│   └── observability.py          # 7-tab observability dashboard
├── src/
│   ├── agents/
│   │   ├── cleaner.py            # CSV cleaning — Haiku
│   │   ├── pii_anonymiser.py     # PII detection — Haiku
│   │   ├── validator.py          # Schema validation — Sonnet
│   │   ├── transformer.py        # Data transformation — Haiku
│   │   ├── anomaly.py            # Anomaly detection — Sonnet
│   │   ├── summariser.py         # Business summary — Sonnet
│   │   ├── pdf_parser.py         # PDF structure analysis — Haiku
│   │   ├── entity_extractor.py   # Named entity extraction — Haiku
│   │   ├── risk_detector.py      # Risk and PII detection — Sonnet
│   │   ├── action_extractor.py   # Action items and decisions — Sonnet
│   │   └── (pdf summariser via summariser.py)
│   ├── auth/
│   │   ├── credits.py            # Credit tracking — anonymous (IP fingerprint) + GitHub + BYOK
│   │   └── github_api.py         # GitHub API — star/fork verification
│   ├── connectors/
│   │   ├── databricks.py         # Azure Databricks
│   │   ├── snowflake_conn.py     # Snowflake
│   │   ├── postgres.py           # PostgreSQL
│   │   ├── mysql.py              # MySQL
│   │   ├── bigquery.py           # BigQuery
│   │   └── duckdb_conn.py        # DuckDB
│   ├── observability/
│   │   ├── tracer.py             # RunTracer + AgentSpan — tokens, cost, latency, prompts
│   │   ├── store.py              # SQLite persistence — runs, spans, guardrail events
│   │   ├── guardrails.py         # GuardrailEngine — budget, timeout, PII, parse failures
│   │   └── metrics.py            # Analytics queries — cost trend, agent performance
│   ├── report_generator.py       # fpdf2 PDF report builder — 5-section branded output
│   ├── cost_config.py            # Model pricing (GBP), token limits, timeouts
│   ├── router.py                 # Router engine — assigns cheapest model per agent
│   ├── models.py                 # Pydantic schemas — all agent result types
│   └── pipeline.py               # CSV pipeline orchestrator
├── demo/
│   ├── sample_data.csv           # Demo CSV with intentional data quality issues
│   └── sample_report.pdf         # Demo PDF for the PDF pipeline
├── .streamlit/
│   └── config.toml               # Dark theme, CORS settings for cloud deployment
├── tests/
│   └── test_pipeline.py          # 16 passing tests
├── requirements.txt
└── .env.example
```

---

## Data Sources

### 📄 CSV Upload

Drop any CSV — no schema required. Agents infer structure and process automatically.

```bash
# CLI
python main.py your_data.csv

# With JSON output
python main.py your_data.csv --output results.json
```

Tested with: retail transactions · financial ledgers · HR records · IoT sensor data · marketing CSVs

---

### 📑 PDF Intelligence

Upload any PDF. Best results with:

- Quarterly / annual reports
- Contracts and legal documents
- Invoices and purchase orders
- Meeting minutes and notes
- Research papers · HR policies

---

### 🔌 Database Connectors

Connect directly to your database — agents fetch any table and run the full pipeline.

#### Azure Databricks
```python
from src.connectors.databricks import fetch_table

df = fetch_table(
    host="adb-xxxxx.azuredatabricks.net",
    token="dapi...",
    http_path="/sql/1.0/warehouses/xxxxx",
    table="catalog.schema.table_name"
)
```

#### Snowflake
```python
from src.connectors.snowflake_conn import fetch_table

df = fetch_table(
    account="xy12345.eu-west-1",
    user="my_user", password="my_password",
    database="MY_DATABASE", schema="PUBLIC", table="MY_TABLE"
)
```

#### PostgreSQL
```python
from src.connectors.postgres import fetch_table

df = fetch_table(host="localhost", port=5432, database="my_db",
                 user="postgres", password="my_password", table="my_table")
```

#### MySQL
```python
from src.connectors.mysql import fetch_table

df = fetch_table(host="localhost", port=3306, database="my_db",
                 user="root", password="my_password", table="my_table")
```

#### BigQuery
```python
from src.connectors.bigquery import fetch_table

df = fetch_table(project_id="my-gcp-project",
                 credentials_json=credentials_dict,
                 dataset="my_dataset", table="my_table")
```

#### DuckDB
```python
from src.connectors.duckdb_conn import fetch_table

df = fetch_table(database="/path/to/database.duckdb", table="my_table")
```

### Connector Status

| Database | Status |
|----------|--------|
| Azure Databricks | ✅ Stable |
| Snowflake | ✅ Stable |
| PostgreSQL | ✅ Stable |
| MySQL | ✅ Stable |
| BigQuery | ✅ Stable |
| DuckDB | ✅ Stable |
| MongoDB | 🔜 Planned |
| Redshift | 🔜 Planned |
| Microsoft Fabric | 🔜 Planned |

---

## Deploy to Production

### ☁️ Streamlit Community Cloud (Recommended — Free)

The fastest way to get a public URL.

1. Push this repo to GitHub (public or private)
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
3. Click **New app** and select this repository
4. Set **Main file path** to `app.py`
5. Click **Advanced settings → Secrets** and paste:

```toml
ANTHROPIC_API_KEY = "sk-ant-xxxxxxxxxxxxxxxx"
```

6. Click **Deploy** — live URL in under 2 minutes

The app automatically reads from `st.secrets` in cloud and `.env` locally — no code changes needed.

---

### 🐳 Docker

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

```bash
docker build -t multi-agent-pipeline .
docker run -p 8501:8501 -e ANTHROPIC_API_KEY=sk-ant-... multi-agent-pipeline
```

---

### ☁️ Azure

**Container Apps**
```bash
az containerapp create \
  --name multi-agent-pipeline \
  --resource-group my-rg \
  --image my-registry/multi-agent-pipeline:latest \
  --env-vars ANTHROPIC_API_KEY=sk-ant-...
```

**App Service**
```bash
az webapp create --name multi-agent-pipeline --resource-group my-rg --plan my-plan
az webapp config appsettings set --name multi-agent-pipeline \
  --settings ANTHROPIC_API_KEY=sk-ant-...
```

---

### ☁️ AWS

**Lambda + S3 trigger**
```python
import boto3
from src.pipeline import run_pipeline

def lambda_handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    # Download CSV from S3, run pipeline, push results back
```

---

### ☁️ GCP — Cloud Run

```bash
gcloud run deploy multi-agent-pipeline \
  --image gcr.io/my-project/multi-agent-pipeline \
  --platform managed \
  --set-env-vars ANTHROPIC_API_KEY=sk-ant-...
```

---

### 🚀 Render / Railway (Free Tier)

**Render:** Fork → Connect → Set `ANTHROPIC_API_KEY` → Deploy  
**Railway:** `railway login && railway init && railway up`

---

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | ✅ Yes | Anthropic API key (or use BYOK in the UI) |
| `DATABRICKS_HOST` | Optional | Databricks workspace URL |
| `DATABRICKS_TOKEN` | Optional | Databricks PAT token |
| `SNOWFLAKE_ACCOUNT` | Optional | Snowflake account identifier |
| `POSTGRES_HOST` | Optional | PostgreSQL host |
| `MYSQL_HOST` | Optional | MySQL host |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| AI — complex agents | Claude Sonnet (`claude-sonnet-4-6`) |
| AI — simple agents | Claude Haiku (`claude-haiku-4-5-20251001`) |
| Router Engine | Custom — `src/router.py` |
| PDF Report | fpdf2 — custom branded multi-section layout |
| Language | Python 3.10+ |
| Data | Pandas, PyPDF2 |
| Validation | Pydantic v2 |
| UI | Streamlit 1.58 |
| Persistence | SQLite (`pipeline_runs.db`) |
| Access Control | ip-api.com (VPN detection), SHA-256 fingerprinting |
| Connectors | Databricks SDK, Snowflake, psycopg2, mysql-connector, BigQuery, DuckDB |
| Testing | pytest (16 passing) |

---

## Changelog

### v1.2.0 — June 2026

**New**
- PDF Intelligence Report — download full 5-section analysis as a formatted PDF (fpdf2)
- VPN / proxy blocking — ip-api.com detection, full-screen denial page
- Anonymous run tracking — SHA-256 IP+UserAgent fingerprint, persisted to SQLite `anon_visitors` table across page refreshes
- Compare Runs dashboard tab — side-by-side baseline vs router for CSV and PDF, savings in GBP and %
- PDF mode selector — With Router (Haiku+Sonnet mix) vs Without Router (all Sonnet)
- Result persistence — CSV and PDF results survive navigation until browser refresh
- Dashboard preview card in hero — locked until 2 runs complete
- Streamlit Cloud secrets loader — reads `ANTHROPIC_API_KEY` from `st.secrets` automatically

**Fixed**
- fpdf2 cursor position bug — all `multi_cell` calls now use explicit widths and `set_x()` anchoring
- fpdf2 Latin-1 encoding — `_safe()` sanitiser replaces em dashes, smart quotes, bullets before render
- `NameError: safe_mode` — moved variable definition before `try` block
- `st.progress()` — fixed float vs int (Streamlit 1.58 requires 0.0–1.0)
- HTML entities in tab labels — replaced with real emoji characters
- PDF result display — moved outside `if pdf_file:` guard so results persist after navigation

**Changed**
- Comparison panel replaced with redirect CTA — cleaner homepage, dashboard is the comparison surface
- Dashboard light theme — white cards, sky-blue accents, improved readability
- `.gitignore` updated — `*.db`, `venv_win/`, `*:Zone.Identifier` excluded

---

### v1.1.0

- Router Engine — Haiku for simple tasks, Sonnet for complex
- Parallel Wave 1 execution — 63% latency reduction
- Observability dashboard — 6 tabs, SQLite persistence
- BYOK — bring your own Anthropic API key
- GitHub credit system — star bonus run

---

### v1.0.0

- CSV pipeline — 6 agents (Cleaner, PII, Validator, Transformer, Anomaly, Summariser)
- PDF pipeline — 5 agents (Parser, Entity, Risk, Action, Summariser)
- Database connectors — Databricks, Snowflake, PostgreSQL, MySQL, BigQuery, DuckDB
- Streamlit UI — dark theme
- CLI entrypoint
- 16 unit tests

---

## Roadmap

- [x] CSV pipeline — 6 agents
- [x] PDF intelligence — 5 agents
- [x] Database connectors — 6 databases
- [x] Router Engine — Haiku / Sonnet routing
- [x] Observability dashboard — traces, cost, guardrails
- [x] Compare Runs tab
- [x] BYOK + GitHub credit system
- [x] VPN blocking
- [x] Anonymous run tracking (IP fingerprint)
- [x] PDF Intelligence Report download
- [x] Streamlit Cloud deployment
- [ ] `pip install multi-agent-data-pipeline`
- [ ] MongoDB connector
- [ ] Redshift connector
- [ ] Microsoft Fabric connector
- [ ] REST API — FastAPI wrapper
- [ ] Agent memory — learn from past runs
- [ ] Webhook support — trigger via HTTP
- [ ] Docker image on Docker Hub
- [ ] GitHub Actions CI/CD

---

## Contributing

### Ways to Contribute

#### 🔌 Add a Database Connector

| Database | Difficulty |
|----------|-----------|
| MongoDB | Medium |
| Redshift | Easy |
| Microsoft Fabric | Medium |
| Elasticsearch | Hard |

#### 🤖 New Agents

Ideas for new agents:
- **Schema Inferencer** — auto-detect and document schema
- **Data Lineage Tracker** — track where each column came from
- **Duplicate Detector** — find near-duplicate records
- **Language Translator** — translate non-English fields

#### Adding a Connector

```python
# src/connectors/your_db.py

def connect(host: str, port: int, database: str, user: str, password: str): ...
def list_tables(host: str, ...) -> list: ...
def fetch_table(host: str, ..., table: str, limit: int = 1000) -> pd.DataFrame: ...
```

#### Adding an Agent

```python
# src/agents/your_agent.py

SYSTEM_PROMPT = """You are a [role] agent.
Respond ONLY with valid JSON. No markdown. No explanation."""

def run(csv_preview: str, total_rows: int,
        model: str = None, span=None, api_key: str = None) -> YourAgentResult:
    _client = Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
    response = _client.messages.create(model=model, ...)
    if span:
        span.finish(input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                    model=model, raw_response=..., parsed_output=..., parse_ok=True)
    return result
```

### Getting Started

```bash
git clone https://github.com/YOUR_USERNAME/multi-agent-data-pipeline.git
cd multi-agent-data-pipeline
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
git checkout -b feature/your-feature
# make changes
pytest tests/ -v
git push origin feature/your-feature
# open a PR
```

### Contribution Guidelines

- One feature per PR
- All 16 tests must pass
- Follow existing agent structure — same `run()` signature, same `span.finish()` pattern
- Update README if adding a connector or agent

---

## Running Tests

```bash
pytest tests/ -v
```

```
16 passed in 0.6s
```

---

## About

Built by **Harshit Tripathi** — Founder, Britcore AI · Lead Data Engineer

- Creator of **ATLAS Knowledge Graph** — AI-powered data lineage on Azure Databricks
- 10 years across Azure, Databricks, PySpark, Unity Catalog, Microsoft Fabric
- Databricks Certified Professional
- Cross-industry: retail, aerospace, healthcare

This project is part of the **Britcore.AI open source initiative** — practical AI tools for data engineers.

| | |
|--|--|
| 🌐 Website | [britcore.ai](https://britcore.ai) |
| 🐙 GitHub | [github.com/harshitboots](https://github.com/harshitboots) |
| 💼 LinkedIn | [linkedin.com/in/harshittripathi](https://linkedin.com/in/harshittripathi) |

---

## License

MIT License — free to use, modify and distribute. See [LICENSE](LICENSE) for full terms.

---

<div align="center">

<br/>

### If this tool saved you time or taught you something new

# ⭐ Star the repo

*It takes 2 seconds and helps thousands of data engineers find this tool.*  
*You also unlock a bonus free run on the live app.*

<br/>

[![Star this repo](https://img.shields.io/github/stars/harshitboots/multi-agent-data-pipeline?style=for-the-badge&color=yellow)](https://github.com/harshitboots/multi-agent-data-pipeline/stargazers)

<br/>

**Built with Claude AI · Powered by Britcore.AI · Made with ❤️ for the data engineering community**

</div>
