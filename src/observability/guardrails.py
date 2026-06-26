from dataclasses import dataclass
from typing import Literal


@dataclass
class GuardrailResult:
    passed: bool
    action: Literal["continue", "warn", "stop", "skip"]
    reason: str
    severity: Literal["info", "warning", "critical"]
    guardrail_type: str
    value: float
    threshold: float

    def as_event(self, agent_name: str) -> dict:
        return {
            "agent": agent_name,
            "type": self.guardrail_type,
            "value": self.value,
            "threshold": self.threshold,
            "action": self.action,
            "severity": self.severity,
            "reason": self.reason,
        }


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
        self.budget_cap_gbp = budget_cap_gbp
        self.agent_timeout_s = agent_timeout_s
        self.min_completeness = min_completeness
        self.max_pii_rows = max_pii_rows
        self.max_parse_failures = max_parse_failures
        self.anomaly_score_warn = anomaly_score_warn
        self.enabled = enabled

    def check_budget(self, spent_so_far_gbp: float) -> GuardrailResult:
        if not self.enabled:
            return self._pass("budget")
        pct = (spent_so_far_gbp / self.budget_cap_gbp) * 100 if self.budget_cap_gbp > 0 else 0
        if spent_so_far_gbp >= self.budget_cap_gbp:
            return GuardrailResult(
                passed=False, action="stop", severity="critical",
                reason=f"Budget cap reached: £{spent_so_far_gbp:.4f} >= £{self.budget_cap_gbp:.2f}",
                guardrail_type="budget_cap", value=spent_so_far_gbp, threshold=self.budget_cap_gbp,
            )
        if pct >= 80:
            return GuardrailResult(
                passed=True, action="warn", severity="warning",
                reason=f"Budget at {pct:.0f}% — £{spent_so_far_gbp:.4f} of £{self.budget_cap_gbp:.2f}",
                guardrail_type="budget_cap", value=spent_so_far_gbp, threshold=self.budget_cap_gbp,
            )
        return self._pass("budget_cap", value=spent_so_far_gbp, threshold=self.budget_cap_gbp)

    def check_pii(self, pii_rows: int) -> GuardrailResult:
        if not self.enabled:
            return self._pass("pii_rows")
        if pii_rows > self.max_pii_rows:
            return GuardrailResult(
                passed=True, action="warn", severity="warning",
                reason=f"PII detected in {pii_rows} rows — data was anonymised before LLM call",
                guardrail_type="pii_rows_detected", value=pii_rows, threshold=self.max_pii_rows,
            )
        return self._pass("pii_rows_detected", value=pii_rows, threshold=self.max_pii_rows)

    def check_completeness(self, score: float) -> GuardrailResult:
        if not self.enabled:
            return self._pass("completeness")
        if score < self.min_completeness:
            return GuardrailResult(
                passed=True, action="warn", severity="warning",
                reason=f"Completeness score {score:.1f}% below threshold {self.min_completeness:.0f}% — flag for review",
                guardrail_type="completeness_score", value=score, threshold=self.min_completeness,
            )
        return self._pass("completeness_score", value=score, threshold=self.min_completeness)

    def check_anomaly_score(self, score: float) -> GuardrailResult:
        if not self.enabled:
            return self._pass("anomaly_score")
        if score >= self.anomaly_score_warn:
            return GuardrailResult(
                passed=True, action="warn", severity="warning",
                reason=f"Anomaly score {score}/10 — high risk data, recommend human review",
                guardrail_type="anomaly_score", value=score, threshold=self.anomaly_score_warn,
            )
        return self._pass("anomaly_score", value=score, threshold=self.anomaly_score_warn)

    def check_parse_failures(self, failure_count: int) -> GuardrailResult:
        if not self.enabled:
            return self._pass("parse_failures")
        if failure_count >= self.max_parse_failures:
            return GuardrailResult(
                passed=False, action="stop", severity="critical",
                reason=f"{failure_count} parse failures in this run — pipeline reliability compromised",
                guardrail_type="parse_failure_streak", value=failure_count, threshold=self.max_parse_failures,
            )
        return self._pass("parse_failure_streak", value=failure_count, threshold=self.max_parse_failures)

    def _pass(self, guardrail_type: str, value: float = 0, threshold: float = 0) -> GuardrailResult:
        return GuardrailResult(
            passed=True, action="continue", severity="info",
            reason="Passed", guardrail_type=guardrail_type, value=value, threshold=threshold,
        )


DEFAULT_GUARDRAILS = GuardrailEngine()
