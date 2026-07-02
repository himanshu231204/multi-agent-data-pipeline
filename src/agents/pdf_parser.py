import json
import os

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are a document parsing agent.
Your job is to analyse extracted PDF text and identify document structure, metadata and content type.
You must respond ONLY with valid JSON. No explanation, no markdown, no code fences.
JSON format:
{
    "document_type": "invoice/contract/report/letter/other",
    "language": "English",
    "total_sections": 5,
    "has_tables": true,
    "has_numbers": true,
    "key_topics": ["topic1", "topic2", "topic3"],
    "document_quality": "good/fair/poor",
    "parsing_notes": ["note1", "note2"]
}"""


class PDFParserResult:
    def __init__(self, **kwargs):
        self.document_type = kwargs.get("document_type", "unknown")
        self.language = kwargs.get("language", "English")
        self.total_sections = kwargs.get("total_sections", 0)
        self.has_tables = kwargs.get("has_tables", False)
        self.has_numbers = kwargs.get("has_numbers", False)
        self.key_topics = kwargs.get("key_topics", [])
        self.document_quality = kwargs.get("document_quality", "unknown")
        self.parsing_notes = kwargs.get("parsing_notes", [])

    def model_dump(self):
        return self.__dict__


def run(
    text_preview: str,
    total_pages: int,
    model: str = "claude-haiku-4-5-20251001",
    api_key: str = None,
    span=None,
) -> PDFParserResult:
    print(f"[PDF Parser Agent] Starting... model={model}")
    import os

    _client = Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
    user_msg = f"Parse this PDF document ({total_pages} pages):\n\n{text_preview}"
    response = _client.messages.create(
        model=model,
        max_tokens=1000,
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

    try:
        data = json.loads(raw)
        result = PDFParserResult(**data)
        if span:
            span.finish(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                model=model,
                raw_response=raw,
                parsed_output=str(result.model_dump()),
                parse_ok=True,
            )
        print(f"[PDF Parser Agent] Done — {result.document_type}")
        return result
    except Exception as e:
        if span:
            span.finish(
                input_tokens=getattr(response.usage, "input_tokens", 0),
                output_tokens=getattr(response.usage, "output_tokens", 0),
                model=model,
                raw_response=raw,
                parsed_output="",
                parse_ok=False,
                error_message=str(e),
            )
        return PDFParserResult(
            document_type="unknown", parsing_notes=["Could not parse response"]
        )
