import json
import os

from anthropic import Anthropic
from dotenv import load_dotenv

from src.cost_config import AGENT_MAX_TOKENS, MODELS
from src.models import SummariserResult

load_dotenv()

SYSTEM_PROMPT = """You are a data summarisation agent.
Your job is to produce a business-readable summary of CSV data with key statistics and actionable recommendations.
You must respond ONLY with valid JSON. No explanation, no markdown, no code fences.
JSON format:
{
    "summary": "one paragraph business-readable summary of the dataset",
    "key_stats": {
        "Total Rows": "15",
        "Categories": "4",
        "Date Range": "Jan 2024"
    },
    "recommendations": ["recommendation 1", "recommendation 2"]
}"""


def run(
    csv_preview: str,
    total_rows: int,
    context: str = "",
    model: str = None,
    span=None,
    api_key: str = None,
) -> SummariserResult:
    if model is None:
        model = MODELS["quality"]
    client = Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
    user_msg = f"Summarise this dataset ({total_rows} total rows).\n\nAgent findings:\n{context}"

    try:
        response = client.messages.create(
            model=model,
            max_tokens=AGENT_MAX_TOKENS["summariser"],
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
        result = SummariserResult(**data)
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
        fallback = SummariserResult(
            summary="Could not parse response", key_stats={}, recommendations=[]
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
