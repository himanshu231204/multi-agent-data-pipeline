# API Reference — Multi-Agent Data Pipeline

Complete reference for every public function, class, and model in the pipeline.

---

## Table of Contents

- [Pipeline (`src/pipeline.py`)](#pipeline-srcpipelinepy)
- [Router (`src/router.py`)](#router-srcrouterpy)
- [Cost Config (`src/cost_config.py`)](#cost-config-srccost_configpy)
- [Models (`src/models.py`)](#models-srcmodelspy)
- [Tracer (`src/observability/tracer.py`)](#tracer-srcobservabilitytracerpy)
- [Guardrails (`src/observability/guardrails.py`)](#guardrails-srcobservabilityguardrailspy)
- [Store (`src/observability/store.py`)](#store-srcobservabilitystorepy)
- [Metrics (`src/observability/metrics.py`)](#metrics-srcobservabilitymetricspy)
- [Credits (`src/auth/credits.py`)](#credits-srcauthcreditspy)
- [GitHub API (`src/auth/github_api.py`)](#github-api-srcauthgithub_apipy)
- [Report Generator (`src/report_generator.py`)](#report-generator-srcreport_generatorpy)

---

## Pipeline (`src/pipeline.py`)

### `load_csv`

```python
def load_csv(file_path: str) -> tuple[pd.DataFrame, str, int]:
```

Load a CSV file and return the DataFrame, a CSV preview string, and total row count.

| Parameter  | Type   | Default | Description                          |
|------------|--------|---------|--------------------------------------|
| `file_path`| `str`  | —       | Path to the CSV file                 |

**Returns** `tuple[pd.DataFrame, str, int]` — `(df, preview_csv, total_rows)` where `preview_csv` is the first 20 rows as a CSV string.

```python
import pandas as pd
from src.pipeline import load_csv

df, preview, total_rows = load_csv("demo/sample_data.csv")

print(f"Loaded {total_rows} rows")
print(f"Columns: {list(df.columns)}")
print(f"Preview (first 5 rows):\n{preview[:500]}")
```

---

### `run_pipeline`

```python
def run_pipeline(file_path: str, routing_enabled: bool = False,
                 guardrails: GuardrailEngine = None,
                 api_key: str = None) -> PipelineResult:
```

Run the full multi-agent pipeline on a CSV file. Executes Wave 1 (5 agents in parallel), then Wave 2 (summariser with context).

| Parameter        | Type             | Default  | Description                                        |
|------------------|------------------|----------|----------------------------------------------------|
| `file_path`      | `str`            | —        | Path to the CSV file to process                    |
| `routing_enabled`| `bool`           | `False`  | Enable Haiku/Sonnet routing (saves cost)           |
| `guardrails`     | `GuardrailEngine`| `None`   | Custom guardrails (defaults to `DEFAULT_GUARDRAILS`)|
| `api_key`        | `str`            | `None`   | Anthropic API key (overrides env var)               |

**Returns** `PipelineResult` — full result with all agent outputs, telemetry, routing decisions, and cost.

```python
from src.pipeline import run_pipeline
from src.observability.guardrails import GuardrailEngine

# Basic run — all agents use Sonnet (baseline)
result = run_pipeline("demo/sample_data.csv")
print(f"Cost: £{result.total_cost_gbp:.5f}")
print(f"Quality: {result.quality_score}%")

# With routing — simple agents use Haiku (cheaper)
result = run_pipeline("demo/sample_data.csv", routing_enabled=True)

# With custom guardrails
guardrails = GuardrailEngine(budget_cap_gbp=0.25, max_parse_failures=5)
result = run_pipeline("demo/sample_data.csv", guardrails=guardrails)

# With BYOK (Bring Your Own Key)
result = run_pipeline("demo/sample_data.csv", api_key="sk-ant-...")

# Access individual agent results
print(f"Cleaner fixed {result.cleaner.issues_fixed}")
print(f"Validator completeness: {result.validator.completeness_score}%")
print(f"Anomaly score: {result.anomaly.anomaly_score}/10")
print(f"Summary: {result.summariser.summary[:200]}")
```

---

## Router (`src/router.py`)

### `RouterDecision`

```python
@dataclass
class RouterDecision:
    agent_name: str
    model: str
    model_label: str
    reason: str
    routing_enabled: bool
```

Returned by `route()`. Describes which model was assigned to an agent and why.

| Field            | Type   | Description                                    |
|------------------|--------|------------------------------------------------|
| `agent_name`     | `str`  | Agent being routed (e.g. `"cleaner"`)          |
| `model`          | `str`  | Model ID (e.g. `"claude-haiku-4-5-20251001"`) |
| `model_label`    | `str`  | Human label (`"Haiku"` or `"Sonnet"`)          |
| `reason`         | `str`  | Routing rationale                              |
| `routing_enabled`| `bool` | Whether routing was active                     |

```python
from src.router import route

decision = route("cleaner", total_rows=100, routing_enabled=True)
print(f"{decision.agent_name} -> {decision.model_label}")
# Output: cleaner -> Haiku

decision = route("summariser", total_rows=100, routing_enabled=True)
print(f"{decision.agent_name} -> {decision.model_label}")
# Output: summariser -> Sonnet
```

---

### `route`

```python
def route(agent_name: str, total_rows: int = 0, routing_enabled: bool = True) -> RouterDecision:
```

Route an agent to the appropriate model.

**Routing logic:**
- `routing_enabled=False` → all agents use Sonnet (baseline)
- `routing_enabled=True` → simple agents (`cleaner`, `pii_anonymiser`, `transformer`) use Haiku; complex agents use Sonnet

| Parameter        | Type   | Default | Description                              |
|------------------|--------|---------|------------------------------------------|
| `agent_name`     | `str`  | —       | Agent to route                           |
| `total_rows`     | `int`  | `0`     | Row count (currently unused in logic)    |
| `routing_enabled`| `bool` | `True`  | Whether to apply routing                 |

**Returns** `RouterDecision`

```python
from src.router import route, SIMPLE_AGENTS, COMPLEX_AGENTS

# Check which agents are simple vs complex
print(f"Simple agents: {SIMPLE_AGENTS}")
# {'cleaner', 'pii_anonymiser', 'transformer'}

print(f"Complex agents: {COMPLEX_AGENTS}")
# {'validator', 'anomaly', 'summariser', 'pdf_parser', 'entity_extractor', 'risk_detector', 'action_extractor'}

# Route each agent type
for agent in ["cleaner", "validator", "anomaly", "summariser"]:
    d = route(agent, total_rows=500, routing_enabled=True)
    print(f"  {d.agent_name:20s} -> {d.model_label:8s} ({d.reason})")
```

---

### `baseline_model`

```python
def baseline_model() -> str:
```

Return the baseline model ID (always Sonnet).

**Returns** `str` — `"claude-sonnet-4-6"`

```python
from src.router import baseline_model

model = baseline_model()
print(model)  # claude-sonnet-4-6
```

---

## Cost Config (`src/cost_config.py`)

### Constants

| Constant           | Type   | Value / Description                                  |
|--------------------|--------|------------------------------------------------------|
| `MODELS`           | `dict` | `{"fast": "claude-haiku-4-5-20251001", "quality": "claude-sonnet-4-6"}` |
| `PRICING`          | `dict` | USD per million tokens per model                     |
| `GBP_PER_USD`      | `float`| `0.79`                                               |
| `FREE_RUNS`        | `int`  | `2` — free runs for anonymous users                  |
| `STAR_BONUS_RUNS`  | `int`  | `3` — bonus for starring the repo                    |
| `LIFETIME_ACCESS_RUNS` | `int` | `9999` — unlimited (fork + follow)               |
| `MAX_INPUT_TOKENS` | `int`  | `8000` — max tokens sent to any agent                |
| `AGENT_MAX_TOKENS` | `dict` | Max output tokens per agent (400–1000)               |
| `AGENT_TIMEOUTS`   | `dict` | Timeout in seconds per agent (10–20)                 |

```python
from src.cost_config import MODELS, PRICING, AGENT_MAX_TOKENS, AGENT_TIMEOUTS

print(f"Fast model: {MODELS['fast']}")
# claude-haiku-4-5-20251001

print(f"Quality model: {MODELS['quality']}")
# claude-sonnet-4-6

print(f"Sonnet input price: ${PRICING['claude-sonnet-4-6']['input_per_m']}/M tokens")
# $3.00/M tokens

print(f"Summariser max tokens: {AGENT_MAX_TOKENS['summariser']}")
# 1000

print(f"Validator timeout: {AGENT_TIMEOUTS['validator']}s")
# 18
```

---

### `compute_cost_usd`

```python
def compute_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
```

Calculate API cost in USD.

| Parameter      | Type  | Default | Description                    |
|----------------|-------|---------|--------------------------------|
| `model`        | `str` | —       | Model ID (from `MODELS`)       |
| `input_tokens` | `int` | —       | Number of input tokens         |
| `output_tokens`| `int` | —       | Number of output tokens        |

**Returns** `float` — cost in USD

```python
from src.cost_config import compute_cost_usd

# Haiku: $0.80/M input, $4.00/M output
cost = compute_cost_usd("claude-haiku-4-5-20251001", input_tokens=1000, output_tokens=200)
print(f"Cost: ${cost:.6f}")  # $0.000880

# Sonnet: $3.00/M input, $15.00/M output
cost = compute_cost_usd("claude-sonnet-4-6", input_tokens=1000, output_tokens=200)
print(f"Cost: ${cost:.6f}")  # $0.006000
```

---

### `compute_cost_gbp`

```python
def compute_cost_gbp(model: str, input_tokens: int, output_tokens: int) -> float:
```

Calculate API cost in GBP (USD × 0.79).

| Parameter      | Type  | Default | Description                    |
|----------------|-------|---------|--------------------------------|
| `model`        | `str` | —       | Model ID                       |
| `input_tokens` | `int` | —       | Number of input tokens         |
| `output_tokens`| `int` | —       | Number of output tokens        |

**Returns** `float` — cost in GBP

```python
from src.cost_config import compute_cost_gbp

cost = compute_cost_gbp("claude-sonnet-4-6", input_tokens=5000, output_tokens=1000)
print(f"Cost: £{cost:.6f}")  # £0.019500
```

---

## Models (`src/models.py`)

All models are Pydantic v2 `BaseModel` classes.

### `CleanerResult`

```python
class CleanerResult(BaseModel):
    issues_fixed: List[str]
    rows_affected: int
    cleaned_columns: List[str]
```

Output from the Cleaner agent.

| Field            | Type         | Description                              |
|------------------|--------------|------------------------------------------|
| `issues_fixed`   | `List[str]`  | List of issues found and fixed           |
| `rows_affected`  | `int`        | Number of rows that had issues           |
| `cleaned_columns`| `List[str]`  | Column names that were cleaned           |

```python
from src.models import CleanerResult

result = CleanerResult(
    issues_fixed=["Removed 3 duplicate rows", "Filled 12 null values in 'age'"],
    rows_affected=15,
    cleaned_columns=["age", "email", "name"]
)

print(f"Fixed {len(result.issues_fixed)} issues in {result.rows_affected} rows")
# Fixed 2 issues in 15 rows
```

---

### `ValidatorResult`

```python
class ValidatorResult(BaseModel):
    schema_ok: bool
    violations: List[str]
    passed_checks: List[str]
    completeness_score: float
```

| Field                | Type         | Description                                |
|----------------------|--------------|--------------------------------------------|
| `schema_ok`          | `bool`       | `True` if no schema violations             |
| `violations`         | `List[str]`  | List of schema violations found            |
| `passed_checks`      | `List[str]`  | List of checks that passed                 |
| `completeness_score` | `float`      | Completeness percentage (0–100)            |

```python
from src.models import ValidatorResult

result = ValidatorResult(
    schema_ok=True,
    violations=[],
    passed_checks=["Column types valid", "No empty required fields", "Date format correct"],
    completeness_score=94.5
)

if result.completeness_score < 60:
    print("WARNING: Data completeness below threshold")
```

---

### `TransformerResult`

```python
class TransformerResult(BaseModel):
    transformations_applied: List[str]
    new_columns: List[str]
    rows_transformed: int
```

| Field                      | Type         | Description                        |
|----------------------------|--------------|------------------------------------|
| `transformations_applied`  | `List[str]`  | List of transformations performed  |
| `new_columns`              | `List[str]`  | Column names that were created     |
| `rows_transformed`         | `int`        | Number of rows modified            |

```python
from src.models import TransformerResult

result = TransformerResult(
    transformations_applied=["Normalized 'price' to USD", "Created 'year' from 'date'"],
    new_columns=["price_usd", "year"],
    rows_transformed=500
)
```

---

### `AnomalyResult`

```python
class AnomalyResult(BaseModel):
    anomalies: List[str]
    anomaly_count: int
    anomaly_score: float
    flagged_rows: List[int]
```

| Field            | Type         | Description                                  |
|------------------|--------------|----------------------------------------------|
| `anomalies`      | `List[str]`  | Descriptions of detected anomalies           |
| `anomaly_count`  | `int`        | Total anomaly count                          |
| `anomaly_score`  | `float`      | Risk score 0–10 (10 = highest risk)          |
| `flagged_rows`   | `List[int]`  | Row indices that were flagged                |

```python
from src.models import AnomalyResult

result = AnomalyResult(
    anomalies=["Row 42: price is 10x average", "Row 108: negative age value"],
    anomaly_count=2,
    anomaly_score=7.5,
    flagged_rows=[42, 108]
)

if result.anomaly_score >= 9.0:
    print("CRITICAL: High anomaly score — human review recommended")
```

---

### `SummariserResult`

```python
class SummariserResult(BaseModel):
    summary: str
    key_stats: dict
    recommendations: List[str]
```

| Field              | Type         | Description                        |
|--------------------|--------------|------------------------------------|
| `summary`          | `str`        | Natural language summary           |
| `key_stats`        | `dict`       | Key statistics as key-value pairs  |
| `recommendations`  | `List[str]`  | Actionable recommendations         |

```python
from src.models import SummariserResult

result = SummariserResult(
    summary="Dataset contains 500 customer records with 94% completeness. 2 anomalies detected.",
    key_stats={"total_rows": 500, "completeness": 94.5, "anomalies": 2},
    recommendations=["Review flagged anomalies", "Fill missing email fields"]
)

print(result.summary)
for rec in result.recommendations:
    print(f"  -> {rec}")
```

---

### `PIIAnonymiserResult`

```python
class PIIAnonymiserResult(BaseModel):
    pii_found: List[str]
    rows_affected: int
    pii_types_detected: List[str]
    anonymised_preview: str
```

| Field                | Type         | Description                                    |
|----------------------|--------------|------------------------------------------------|
| `pii_found`          | `List[str]`  | Raw PII values found (before anonymisation)    |
| `rows_affected`      | `int`        | Number of rows containing PII                  |
| `pii_types_detected` | `List[str]`  | Types of PII found (e.g. `"email"`, `"phone"`) |
| `anonymised_preview` | `str`        | CSV preview of anonymised data                 |

```python
from src.models import PIIAnonymiserResult

result = PIIAnonymiserResult(
    pii_found=["john@example.com", "+44 7700 900123"],
    rows_affected=2,
    pii_types_detected=["email", "phone"],
    anonymised_preview="name,email,phone\nJohn,[REDACTED],[REDACTED]"
)
```

---

### `AgentTelemetry`

```python
class AgentTelemetry(BaseModel):
    agent_name: str
    model: str
    model_label: str
    input_tokens: int
    output_tokens: int
    cost_gbp: float
    latency_ms: int
    status: str
    parse_ok: bool
    error_message: str = ""
    guardrails_fired: List[dict] = []
    routing_reason: str = ""
```

Per-agent telemetry recorded during a pipeline run.

| Field              | Type           | Description                                    |
|--------------------|----------------|------------------------------------------------|
| `agent_name`       | `str`          | Agent name (e.g. `"cleaner"`)                  |
| `model`            | `str`          | Full model ID used                             |
| `model_label`      | `str`          | `"Haiku"` or `"Sonnet"`                        |
| `input_tokens`     | `int`          | Tokens consumed as input                       |
| `output_tokens`    | `int`          | Tokens produced as output                      |
| `cost_gbp`         | `float`        | Cost in GBP                                    |
| `latency_ms`       | `int`          | Latency in milliseconds                        |
| `status`           | `str`          | `"complete"`, `"error"`, or `"timeout"`        |
| `parse_ok`         | `bool`         | `True` if JSON response parsed successfully    |
| `error_message`    | `str`          | Error details (empty if none)                  |
| `guardrails_fired` | `List[dict]`   | Guardrail events triggered during this agent   |
| `routing_reason`   | `str`          | Why this model was chosen                      |

```python
from src.models import AgentTelemetry

telemetry = AgentTelemetry(
    agent_name="cleaner",
    model="claude-haiku-4-5-20251001",
    model_label="Haiku",
    input_tokens=1200,
    output_tokens=350,
    cost_gbp=0.0012,
    latency_ms=850,
    status="complete",
    parse_ok=True
)

print(f"{telemetry.agent_name}: {telemetry.latency_ms}ms, £{telemetry.cost_gbp:.5f}")
```

---

### `RouterDecisionModel`

```python
class RouterDecisionModel(BaseModel):
    agent_name: str
    model: str
    model_label: str
    reason: str
    routing_enabled: bool
```

Pydantic version of `RouterDecision` for serialization in `PipelineResult`.

```python
from src.models import RouterDecisionModel

rd = RouterDecisionModel(
    agent_name="anomaly",
    model="claude-sonnet-4-6",
    model_label="Sonnet",
    reason="Complex reasoning task — Sonnet required for quality",
    routing_enabled=True
)
```

---

### `PipelineResult`

```python
class PipelineResult(BaseModel):
    file_name: str
    total_rows: int
    cleaner: Optional[CleanerResult] = None
    pii: Optional[PIIAnonymiserResult] = None
    validator: Optional[ValidatorResult] = None
    transformer: Optional[TransformerResult] = None
    anomaly: Optional[AnomalyResult] = None
    summariser: Optional[SummariserResult] = None
    status: str = "complete"
    run_id: str = ""
    mode: str = "no_router"
    telemetry: List[AgentTelemetry] = []
    routing_decisions: List[RouterDecisionModel] = []
    total_cost_gbp: float = 0.0
    total_latency_ms: int = 0
    guardrail_events: List[dict] = []
    quality_score: float = 100.0
```

The top-level result object returned by `run_pipeline()`.

| Field                | Type                          | Description                                |
|----------------------|-------------------------------|--------------------------------------------|
| `file_name`          | `str`                         | Original CSV filename                      |
| `total_rows`         | `int`                         | Row count                                  |
| `cleaner`            | `Optional[CleanerResult]`     | Cleaner agent output                       |
| `pii`                | `Optional[PIIAnonymiserResult]`| PII anonymiser output                    |
| `validator`          | `Optional[ValidatorResult]`   | Validator agent output                     |
| `transformer`        | `Optional[TransformerResult]` | Transformer agent output                   |
| `anomaly`            | `Optional[AnomalyResult]`     | Anomaly detector output                    |
| `summariser`         | `Optional[SummariserResult]`  | Summariser agent output                    |
| `status`             | `str`                         | `"complete"`, `"stopped_budget"`, `"stopped_parse_failures"` |
| `run_id`             | `str`                         | 8-char UUID for this run                   |
| `mode`               | `str`                         | `"with_router"` or `"no_router"`           |
| `telemetry`          | `List[AgentTelemetry]`        | Per-agent telemetry                        |
| `routing_decisions`  | `List[RouterDecisionModel]`   | Model assignments per agent                |
| `total_cost_gbp`     | `float`                       | Total cost in GBP                          |
| `total_latency_ms`   | `int`                         | Total pipeline latency                     |
| `guardrail_events`   | `List[dict]`                  | All guardrail events across agents         |
| `quality_score`      | `float`                       | Quality score 0–100                        |

```python
from src.pipeline import run_pipeline

result = run_pipeline("demo/sample_data.csv", routing_enabled=True)

# Print summary
print(f"Run: {result.run_id}")
print(f"Status: {result.status}")
print(f"Mode: {result.mode}")
print(f"Total cost: £{result.total_cost_gbp:.5f}")
print(f"Total latency: {result.total_latency_ms}ms")
print(f"Quality score: {result.quality_score}%")

# Iterate telemetry
for t in result.telemetry:
    print(f"  {t.agent_name:20s} {t.model_label:8s} {t.latency_ms}ms £{t.cost_gbp:.5f}")

# Access specific results
if result.anomaly:
    print(f"Anomaly score: {result.anomaly.anomaly_score}/10")
```

---

## Tracer (`src/observability/tracer.py`)

### `AgentSpan`

```python
@dataclass
class AgentSpan:
    run_id: str
    agent_name: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_gbp: float = 0.0
    latency_ms: int = 0
    status: str = "pending"
    parse_ok: bool = True
    system_prompt: str = ""
    user_message: str = ""
    raw_response: str = ""
    parsed_output: str = ""
    error_message: str = ""
    guardrails_fired: list = field(default_factory=list)
    started_at: float = field(default_factory=time.time)
```

Tracks one agent's execution within a run.

#### `AgentSpan.finish`

```python
def finish(self, input_tokens: int, output_tokens: int, model: str,
           raw_response: str, parsed_output: str, parse_ok: bool = True,
           error_message: str = ""):
```

Mark the span as complete. Calculates latency and cost automatically.

| Parameter      | Type   | Default | Description                              |
|----------------|--------|---------|------------------------------------------|
| `input_tokens` | `int`  | —       | Input tokens consumed                    |
| `output_tokens`| `int`  | —       | Output tokens produced                   |
| `model`        | `str`  | —       | Model ID used                            |
| `raw_response` | `str`  | —       | Raw LLM response (truncated to 2000)     |
| `parsed_output`| `str`  | —       | Parsed JSON output (truncated to 2000)   |
| `parse_ok`     | `bool` | `True`  | Whether JSON parsing succeeded           |
| `error_message`| `str`  | `""`    | Error message (sets status to `"error"`) |

#### `AgentSpan.finish_timeout`

```python
def finish_timeout(self):
```

Mark the span as timed out. Sets `status="timeout"`, `parse_ok=False`.

```python
from src.observability.tracer import RunTracer

tracer = RunTracer(source="data.csv", mode="with_router")
span = tracer.start_span("cleaner", "claude-haiku-4-5-20251001")

# ... run the agent ...

span.finish(
    input_tokens=1200,
    output_tokens=300,
    model="claude-haiku-4-5-20251001",
    raw_response='{"issues_fixed": ["Removed duplicates"], ...}',
    parsed_output='{"issues_fixed": ["Removed duplicates"], ...}',
    parse_ok=True
)

print(f"Cost: £{span.cost_gbp:.5f}")
print(f"Latency: {span.latency_ms}ms")
print(f"Status: {span.status}")
```

---

### `RunTracer`

```python
class RunTracer:
    def __init__(self, source: str, mode: str):
```

Top-level tracer for a pipeline run. Creates a unique `run_id` and collects all `AgentSpan` instances.

| Parameter | Type  | Default | Description                   |
|-----------|-------|---------|-------------------------------|
| `source`  | `str` | —       | Filename or source identifier |
| `mode`    | `str` | —       | `"with_router"` or `"no_router"` |

#### `RunTracer.start_span`

```python
def start_span(self, agent_name: str, model: str,
               system_prompt: str = "", user_message: str = "") -> AgentSpan:
```

Create a new `AgentSpan` for an agent and append it to `self.spans`.

| Parameter        | Type   | Default | Description                      |
|------------------|--------|---------|----------------------------------|
| `agent_name`     | `str`  | —       | Agent name                       |
| `model`          | `str`  | —       | Model ID                         |
| `system_prompt`  | `str`  | `""`    | System prompt (truncated to 1000)|
| `user_message`   | `str`  | `""`    | User message (truncated to 500)  |

**Returns** `AgentSpan`

#### Read-only Properties

| Property              | Type    | Description                                    |
|-----------------------|---------|------------------------------------------------|
| `total_cost_gbp`      | `float` | Sum of all span costs in GBP                   |
| `total_latency_ms`    | `int`   | Total elapsed time since tracer creation        |
| `total_input_tokens`  | `int`   | Sum of input tokens across all spans            |
| `total_output_tokens` | `int`   | Sum of output tokens across all spans           |
| `parse_failures`      | `int`   | Count of spans where `parse_ok=False`           |
| `timeout_count`       | `int`   | Count of spans with `status="timeout"`          |
| `guardrail_events`    | `list`  | All guardrail events from all spans             |

```python
from src.observability.tracer import RunTracer

tracer = RunTracer(source="sales.csv", mode="with_router")

# Start spans for agents
span1 = tracer.start_span("cleaner", "claude-haiku-4-5-20251001")
span2 = tracer.start_span("validator", "claude-sonnet-4-6")

# ... agents run ...

span1.finish(1000, 300, "claude-haiku-4-5-20251001", "{}", "{}")
span2.finish(2000, 500, "claude-sonnet-4-6", "{}", "{}")

print(f"Run ID: {tracer.run_id}")
print(f"Total cost: £{tracer.total_cost_gbp:.5f}")
print(f"Total latency: {tracer.total_latency_ms}ms")
print(f"Parse failures: {tracer.parse_failures}")
print(f"Timeouts: {tracer.timeout_count}")
print(f"Spans: {len(tracer.spans)}")
```

---

## Guardrails (`src/observability/guardrails.py`)

### `GuardrailResult`

```python
@dataclass
class GuardrailResult:
    passed: bool
    action: Literal["continue", "warn", "stop", "skip"]
    reason: str
    severity: Literal["info", "warning", "critical"]
    guardrail_type: str
    value: float
    threshold: float
```

Result of a guardrail check.

| Field            | Type                                          | Description                            |
|------------------|-----------------------------------------------|----------------------------------------|
| `passed`         | `bool`                                        | `True` if check passed                 |
| `action`         | `Literal["continue", "warn", "stop", "skip"]` | Recommended action                     |
| `reason`         | `str`                                         | Human-readable explanation             |
| `severity`       | `Literal["info", "warning", "critical"]`      | Severity level                         |
| `guardrail_type` | `str`                                         | Type of check (e.g. `"budget_cap"`)    |
| `value`          | `float`                                       | Actual measured value                  |
| `threshold`      | `float`                                       | Configured threshold                   |

#### `GuardrailResult.as_event`

```python
def as_event(self, agent_name: str) -> dict:
```

Convert to a serialisable dict for storage.

```python
from src.observability.guardrails import GuardrailResult

result = GuardrailResult(
    passed=False,
    action="stop",
    reason="Budget cap reached: £0.52 >= £0.50",
    severity="critical",
    guardrail_type="budget_cap",
    value=0.52,
    threshold=0.50
)

event = result.as_event("cleaner")
print(event)
# {'agent': 'cleaner', 'type': 'budget_cap', 'value': 0.52, ...}
```

---

### `GuardrailEngine`

```python
class GuardrailEngine:
    def __init__(
        self,
        budget_cap_gbp: float = 0.50,
        agent_timeout_s: int = 30,
        min_completeness: float = 60.0,
        max_pii_rows: int = 0,
        max_parse_failures: int = 3,
        anomaly_score_warn: float = 9.0,
        enabled: bool = True,
    ):
```

Configurable guardrail engine. All thresholds are customisable.

| Parameter           | Type    | Default | Description                                |
|---------------------|---------|---------|--------------------------------------------|
| `budget_cap_gbp`    | `float` | `0.50`  | Max total cost in GBP before stopping      |
| `agent_timeout_s`   | `int`   | `30`    | Max seconds per agent                      |
| `min_completeness`  | `float` | `60.0`  | Min completeness score (%) before warning  |
| `max_pii_rows`      | `int`   | `0`     | Max PII rows before warning                |
| `max_parse_failures`| `int`   | `3`     | Max parse failures before stopping         |
| `anomaly_score_warn`| `float` | `9.0`   | Anomaly score threshold for warning        |
| `enabled`           | `bool`  | `True`  | Enable/disable all guardrails              |

#### `check_budget`

```python
def check_budget(self, spent_so_far_gbp: float) -> GuardrailResult:
```

Check if cumulative spend exceeds the budget cap. Warns at 80%, stops at 100%.

```python
from src.observability.guardrails import GuardrailEngine

engine = GuardrailEngine(budget_cap_gbp=0.50)

result = engine.check_budget(0.30)
print(result.action)   # "continue"
print(result.passed)   # True

result = engine.check_budget(0.45)
print(result.action)   # "warn"
print(result.reason)   # "Budget at 90% — £0.4500 of £0.50"

result = engine.check_budget(0.55)
print(result.action)   # "stop"
print(result.passed)   # False
```

#### `check_pii`

```python
def check_pii(self, pii_rows: int) -> GuardrailResult:
```

Warns if PII was detected and anonymised (always a warning, never stops).

```python
engine = GuardrailEngine(max_pii_rows=0)

result = engine.check_pii(0)
print(result.action)   # "continue"

result = engine.check_pii(5)
print(result.action)   # "warn"
print(result.reason)   # "PII detected in 5 rows — data was anonymised before LLM call"
```

#### `check_completeness`

```python
def check_completeness(self, score: float) -> GuardrailResult:
```

Warns if data completeness is below the minimum threshold.

```python
engine = GuardrailEngine(min_completeness=60.0)

result = engine.check_completeness(95.0)
print(result.action)   # "continue"

result = engine.check_completeness(45.0)
print(result.action)   # "warn"
```

#### `check_anomaly_score`

```python
def check_anomaly_score(self, score: float) -> GuardrailResult:
```

Warns if anomaly score meets or exceeds the threshold.

```python
engine = GuardrailEngine(anomaly_score_warn=9.0)

result = engine.check_anomaly_score(5.0)
print(result.action)   # "continue"

result = engine.check_anomaly_score(9.5)
print(result.action)   # "warn"
print(result.reason)   # "Anomaly score 9.5/10 — high risk data, recommend human review"
```

#### `check_parse_failures`

```python
def check_parse_failures(self, failure_count: int) -> GuardrailResult:
```

Stops the pipeline if too many agents fail to parse LLM responses.

```python
engine = GuardrailEngine(max_parse_failures=3)

result = engine.check_parse_failures(1)
print(result.action)   # "continue"

result = engine.check_parse_failures(3)
print(result.action)   # "stop"
print(result.passed)   # False
```

---

## Store (`src/observability/store.py`)

SQLite persistence layer for run data. Database file: `pipeline_runs.db`.

### `init_db`

```python
def init_db():
```

Create tables if they don't exist: `runs`, `agent_spans`, `guardrail_events`, `budget`. Called automatically by `save_run()`.

```python
from src.observability.store import init_db

init_db()  # Safe to call multiple times
```

---

### `save_run`

```python
def save_run(tracer: RunTracer, status: str = "complete"):
```

Persist a completed run and all its spans to SQLite.

| Parameter | Type         | Default    | Description             |
|-----------|--------------|------------|-------------------------|
| `tracer`  | `RunTracer`  | —          | Completed run tracer    |
| `status`  | `str`        | `"complete"`| Final run status       |

```python
from src.observability.tracer import RunTracer
from src.observability.store import save_run

tracer = RunTracer(source="data.csv", mode="no_router")
# ... run agents, finish spans ...
save_run(tracer, status="complete")
```

---

### `get_runs`

```python
def get_runs(limit: int = 50):
```

Retrieve recent runs ordered by timestamp (newest first).

| Parameter | Type  | Default | Description          |
|-----------|-------|---------|----------------------|
| `limit`   | `int` | `50`    | Max runs to return   |

**Returns** `list[dict]` — each dict has keys: `run_id`, `timestamp`, `source`, `mode`, `total_cost_gbp`, `total_latency_ms`, `total_input_tokens`, `total_output_tokens`, `agent_count`, `parse_failures`, `timeout_count`, `guardrail_events`, `status`.

```python
from src.observability.store import get_runs

runs = get_runs(limit=10)
for run in runs:
    print(f"{run['run_id']}  {run['source']:20s}  £{run['total_cost_gbp']:.5f}  {run['status']}")
```

---

### `get_spans`

```python
def get_spans(run_id: str):
```

Get all agent spans for a specific run.

| Parameter | Type  | Default | Description |
|-----------|-------|---------|-------------|
| `run_id`  | `str` | —       | Run ID      |

**Returns** `list[dict]` — each dict has keys: `id`, `run_id`, `agent_name`, `model`, `input_tokens`, `output_tokens`, `cost_gbp`, `latency_ms`, `status`, `parse_ok`, `system_prompt`, `user_message`, `raw_response`, `parsed_output`, `error_message`, `guardrails_fired`.

```python
from src.observability.store import get_spans

spans = get_spans("a1b2c3d4")
for span in spans:
    print(f"  {span['agent_name']:20s} {span['model']} {span['latency_ms']}ms")
```

---

### `get_guardrail_events`

```python
def get_guardrail_events(limit: int = 100):
```

Retrieve guardrail events across all runs.

| Parameter | Type  | Default | Description               |
|-----------|-------|---------|---------------------------|
| `limit`   | `int` | `100`   | Max events to return      |

**Returns** `list[dict]` — keys: `id`, `run_id`, `agent_name`, `guardrail_type`, `value`, `threshold`, `action`, `severity`, `timestamp`.

```python
from src.observability.store import get_guardrail_events

events = get_guardrail_events(limit=20)
for e in events:
    print(f"  {e['guardrail_type']:20s} {e['action']:8s} {e['severity']}")
```

---

### `get_budget`

```python
def get_budget():
```

Get cumulative budget stats.

**Returns** `dict` — `{"total_spent_gbp": float, "run_count": int}`

```python
from src.observability.store import get_budget

budget = get_budget()
print(f"Total spent: £{budget['total_spent_gbp']:.4f}")
print(f"Total runs: {budget['run_count']}")
```

---

### `get_agent_stats`

```python
def get_agent_stats():
```

Get aggregated stats per agent across all runs.

**Returns** `list[dict]` — keys: `agent_name`, `runs`, `avg_latency_ms`, `avg_cost_gbp`, `parse_failures`, `errors`, `timeouts`.

```python
from src.observability.store import get_agent_stats

stats = get_agent_stats()
for s in stats:
    print(f"  {s['agent_name']:20s} runs={s['runs']} avg={s['avg_latency_ms']:.0f}ms")
```

---

## Metrics (`src/observability/metrics.py`)

### `run_quality_score`

```python
def run_quality_score(run_id: str) -> float:
```

Calculate quality score for a run: `(parse_ok / total) * 100 - (timeouts * 15)`. Floor at 0.

| Parameter | Type  | Default | Description |
|-----------|-------|---------|-------------|
| `run_id`  | `str` | —       | Run ID      |

**Returns** `float` — score 0–100

```python
from src.observability.metrics import run_quality_score

score = run_quality_score("a1b2c3d4")
print(f"Quality: {score}%")
```

---

### `cost_trend`

```python
def cost_trend(limit: int = 20) -> list[dict]:
```

Return cost over time for the last N runs (oldest first).

| Parameter | Type  | Default | Description         |
|-----------|-------|---------|---------------------|
| `limit`   | `int` | `20`    | Number of runs      |

**Returns** `list[dict]` — keys: `run_id`, `timestamp`, `cost_gbp`, `mode`.

```python
from src.observability.metrics import cost_trend

trend = cost_trend(limit=10)
for t in trend:
    print(f"  {t['timestamp'][:10]}  £{t['cost_gbp']:.5f}  {t['mode']}")
```

---

### `agent_performance_table`

```python
def agent_performance_table() -> list[dict]:
```

Aggregated performance metrics per agent.

**Returns** `list[dict]` — keys: `agent`, `runs`, `avg_latency_s`, `avg_cost_gbp`, `parse_fail_pct`, `error_rate_pct`, `timeout_rate_pct`, `reliability_pct`.

```python
from src.observability.metrics import agent_performance_table

table = agent_performance_table()
for row in table:
    print(f"  {row['agent']:20s} reliability={row['reliability_pct']}%  avg={row['avg_latency_s']}s")
```

---

### `model_usage_breakdown`

```python
def model_usage_breakdown() -> dict:
```

Total cost split by Haiku vs Sonnet across all stored runs.

**Returns** `dict` — `{"haiku_gbp": float, "sonnet_gbp": float}`

```python
from src.observability.metrics import model_usage_breakdown

breakdown = model_usage_breakdown()
print(f"Haiku total:  £{breakdown['haiku_gbp']:.4f}")
print(f"Sonnet total: £{breakdown['sonnet_gbp']:.4f}")
```

---

### `summary_stats`

```python
def summary_stats() -> dict:
```

High-level summary of all stored runs.

**Returns** `dict` — keys: `total_runs`, `total_cost_gbp`, `avg_cost_gbp`, `avg_latency_s`, `success_rate_pct`.

```python
from src.observability.metrics import summary_stats

stats = summary_stats()
print(f"Total runs: {stats['total_runs']}")
print(f"Total cost: £{stats['total_cost_gbp']:.4f}")
print(f"Avg cost per run: £{stats['avg_cost_gbp']:.4f}")
print(f"Avg latency: {stats['avg_latency_s']}s")
print(f"Success rate: {stats['success_rate_pct']}%")
```

---

## Credits (`src/auth/credits.py`)

### `make_fingerprint`

```python
def make_fingerprint(ip: str, user_agent: str) -> str:
```

Create a SHA-256 fingerprint from IP + User-Agent, truncated to 20 hex chars.

| Parameter    | Type  | Default | Description        |
|--------------|-------|---------|--------------------|
| `ip`         | `str` | —       | Client IP address  |
| `user_agent` | `str` | —       | Client User-Agent  |

**Returns** `str` — 20-char hex fingerprint

```python
from src.auth.credits import make_fingerprint

fp = make_fingerprint("192.168.1.1", "Mozilla/5.0 ...")
print(fp)  # e.g. "a1b2c3d4e5f6a7b8c9d0"
```

---

### `get_anon_runs`

```python
def get_anon_runs(fingerprint: str) -> int:
```

Get the number of runs used by an anonymous visitor. Creates a record if first visit.

| Parameter     | Type  | Default | Description         |
|---------------|-------|---------|---------------------|
| `fingerprint` | `str` | —       | Visitor fingerprint |

**Returns** `int` — runs used so far

```python
from src.auth.credits import get_anon_runs, make_fingerprint

fp = make_fingerprint("1.2.3.4", "Mozilla/5.0")
used = get_anon_runs(fp)
print(f"Runs used: {used}")  # 0 on first visit
```

---

### `record_anon_run`

```python
def record_anon_run(fingerprint: str):
```

Increment the run counter for an anonymous visitor.

| Parameter     | Type  | Default | Description         |
|---------------|-------|---------|---------------------|
| `fingerprint` | `str` | —       | Visitor fingerprint |

```python
from src.auth.credits import get_anon_runs, record_anon_run, make_fingerprint

fp = make_fingerprint("1.2.3.4", "Mozilla/5.0")
record_anon_run(fp)
print(get_anon_runs(fp))  # 1
```

---

### `get_or_create_user`

```python
def get_or_create_user(username: str) -> dict:
```

Get or create a user record by GitHub username.

| Parameter  | Type  | Default | Description          |
|------------|-------|---------|----------------------|
| `username` | `str` | —       | GitHub username      |

**Returns** `dict` — keys: `github_username`, `runs_used`, `has_forked`, `has_starred`, `has_followed`, `using_byok`, `first_seen`, `last_seen`.

```python
from src.auth.credits import get_or_create_user

user = get_or_create_user("octocat")
print(f"User: {user['github_username']}")
print(f"Runs used: {user['runs_used']}")
```

---

### `refresh_github_status`

```python
def refresh_github_status(username: str) -> dict:
```

Check GitHub API for star/fork/follow status and update the database.

| Parameter  | Type  | Default | Description     |
|------------|-------|---------|-----------------|
| `username` | `str` | —       | GitHub username |

**Returns** `dict` — `{"has_forked": bool, "has_starred": bool, "has_followed": bool}`

```python
from src.auth.credits import refresh_github_status

status = refresh_github_status("octocat")
print(f"Starred: {status['has_starred']}")
print(f"Forked: {status['has_forked']}")
print(f"Followed: {status['has_followed']}")
```

---

### `get_credits`

```python
def get_credits(username: str) -> dict:
```

Calculate remaining free credits for a user.

| Parameter  | Type  | Default | Description     |
|------------|-------|---------|-----------------|
| `username` | `str` | —       | GitHub username |

**Returns** `dict` — keys: `runs_used`, `max_free_runs`, `remaining_free`, `can_run_free`, `needs_byok`, `using_byok`, `has_forked`, `has_starred`, `has_followed`, `lifetime`.

**Credit tiers:**
- Anonymous: 2 free runs
- Star: 2 + 3 = 5 free runs
- Fork + Follow: lifetime unlimited (9999)

```python
from src.auth.credits import get_credits

credits = get_credits("octocat")
print(f"Runs used: {credits['runs_used']}")
print(f"Max free: {credits['max_free_runs']}")
print(f"Remaining: {credits['remaining_free']}")
print(f"Can run free: {credits['can_run_free']}")
print(f"Lifetime access: {credits['lifetime']}")
```

---

### `record_run`

```python
def record_run(username: str):
```

Increment the run counter for a logged-in user.

| Parameter  | Type  | Default | Description     |
|------------|-------|---------|-----------------|
| `username` | `str` | —       | GitHub username |

```python
from src.auth.credits import record_run

record_run("octocat")
```

---

### `enable_byok`

```python
def enable_byok(username: str):
```

Enable BYOK (Bring Your Own Key) for a user. Sets `using_byok=1`.

| Parameter  | Type  | Default | Description     |
|------------|-------|---------|-----------------|
| `username` | `str` | —       | GitHub username |

```python
from src.auth.credits import enable_byok

enable_byok("octocat")
```

---

### `can_run`

```python
def can_run(username: str, byok_key: str = None) -> tuple[bool, str]:
```

Check if a user is allowed to run the pipeline.

| Parameter  | Type     | Default | Description                  |
|------------|----------|---------|------------------------------|
| `username` | `str`    | —       | GitHub username              |
| `byok_key` | `str`    | `None`  | API key if using BYOK        |

**Returns** `tuple[bool, str]` — `(allowed, reason)` where reason is `"free"`, `"byok"`, or `"no_credits"`.

```python
from src.auth.credits import can_run

allowed, reason = can_run("octocat")
print(f"Can run: {allowed}, reason: {reason}")

# With BYOK
allowed, reason = can_run("octocat", byok_key="sk-ant-...")
print(f"Can run: {allowed}, reason: {reason}")  # True, "byok"
```

---

## GitHub API (`src/auth/github_api.py`)

Unauthenticated GitHub API calls (rate-limited to 60 req/hr).

### `get_repo_stats`

```python
def get_repo_stats() -> dict:
```

Get star and fork counts for the repo.

**Returns** `dict` — `{"stars": int, "forks": int}`

```python
from src.auth.github_api import get_repo_stats

stats = get_repo_stats()
print(f"Stars: {stats['stars']}, Forks: {stats['forks']}")
```

---

### `has_starred`

```python
def has_starred(username: str) -> bool:
```

Check if a user has starred the repo.

| Parameter  | Type  | Default | Description     |
|------------|-------|---------|-----------------|
| `username` | `str` | —       | GitHub username |

**Returns** `bool`

```python
from src.auth.github_api import has_starred

print(has_starred("octocat"))  # True or False
```

---

### `has_forked`

```python
def has_forked(username: str) -> bool:
```

Check if a user has forked the repo.

| Parameter  | Type  | Default | Description     |
|------------|-------|---------|-----------------|
| `username` | `str` | —       | GitHub username |

**Returns** `bool`

```python
from src.auth.github_api import has_forked

print(has_forked("octocat"))
```

---

### `has_followed`

```python
def has_followed(username: str, target: str = "harshitboots") -> bool:
```

Check if a user follows the target account.

| Parameter  | Type  | Default         | Description          |
|------------|-------|-----------------|----------------------|
| `username` | `str` | —               | GitHub username      |
| `target`   | `str` | `"harshitboots"`| Account to check     |

**Returns** `bool`

```python
from src.auth.github_api import has_followed

print(has_followed("octocat"))
```

---

### `validate_username`

```python
def validate_username(username: str) -> bool:
```

Check if a GitHub username exists.

| Parameter  | Type  | Default | Description     |
|------------|-------|---------|-----------------|
| `username` | `str` | —       | GitHub username |

**Returns** `bool`

```python
from src.auth.github_api import validate_username

print(validate_username("octocat"))      # True
print(validate_username("nonexistent")) # False
```

---

## Report Generator (`src/report_generator.py`)

### `generate_pdf_report`

```python
def generate_pdf_report(cur: dict) -> bytes:
```

Generate a styled PDF report from PDF pipeline results. Returns raw PDF bytes.

**`cur` dict keys:**

| Key            | Type     | Description                                |
|----------------|----------|--------------------------------------------|
| `mode`         | `str`    | Pipeline mode (e.g. `"PDF Intelligence"`)  |
| `total_pages`  | `int`    | Number of pages in the source PDF          |
| `word_count`   | `int`    | Total word count                           |
| `models`       | `dict`   | Model IDs used per agent                   |
| `parser`       | object   | `ParserResult` with `document_type`, `language`, `document_quality`, `has_tables`, `has_numbers`, `key_topics`, `parsing_notes` |
| `entity`       | object   | `EntityResult` with `total_entities`, `people`, `organisations`, `locations`, `dates`, `amounts`, `emails` |
| `risk`         | object   | `RiskResult` with `risk_level`, `overall_risk_score`, `pii_detected`, `pii_types`, `compliance_risks`, `legal_risks`, `financial_risks`, `recommendations` |
| `action`       | object   | `ActionResult` with `total_actions`, `priority_actions`, `action_items`, `decisions_made`, `deadlines`, `follow_ups`, `owners` |
| `summary`      | object   | `SummaryResult` with `summary`, `key_stats`, `recommendations` |

**Returns** `bytes` — PDF file content

```python
from src.report_generator import generate_pdf_report

cur = {
    "mode": "PDF Intelligence",
    "total_pages": 12,
    "word_count": 4500,
    "models": {
        "parser": "claude-sonnet-4-6",
        "entity": "claude-sonnet-4-6",
        "risk": "claude-sonnet-4-6",
        "action": "claude-sonnet-4-6",
        "summary": "claude-sonnet-4-6",
    },
    "parser": parser_result,    # ParserResult instance
    "entity": entity_result,    # EntityResult instance
    "risk": risk_result,        # RiskResult instance
    "action": action_result,    # ActionResult instance
    "summary": summary_result,  # SummaryResult instance
}

pdf_bytes = generate_pdf_report(cur)

# Save to file
with open("report.pdf", "wb") as f:
    f.write(pdf_bytes)

print(f"Report: {len(pdf_bytes)} bytes")
```

---

## Complete Pipeline Example

End-to-end usage combining all APIs:

```python
from src.pipeline import run_pipeline
from src.observability.guardrails import GuardrailEngine
from src.observability.store import get_runs, get_spans, get_budget
from src.observability.metrics import summary_stats, agent_performance_table

# 1. Configure guardrails
guardrails = GuardrailEngine(
    budget_cap_gbp=0.25,
    min_completeness=70.0,
    max_parse_failures=2,
    anomaly_score_warn=8.5,
)

# 2. Run pipeline with routing enabled
result = run_pipeline(
    file_path="demo/sample_data.csv",
    routing_enabled=True,
    guardrails=guardrails,
)

# 3. Check result
print(f"\n=== Run {result.run_id} ===")
print(f"Status: {result.status}")
print(f"Quality: {result.quality_score}%")
print(f"Cost: £{result.total_cost_gbp:.5f}")
print(f"Latency: {result.total_latency_ms}ms")

# 4. Per-agent telemetry
for t in result.telemetry:
    status = "ok" if t.parse_ok else "FAIL"
    print(f"  {t.agent_name:20s} {t.model_label:8s} {t.latency_ms:>5}ms  £{t.cost_gbp:.5f}  {status}")

# 5. Query stored data
runs = get_runs(limit=5)
budget = get_budget()
stats = summary_stats()

print(f"\nTotal runs: {stats['total_runs']}")
print(f"Total spent: £{stats['total_cost_gbp']:.4f}")
print(f"Avg cost/run: £{stats['avg_cost_gbp']:.4f}")
print(f"Success rate: {stats['success_rate_pct']}%")

# 6. Agent performance
perf = agent_performance_table()
for p in perf:
    print(f"  {p['agent']:20s} reliability={p['reliability_pct']}%  avg={p['avg_latency_s']}s")
```
