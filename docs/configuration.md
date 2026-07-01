# Configuration Reference

> All configuration options, environment variables, cost model, guardrails, and build settings for the Multi-Agent Data Pipeline.

---

## Table of Contents

- [Environment Variables](#environment-variables)
- [Cost Model](#cost-model)
- [Router Configuration](#router-configuration)
- [Guardrail Thresholds](#guardrail-thresholds)
- [Credit System](#credit-system)
- [Streamlit Configuration](#streamlit-configuration)
- [Build Configuration](#build-configuration)
- [File Exclusions](#file-exclusions)
- [Cost Calculation Example](#cost-calculation-example)

---

## Environment Variables

The pipeline requires a single environment variable. Load it via `python-dotenv`.

### Setup

```bash
# Copy the template
cp .env.example .env

# Edit with your Anthropic API key
echo ANTHROPIC_API_KEY=sk-ant-your-key-here > .env
```

### Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Your Anthropic API key. Get one free at [console.anthropic.com](https://console.anthropic.com) |

The API key is loaded at pipeline startup. If using Streamlit Cloud, place the key in `.streamlit/secrets.toml` instead:

```toml
# .streamlit/secrets.toml
ANTHROPIC_API_KEY = "sk-ant-your-key-here"
```

The app reads `st.secrets` in cloud and `.env` locally — zero code changes required.

---

## Cost Model

All costs are defined in `src/cost_config.py`.

### Models

Two Claude model tiers are used:

```python
MODELS = {
    "fast":    "claude-haiku-4-5-20251001",
    "quality": "claude-sonnet-4-6",
}
```

### Pricing (USD per million tokens)

| Model | Input | Output |
|-------|-------|--------|
| Claude Haiku (`claude-haiku-4-5-20251001`) | $0.80 / M | $4.00 / M |
| Claude Sonnet (`claude-sonnet-4-6`) | $3.00 / M | $15.00 / M |

GBP conversion: `GBP_PER_USD = 0.79`

### Per-Agent Token Limits

Maximum output tokens per agent (controls response length):

| Agent | Max Tokens | Purpose |
|-------|-----------|---------|
| Cleaner | 400 | Short fix list |
| PII Anonymiser | 350 | PII rows + masks |
| Validator | 600 | Schema checks + violations |
| Transformer | 400 | Transformation list |
| Anomaly Detector | 550 | Anomaly list + score |
| Summariser | 1000 | Business summary |
| PDF Parser | 600 | Document structure |
| Entity Extractor | 700 | Named entities |
| Risk Detector | 600 | Risk flags + score |
| Action Extractor | 600 | Action items + owners |

### Per-Agent Timeouts

Maximum seconds before an agent is skipped:

| Agent | Timeout | Reason |
|-------|---------|--------|
| Cleaner | 12s | Simple mechanical task |
| PII Anonymiser | 10s | Pattern matching only |
| Validator | 18s | Schema judgment takes longer |
| Transformer | 12s | Column derivation |
| Anomaly Detector | 18s | Statistical analysis |
| Summariser | 20s | Longest generation — needs full context |
| PDF Parser | 15s | Document structure extraction |
| Entity Extractor | 15s | NER processing |
| Risk Detector | 15s | Compliance checks |
| Action Extractor | 15s | Decision extraction |

### Other Constants

```python
MAX_INPUT_TOKENS = 8000      # Max CSV preview sent to each agent
FREE_RUNS = 2                # Anonymous free runs (IP fingerprint)
STAR_BONUS_RUNS = 3          # Bonus runs for starring repo
LIFETIME_ACCESS_RUNS = 9999  # Effectively unlimited for fork + follow
```

### Cost Calculation Functions

```python
from src.cost_config import compute_cost_usd, compute_cost_gbp

# Calculate cost in USD
cost_usd = compute_cost_usd("claude-sonnet-4-6", input_tokens=500, output_tokens=200)

# Calculate cost in GBP (auto-converts)
cost_gbp = compute_cost_gbp("claude-sonnet-4-6", input_tokens=500, output_tokens=200)
```

---

## Router Configuration

The router engine (`src/router.py`) assigns the cheapest model that can handle each agent's task.

### Agent Classification

```python
SIMPLE_AGENTS = {"cleaner", "pii_anonymiser", "transformer"}
COMPLEX_AGENTS = {"validator", "anomaly", "summariser",
                  "pdf_parser", "entity_extractor", "risk_detector", "action_extractor"}
```

### Routing Logic

| Agent | With Router | Without Router | Why |
|-------|-------------|----------------|-----|
| Cleaner | Haiku | Sonnet | Mechanical formatting — no reasoning needed |
| PII Anonymiser | Haiku | Sonnet | Pattern-based detection |
| Transformer | Haiku | Sonnet | Column derivation — structured, deterministic |
| Validator | Sonnet | Sonnet | Schema judgment — needs reasoning |
| Anomaly Detector | Sonnet | Sonnet | Statistical reasoning — needs quality |
| Summariser | Sonnet | Sonnet | Business insights — full quality required |
| PDF Parser | Haiku | Sonnet | Document structure extraction |
| Entity Extractor | Haiku | Sonnet | Pattern-based NER |
| Risk Detector | Sonnet | Sonnet | Compliance reasoning |
| Action Extractor | Sonnet | Sonnet | Decision extraction |

### Disabling Routing

Pass `routing_enabled=False` to the pipeline to force all agents to use Sonnet:

```python
from src.pipeline import run_pipeline

result = run_pipeline("data.csv", routing_enabled=False)
```

### Row Threshold

```python
ROW_THRESHOLD = 500  # Not currently used for routing — reserved for future use
```

---

## Guardrail Thresholds

The guardrail engine (`src/observability/guardrails.py`) enforces safety limits during pipeline execution.

### Default Configuration

```python
from src.observability.guardrails import GuardrailEngine

guardrails = GuardrailEngine(
    budget_cap_gbp=0.50,
    agent_timeout_s=30,
    min_completeness=60.0,
    max_pii_rows=0,
    max_parse_failures=3,
    anomaly_score_warn=9.0,
    enabled=True,
)
```

### Threshold Reference

| Threshold | Default | Action | Description |
|-----------|---------|--------|-------------|
| `budget_cap_gbp` | £0.50 | **Stop** pipeline | Maximum spend per run. Warns at 80%, stops at 100%. |
| `agent_timeout_s` | 30s | **Skip** agent | If an agent takes longer, it's skipped and the pipeline continues. |
| `min_completeness` | 60.0% | **Warn** | Validator completeness score. Below this = flag for review. |
| `max_pii_rows` | 0 | **Warn** | Max rows with PII before warning. `0` = warn on any detection. |
| `max_parse_failures` | 3 | **Stop** pipeline | Max agents that fail JSON parse. Abort if exceeded. |
| `anomaly_score_warn` | 9.0/10 | **Warn** | Anomaly score threshold. Above this = recommend human review. |
| `enabled` | True | — | Master switch. `False` disables all guardrails. |

### Guardrail Result Actions

Every guardrail check returns a `GuardrailResult`:

```python
@dataclass
class GuardrailResult:
    passed: bool        # Did the check pass?
    action: str         # "continue" | "warn" | "stop" | "skip"
    severity: str       # "info" | "warning" | "critical"
    reason: str         # Human-readable message
    guardrail_type: str # Which check (budget_cap, pii_rows_detected, etc.)
    value: float        # Actual value measured
    threshold: float    # Threshold it was compared against
```

### When Guardrails Fire

| Event | Severity | Example |
|-------|----------|---------|
| Budget at 80% | Warning | "Budget at 80% — £0.4000 of £0.50" |
| Budget exceeded | Critical | "Budget cap reached: £0.5100 >= £0.50" |
| PII detected | Warning | "PII detected in 3 rows — data was anonymised" |
| Low completeness | Warning | "Completeness score 55.0% below threshold 60%" |
| High anomaly score | Warning | "Anomaly score 9.5/10 — high risk data" |
| Parse failures hit | Critical | "3 parse failures — pipeline reliability compromised" |

---

## Credit System

The pipeline tracks runs per visitor using IP fingerprinting (SHA-256 hash of IP + User-Agent). No cookies or session storage for anonymous users.

### Tier Breakdown

| Tier | Total Runs | How to Earn | Verification |
|------|-----------|-------------|--------------|
| **Anonymous** | 2 | Automatic on first visit | IP fingerprint (SHA-256) |
| **Free** | 2 | Enter GitHub username | GitHub username stored |
| **Star + Follow** | 5 | Star repo + follow @harshitboots | GitHub API live check |
| **Lifetime** | Unlimited | Fork repo + follow @harshitboots | GitHub API live check |
| **BYOK** | Unlimited | Paste your own `sk-ant-...` key | Session-only, never persisted |

### How Credits Work

1. **Anonymous** — First 2 runs are free. The app hashes your IP + User-Agent and stores it in SQLite. Runs survive page refresh.
2. **Star Bonus** — Star the repo on GitHub. The app verifies via GitHub API and adds 3 bonus runs.
3. **Lifetime** — Fork the repo + follow. Verified via GitHub API. Effectively unlimited (9999 runs).
4. **BYOK** — Paste your Anthropic API key in the sidebar. Stored in `st.session_state` only — never written to disk, SQLite, or logs. Disappears when you close the tab.

### VPN / Proxy Blocking

All VPN, proxy, and hosting IPs are blocked at startup via [ip-api.com](https://ip-api.com). Private/localhost IPs (`127.0.0.1`, `192.168.x.x`, `10.x.x.x`) are always allowed for local development.

---

## Streamlit Configuration

Theme and server settings in `.streamlit/config.toml`.

### Theme

```toml
[theme]
base = "dark"
primaryColor = "#6366f1"
backgroundColor = "#0f172a"
secondaryBackgroundColor = "#1e293b"
textColor = "#f1f5f9"
font = "sans serif"
```

### Server

```toml
[server]
headless = true
enableCORS = false
enableXsrfProtection = true
```

| Setting | Value | Purpose |
|---------|-------|---------|
| `headless` | `true` | No browser auto-open — required for cloud deployment |
| `enableCORS` | `false` | Disable CORS for iframe embedding |
| `enableXsrfProtection` | `true` | Cross-site request forgery protection |

### Browser

```toml
[browser]
gatherUsageStats = false
```

Disables Streamlit telemetry collection.

---

## Build Configuration

Defined in `pyproject.toml`.

### Project Metadata

| Setting | Value |
|---------|-------|
| Build system | `setuptools >= 68.0` |
| Python requirement | `>= 3.10` |
| CLI entrypoint | `multi-agent-pipeline = "main:app"` |

### Test Configuration

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
```

Run tests:

```bash
pytest tests/ -v          # All tests
pytest tests/test_pipeline.py -v  # Single file
pytest -k test_pii        # By name
```

Tests validate models, regex patterns, CSV loading, and DuckDB connector — no LLM calls.

---

## File Exclusions

Rules from `.gitignore`:

### Excluded

| Pattern | Reason |
|---------|--------|
| `.env` | Contains API key — never committed |
| `venv/`, `myenv/` | Virtual environments |
| `__pycache__/`, `*.pyc` | Python bytecode |
| `*.db` | SQLite databases generated at runtime |
| `.streamlit/secrets.toml` | Streamlit secrets — never committed |
| `.opencode/` | Editor config |
| `AGENTS.md` | Agent instructions — project-specific |
| `.tmp/` | Temporary files |

### Excluded CSV (with exception)

```gitignore
*.csv
!demo/sample_data.csv
```

All CSV files are excluded **except** the demo sample. This prevents accidentally committing data files while keeping the demo intact.

### Runtime Files

These are generated during execution and should not be committed:

- `pipeline_runs.db` — SQLite observability store
- `anon_visitors.db` — Anonymous visitor tracking

---

## Cost Calculation Example

### Scenario: CSV Pipeline with 15 Rows

Running the demo CSV (`demo/sample_data.csv`, 15 rows) in both modes.

#### Without Router (All Sonnet)

Every agent uses Claude Sonnet:

| Agent | Input Tokens | Output Tokens | Model | Cost (USD) |
|-------|-------------|---------------|-------|------------|
| Cleaner | 1200 | 150 | Sonnet | $0.0036 |
| PII Anonymiser | 1200 | 120 | Sonnet | $0.0036 |
| Validator | 1200 | 200 | Sonnet | $0.0036 |
| Transformer | 1200 | 150 | Sonnet | $0.0036 |
| Anomaly Detector | 1200 | 180 | Sonnet | $0.0036 |
| Summariser | 1200 | 350 | Sonnet | $0.0059 |
| **Total** | **7200** | **1150** | | **$0.0239** |

**GBP: $0.0239 × 0.79 = £0.0189**

#### With Router (Haiku + Sonnet)

Simple agents use Haiku, complex agents use Sonnet:

| Agent | Input Tokens | Output Tokens | Model | Cost (USD) |
|-------|-------------|---------------|-------|------------|
| Cleaner | 1200 | 150 | Haiku | $0.0006 |
| PII Anonymiser | 1200 | 120 | Haiku | $0.0005 |
| Validator | 1200 | 200 | Sonnet | $0.0036 |
| Transformer | 1200 | 150 | Haiku | $0.0006 |
| Anomaly Detector | 1200 | 180 | Sonnet | $0.0036 |
| Summariser | 1200 | 350 | Sonnet | $0.0059 |
| **Total** | **7200** | **1150** | | **$0.0148** |

**GBP: $0.0148 × 0.79 = £0.0117**

#### Savings

| Metric | Value |
|--------|-------|
| Cost without router | £0.0189 |
| Cost with router | £0.0117 |
| Savings | £0.0072 (38%) |

At scale (1000 runs/month):

| Metric | Without Router | With Router | Monthly Savings |
|--------|---------------|-------------|-----------------|
| Cost | £18.90 | £11.70 | £7.20 |
| Runs | 1000 | 1000 | — |

**Note:** The actual savings depend on token counts. The router provides ~30-70% savings depending on data complexity and row count. Larger datasets amplify savings because Haiku agents process them at 3-4× cheaper per token.

---

## Quick Reference

### Essential Commands

```bash
# Run locally
streamlit run app.py

# Run CLI
python main.py demo/sample_data.csv

# Run tests
pytest tests/ -v
```

### Key Paths

| Path | Purpose |
|------|---------|
| `src/cost_config.py` | All pricing, token limits, timeouts |
| `src/router.py` | Agent routing logic |
| `src/observability/guardrails.py` | Guardrail thresholds |
| `.streamlit/config.toml` | UI theme and server config |
| `.env` | API key (local) |
| `.streamlit/secrets.toml` | API key (cloud) |
