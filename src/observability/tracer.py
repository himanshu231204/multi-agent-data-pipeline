import time
import uuid
from dataclasses import dataclass, field

from src.cost_config import compute_cost_gbp


@dataclass
class AgentSpan:
    run_id: str
    agent_name: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_gbp: float = 0.0
    latency_ms: int = 0
    status: str = "pending"
    parse_ok: bool = True
    system_prompt: str = ""
    user_message: str = ""
    raw_response: str = ""
    parsed_output: str = ""
    error_message: str = ""
    guardrails_fired: list = field(default_factory=list)
    started_at: float = field(default_factory=time.time)

    def finish(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str,
        raw_response: str,
        parsed_output: str,
        parse_ok: bool = True,
        error_message: str = "",
    ):
        self.latency_ms = int((time.time() - self.started_at) * 1000)
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.model = model
        self.cost_gbp = compute_cost_gbp(model, input_tokens, output_tokens)
        self.raw_response = raw_response[:2000]
        self.parsed_output = parsed_output[:2000]
        self.parse_ok = parse_ok
        self.error_message = error_message
        self.status = "error" if error_message else "complete"

    def finish_timeout(self):
        self.latency_ms = int((time.time() - self.started_at) * 1000)
        self.status = "timeout"
        self.parse_ok = False
        self.error_message = "Agent timed out — fallback result used"


class RunTracer:
    def __init__(self, source: str, mode: str):
        self.run_id = str(uuid.uuid4())[:8]
        self.source = source
        self.mode = mode
        self.spans: list[AgentSpan] = []
        self.started_at = time.time()

    def start_span(
        self,
        agent_name: str,
        model: str,
        system_prompt: str = "",
        user_message: str = "",
    ) -> AgentSpan:
        span = AgentSpan(
            run_id=self.run_id,
            agent_name=agent_name,
            model=model,
            system_prompt=system_prompt[:1000],
            user_message=user_message[:500],
        )
        self.spans.append(span)
        return span

    @property
    def total_cost_gbp(self) -> float:
        return sum(s.cost_gbp for s in self.spans)

    @property
    def total_latency_ms(self) -> int:
        return int((time.time() - self.started_at) * 1000)

    @property
    def total_input_tokens(self) -> int:
        return sum(s.input_tokens for s in self.spans)

    @property
    def total_output_tokens(self) -> int:
        return sum(s.output_tokens for s in self.spans)

    @property
    def parse_failures(self) -> int:
        return sum(1 for s in self.spans if not s.parse_ok)

    @property
    def timeout_count(self) -> int:
        return sum(1 for s in self.spans if s.status == "timeout")

    @property
    def guardrail_events(self) -> list:
        events = []
        for s in self.spans:
            for g in s.guardrails_fired:
                events.append(g)
        return events
