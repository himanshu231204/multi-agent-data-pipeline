import os
import json
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """You are an action item extraction agent.
Your job is to extract all action items, decisions, deadlines, and follow-ups from document text.
You must respond ONLY with valid JSON. No explanation, no markdown, no code fences.
JSON format:
{
    "action_items": ["action1", "action2"],
    "decisions_made": ["decision1", "decision2"],
    "deadlines": ["deadline1 - date", "deadline2 - date"],
    "follow_ups": ["follow up1", "follow up2"],
    "owners": ["person/team responsible1", "person/team responsible2"],
    "priority_actions": ["most urgent action1", "most urgent action2"],
    "total_actions": 8
}"""

class ActionExtractorResult:
    def __init__(self, **kwargs):
        self.action_items = kwargs.get("action_items", [])
        self.decisions_made = kwargs.get("decisions_made", [])
        self.deadlines = kwargs.get("deadlines", [])
        self.follow_ups = kwargs.get("follow_ups", [])
        self.owners = kwargs.get("owners", [])
        self.priority_actions = kwargs.get("priority_actions", [])
        self.total_actions = kwargs.get("total_actions", 0)

    def model_dump(self):
        return self.__dict__

def run(text_preview: str, total_pages: int, model: str = "claude-sonnet-4-6", api_key: str = None, span=None) -> ActionExtractorResult:
    print(f"[Action Extractor Agent] Starting... model={model}")
    _client = Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
    user_msg = f"Extract all action items from this document ({total_pages} pages):\n\n{text_preview}"
    response = _client.messages.create(
        model=model,
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}]
    )

    raw = response.content[0].text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        data = json.loads(raw)
        result = ActionExtractorResult(**data)
        if span:
            span.finish(input_tokens=response.usage.input_tokens,
                        output_tokens=response.usage.output_tokens,
                        model=model, raw_response=raw,
                        parsed_output=str(result.model_dump()), parse_ok=True)
        print(f"[Action Extractor Agent] Done — {result.total_actions} actions found")
        return result
    except Exception as e:
        if span:
            span.finish(input_tokens=getattr(response.usage, 'input_tokens', 0),
                        output_tokens=getattr(response.usage, 'output_tokens', 0),
                        model=model, raw_response=raw,
                        parsed_output="", parse_ok=False, error_message=str(e))
        return ActionExtractorResult(action_items=["Could not parse response"], total_actions=0)
