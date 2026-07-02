import json
import os

from anthropic import Anthropic
from dotenv import load_dotenv

from src.cost_config import AGENT_MAX_TOKENS, MODELS
from src.models import CleanerResult

load_dotenv()


SYSTEM_PROMPT = """You are a data cleaning agent.
Your job is to analyse CSV data and identify all cleaning issues.
You must respond ONLY with valid JSON. No explanation, no markdown, no code fences.
JSON format:
{
    "issues_fixed": ["list of issues you found and fixed"],
    "rows_affected": 5,
    "cleaned_columns": ["col1", "col2"]
}"""


def run(
    csv_preview: str, total_rows: int, model: str = None, span=None
) -> CleanerResult:
    if model is None:
        model = MODELS["quality"]
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    user_msg = f"Clean this CSV data ({total_rows} total rows):\n\n{csv_preview}"

    try:
        response = client.messages.create(
            model=model,
            max_tokens=AGENT_MAX_TOKENS["cleaner"],
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
        result = CleanerResult(**data)
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
        fallback = CleanerResult(
            issues_fixed=["Could not parse response"],
            rows_affected=0,
            cleaned_columns=[],
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
