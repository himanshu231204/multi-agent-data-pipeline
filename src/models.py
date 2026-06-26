from pydantic import BaseModel
from typing import List, Optional, Dict


class CleanerResult(BaseModel):
    issues_fixed: List[str]
    rows_affected: int
    cleaned_columns: List[str]


class ValidatorResult(BaseModel):
    schema_ok: bool
    violations: List[str]
    passed_checks: List[str]
    completeness_score: float


class TransformerResult(BaseModel):
    transformations_applied: List[str]
    new_columns: List[str]
    rows_transformed: int


class AnomalyResult(BaseModel):
    anomalies: List[str]
    anomaly_count: int
    anomaly_score: float
    flagged_rows: List[int]


class SummariserResult(BaseModel):
    summary: str
    key_stats: dict
    recommendations: List[str]


class PIIAnonymiserResult(BaseModel):
    pii_found: List[str]
    rows_affected: int
    pii_types_detected: List[str]
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
    guardrails_fired: List[dict] = []
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
