MODELS = {
    "fast": "claude-haiku-4-5-20251001",
    "quality": "claude-sonnet-4-6",
}

# USD per million tokens
PRICING = {
    "claude-haiku-4-5-20251001": {
        "input_per_m": 0.80,
        "output_per_m": 4.00,
    },
    "claude-sonnet-4-6": {
        "input_per_m": 3.00,
        "output_per_m": 15.00,
    },
}

GBP_PER_USD = 0.79

FREE_RUNS = 2
STAR_BONUS_RUNS = 3
LIFETIME_ACCESS_RUNS = 9999

MAX_INPUT_TOKENS = 8000

AGENT_MAX_TOKENS = {
    "cleaner": 400,
    "pii_anonymiser": 350,
    "validator": 600,
    "transformer": 400,
    "anomaly": 550,
    "summariser": 1000,
    "pdf_parser": 600,
    "entity_extractor": 700,
    "risk_detector": 600,
    "action_extractor": 600,
}

AGENT_TIMEOUTS = {
    "cleaner": 12,
    "pii_anonymiser": 10,
    "validator": 18,
    "transformer": 12,
    "anomaly": 18,
    "summariser": 20,
    "pdf_parser": 15,
    "entity_extractor": 15,
    "risk_detector": 15,
    "action_extractor": 15,
}


def compute_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    p = PRICING.get(model, PRICING["claude-sonnet-4-6"])
    return (input_tokens / 1_000_000 * p["input_per_m"]) + (
        output_tokens / 1_000_000 * p["output_per_m"]
    )


def compute_cost_gbp(model: str, input_tokens: int, output_tokens: int) -> float:
    return compute_cost_usd(model, input_tokens, output_tokens) * GBP_PER_USD
