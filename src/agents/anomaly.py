import json
import os

from anthropic import Anthropic
from dotenv import load_dotenv

from src.cost_config import AGENT_MAX_TOKENS, MODELS
from src.models import AnomalyResult

load_dotenv()

SYSTEM_PROMPT = """You are an anomaly detection agent.
Your job is to find statistical outliers, duplicate records, suspicious values, price anomalies, and impossible values in CSV data.
You must respond ONLY with valid JSON. No explanation, no markdown, no code fences.
JSON format:
{
    "anomalies": ["list of anomalies found with row numbers"],
    "anomaly_count": 2,
    "anomaly_score": 4.5,
    "flagged_rows": [7, 11]
}"""


def run(
    csv_preview: str, total_rows: int, model: str = None, span=None
) -> AnomalyResult:
    if model is None:
        model = MODELS["quality"]
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    user_msg = (
        f"Detect anomalies in this CSV data ({total_rows} total rows):\n\n{csv_preview}"
    )

    try:
        response = client.messages.create(
            model=model,
            max_tokens=AGENT_MAX_TOKENS["anomaly"],
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
        raw = (
            response.content[0]
            .text.strip()
            .removeprefix("```json")
            .removeprefix("```")
            .removesuffix("```")
            .strip()
        )
        data = json.loads(raw)
        result = AnomalyResult(**data)
        if span:
            span.finish(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                model=model,
                raw_response=raw,
                parsed_output=str(result.model_dump()),
                parse_ok=True,
            )
        return result
    except Exception as e:
        fallback = AnomalyResult(
            anomalies=["Could not parse response"],
            anomaly_count=0,
            anomaly_score=0.0,
            flagged_rows=[],
        )
        if span:
            span.finish(
                input_tokens=0,
                output_tokens=0,
                model=model,
                raw_response="",
                parsed_output="",
                parse_ok=False,
                error_message=str(e),
            )
        return fallback
