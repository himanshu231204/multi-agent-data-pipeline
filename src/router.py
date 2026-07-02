from dataclasses import dataclass

from src.cost_config import MODELS

SIMPLE_AGENTS = {"cleaner", "pii_anonymiser", "transformer"}
COMPLEX_AGENTS = {
    "validator",
    "anomaly",
    "summariser",
    "pdf_parser",
    "entity_extractor",
    "risk_detector",
    "action_extractor",
}

ROW_THRESHOLD = 500


@dataclass
class RouterDecision:
    agent_name: str
    model: str
    model_label: str
    reason: str
    routing_enabled: bool


def route(
    agent_name: str, total_rows: int = 0, routing_enabled: bool = True
) -> RouterDecision:
    if not routing_enabled:
        return RouterDecision(
            agent_name=agent_name,
            model=MODELS["quality"],
            model_label="Sonnet",
            reason="Router disabled — all agents use Sonnet",
            routing_enabled=False,
        )

    if agent_name in SIMPLE_AGENTS:
        model = MODELS["fast"]
        label = "Haiku"
        reason = "Simple mechanical task — Haiku sufficient, no reasoning required"
    elif agent_name in COMPLEX_AGENTS:
        model = MODELS["quality"]
        label = "Sonnet"
        reason = "Complex reasoning task — Sonnet required for quality"
    else:
        model = MODELS["quality"]
        label = "Sonnet"
        reason = "Unknown agent — defaulting to Sonnet"

    return RouterDecision(
        agent_name=agent_name,
        model=model,
        model_label=label,
        reason=reason,
        routing_enabled=True,
    )


def baseline_model() -> str:
    return MODELS["quality"]
