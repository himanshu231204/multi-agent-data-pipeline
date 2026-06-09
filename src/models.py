from pydantic import BaseModel
from typing import List, Optional

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

# ==========================================
# 1. NEW PII MODEL ADDED HERE
# ==========================================
class PIIAnonymiserResult(BaseModel):
    pii_found: List[str]
    rows_affected: int
    pii_types_detected: List[str]
    anonymised_preview: str

class PipelineResult(BaseModel):
    file_name: str
    total_rows: int
    cleaner: Optional[CleanerResult] = None
    validator: Optional[ValidatorResult] = None
    transformer: Optional[TransformerResult] = None
    anomaly: Optional[AnomalyResult] = None
    summariser: Optional[SummariserResult] = None
    # ==========================================
    # 2. INJECTED INTO FINAL PIPELINE PAYLOAD
    # ==========================================
    pii: Optional[PIIAnonymiserResult] = None 
    status: str = "complete"