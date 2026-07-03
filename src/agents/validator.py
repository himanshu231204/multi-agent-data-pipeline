import json
import os

from anthropic import Anthropic
from dotenv import load_dotenv

from src.cost_config import AGENT_MAX_TOKENS, MODELS
from src.models import ValidatorResult

load_dotenv()

SYSTEM_PROMPT = """You are a data validation agent.
Your job is to validate CSV data for schema correctness, data types, null values, and constraint violations.
You must respond ONLY with valid JSON. No explanation, no markdown, no code fences.
JSON format:
{
    "schema_ok": true,
    "violations": ["list of validation failures found"],
    "passed_checks": ["list of checks that passed"],
    "completeness_score": 95.5
}"""


def run(
    csv_preview: str, total_rows: int, model: str = None, span=None, api_key: str = None
) -> ValidatorResult:
    if model is None:
        model = MODELS["quality"]
    client = Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
    user_msg = f"Validate this CSV data ({total_rows} total rows):\n\n{csv_preview}"

    try:
        response = client.messages.create(
            model=model,
            max_tokens=AGENT_MAX_TOKENS["validator"],
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
        result = ValidatorResult(**data)
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
        fallback = ValidatorResult(
            schema_ok=False,
            violations=["Could not parse response"],
            passed_checks=[],
            completeness_score=0.0,
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
