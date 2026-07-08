# Contributing

Thanks for considering a contribution to the Multi-Agent Data Pipeline.

## Getting started

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

CI (`.github/workflows/test.yml`) runs the full test suite on Python 3.10, 3.11 and 3.12 for every push and pull request against `main` — make sure `pytest tests/ -v` passes locally first.

## Ways to contribute

### Add a database connector

| Database | Difficulty |
|----------|-----------|
| MongoDB | Medium |
| Microsoft Fabric | Medium |
| Elasticsearch | Hard |

```python
# src/connectors/your_db.py

def connect(host: str, port: int, database: str, user: str, password: str): ...
def list_tables(host: str, ...) -> list: ...
def fetch_table(host: str, ..., table: str, limit: int = 1000) -> pd.DataFrame: ...
```

### Add an agent

Ideas: Schema Inferencer, Data Lineage Tracker, Duplicate Detector, Language Translator.

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

## Guidelines

- One feature per PR.
- All tests must pass (`pytest tests/ -v`) — CI enforces this on every PR.
- Follow the existing agent structure — same `run()` signature, same `span.finish()` pattern.
- Update the README if you add a connector or agent.
- Never commit real API keys, credentials, or `.env` files.

## Reporting bugs / requesting features

Use the issue templates under **Issues → New Issue**. For security vulnerabilities, see [SECURITY.md](SECURITY.md) instead of opening a public issue.
