# Changelog

All notable changes to Multi-Agent Data Pipeline are documented here.

---

## [2.0.0] — 2026-06-26

### What's new

#### Router Engine
- New `src/router.py` — routes each agent to the cheapest model that can handle it
- Simple agents (Cleaner, PII Anonymiser, Transformer) → Claude Haiku (~80% cheaper)
- Complex agents (Validator, Anomaly, Summariser) → Claude Sonnet (full quality)
- Toggle in UI — run WITH router or WITHOUT router (all-Sonnet baseline) and compare costs side by side
- Estimated cost per run drops from ~£0.27 (all-Sonnet) to ~£0.08 (routed)

#### Parallel Execution
- Wave 1 agents (Cleaner, PII, Validator, Transformer, Anomaly) now run concurrently via `ThreadPoolExecutor`
- Wave 2 (Summariser) runs after Wave 1 completes, with full context
- Wall-clock latency drops ~63%: from ~14s sequential to ~5s parallel
- Zero quality impact — same inputs, same outputs, just concurrent

#### Observability Dashboard (`pages/observability.py`)
- Live Monitor tab — last run agent waterfall with latency bars, Agent Inspector (prompts, raw responses, parsed output)
- Run History tab — all runs in SQLite, per-run span drill-down
- Cost Analytics tab — spend over time, Haiku vs Sonnet breakdown, cost by mode
- Agent Performance tab — reliability %, avg latency, parse failure rate per agent
- Guardrails Log tab — every guardrail event with severity colour coding
- Settings tab — configure guardrail thresholds (budget cap, timeout, PII limits, parse failure limits)

#### BYOK — Bring Your Own Key
- 2 free runs per GitHub username (router mode, ~£0.06 each)
- +1 bonus run after starring the repo (verified via GitHub API — not honour system)
- After free runs: user provides own `sk-ant-...` key in a password input
- Key stored in `st.session_state` only — never written to SQLite, files, or logs

#### Cost Comparison Dashboard
- Single toggle selects mode (WITH or WITHOUT router)
- `st.session_state` stores both run results independently
- Comparison table auto-appears when both modes have been run — agent-by-agent cost + saving %
- Summary metrics: total cost saved (GBP), latency saved (%), quality delta (%)

#### Guardrails Engine
- `src/observability/guardrails.py` — configurable thresholds
- Budget cap per run, agent timeout, min completeness score, max PII rows, max parse failures, anomaly score warning
- Actions: `continue` / `warn` / `stop` / `skip` — per guardrail type
- All guardrail events persisted to SQLite `guardrail_events` table

#### SQLite Persistence
- `pipeline_runs.db` auto-created on first run (not committed to git)
- Tables: `runs`, `agent_spans`, `guardrail_events`, `budget`
- Survives app restarts — full history available in observability dashboard

### Files added
- `pages/observability.py`
- `src/router.py`
- `src/cost_config.py`
- `src/observability/__init__.py`
- `src/observability/tracer.py`
- `src/observability/store.py`
- `src/observability/guardrails.py`
- `src/observability/metrics.py`
- `src/auth/__init__.py`
- `src/auth/credits.py`
- `src/auth/github_api.py`

### Files modified
- `app.py` — router toggle, BYOK, credits, cost comparison dashboard
- `src/pipeline.py` — parallel execution, router, telemetry
- `src/models.py` — AgentTelemetry, RouterDecisionModel, extended PipelineResult
- `src/agents/cleaner.py` — model param, span telemetry
- `src/agents/validator.py` — model param, span telemetry
- `src/agents/transformer.py` — model param, span telemetry
- `src/agents/anomaly.py` — model param, span telemetry
- `src/agents/summariser.py` — model param, span telemetry
- `src/agents/pii_anonymiser.py` — span telemetry (regex-engine, zero token cost)

---

## [1.0.0] — 2025 (initial release)

- 6-agent CSV pipeline: Cleaner, PII Anonymiser, Validator, Transformer, Anomaly Detector, Summariser
- 5-agent PDF intelligence pipeline: Parser, Entity Extractor, Risk Detector, Action Extractor, Summariser
- 6 database connectors: Azure Databricks, Snowflake, PostgreSQL, MySQL, BigQuery, DuckDB
- Streamlit UI with dark theme
- CLI entrypoint (`main.py`)
- JSON export
- Demo CSV and PDF datasets
- Community connector contributions (`contrib/`)
