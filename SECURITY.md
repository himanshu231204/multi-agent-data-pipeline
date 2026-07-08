# Security Policy

## Supported Versions

Only the latest release on the `main` branch is supported with security fixes.

| Version | Supported |
|---------|-----------|
| 1.2.x   | ✅ |
| < 1.2   | ❌ |

## Reporting a Vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Instead, report privately via:
- GitHub's [private vulnerability reporting](https://github.com/harshitboots/multi-agent-data-pipeline/security/advisories/new) (preferred), or
- Email: harshit@britcore.ai

Include a description of the issue, steps to reproduce, and the potential impact. You should expect an initial response within 5 business days.

## Scope

This project handles two categories of sensitive data:

- **API credentials** — Anthropic API keys (via `.env`, `st.secrets`, or BYOK in the sidebar) and database connector credentials (Databricks, Snowflake, Postgres, MySQL, BigQuery, Redshift).
- **User-uploaded data** — CSV/PDF files may contain PII, which the PII Anonymiser agent is designed to detect and mask before downstream processing.

Reports in these areas are especially welcome:
- Ways a BYOK key or connector credential could leak into logs, SQLite (`pipeline_runs.db`), or the observability dashboard.
- Ways PII could bypass the anonymiser and reach an LLM prompt or the run history.
- Injection risks in database connector queries (e.g. `src/connectors/*.py` table-name interpolation).
- Bypasses of the VPN/proxy access-control block.

## Known Design Notes (not vulnerabilities)

- BYOK API keys are stored only in `st.session_state` for the browser session — never persisted to disk or SQLite.
- Anonymous run tracking stores a SHA-256 hash of IP + User-Agent, never the raw IP.
