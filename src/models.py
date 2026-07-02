from pydantic import BaseModel


class CleanerResult(BaseModel):
    issues_fixed: list[str]
    rows_affected: int
    cleaned_columns: list[str]


class ValidatorResult(BaseModel):
    schema_ok: bool
    violations: list[str]
    passed_checks: list[str]
    completeness_score: float


class TransformerResult(BaseModel):
    transformations_applied: list[str]
    new_columns: list[str]
    rows_transformed: int


class AnomalyResult(BaseModel):
    anomalies: list[str]
    anomaly_count: int
    anomaly_score: float
    flagged_rows: list[int]


class SummariserResult(BaseModel):
    summary: str
    key_stats: dict
    recommendations: list[str]


class PIIAnonymiserResult(BaseModel):
    pii_found: list[str]
    rows_affected: int
    pii_types_detected: list[str]
    anonymised_preview: str


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
    guardrails_fired: list[dict] = []
    routing_reason: str = ""


class RouterDecisionModel(BaseModel):
    agent_name: str
    model: str
    model_label: str
    reason: str
    routing_enabled: bool


class PipelineResult(BaseModel):
    file_name: str
    total_rows: int
    cleaner: CleanerResult | None = None
    pii: PIIAnonymiserResult | None = None
    validator: ValidatorResult | None = None
    transformer: TransformerResult | None = None
    anomaly: AnomalyResult | None = None
    summariser: SummariserResult | None = None
    status: str = "complete"
    run_id: str = ""
    mode: str = "no_router"
    telemetry: list[AgentTelemetry] = []
    routing_decisions: list[RouterDecisionModel] = []
    total_cost_gbp: float = 0.0
    total_latency_ms: int = 0
    guardrail_events: list[dict] = []
    quality_score: float = 100.0
