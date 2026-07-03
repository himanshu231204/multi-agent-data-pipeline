import json
import os

from anthropic import Anthropic
from dotenv import load_dotenv

from src.cost_config import AGENT_MAX_TOKENS, MODELS
from src.models import TransformerResult

load_dotenv()

SYSTEM_PROMPT = """You are a data transformation agent.
Your job is to suggest and apply transformations to CSV data.
This includes: standardising date formats, normalising text casing, deriving new columns, encoding categoricals.
You must respond ONLY with valid JSON. No explanation, no markdown, no code fences.
JSON format:
{
    "transformations_applied": ["list of transformations applied"],
    "new_columns": ["list of new columns derived"],
    "rows_transformed": 10
}"""


def run(
    csv_preview: str, total_rows: int, model: str = None, span=None, api_key: str = None
) -> TransformerResult:
    if model is None:
        model = MODELS["quality"]
    client = Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
    user_msg = f"Transform this CSV data ({total_rows} total rows):\n\n{csv_preview}"

    try:
        response = client.messages.create(
            model=model,
            max_tokens=AGENT_MAX_TOKENS["transformer"],
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
        result = TransformerResult(**data)
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
        fallback = TransformerResult(
            transformations_applied=["Could not parse response"],
            new_columns=[],
            rows_transformed=0,
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
