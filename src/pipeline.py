import os
import asyncio
import concurrent.futures
import json
import pandas as pd
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel

from src.models import PipelineResult, AgentTelemetry, RouterDecisionModel
from src.agents import cleaner, validator, transformer, anomaly, summariser, pii_anonymiser
from src.router import route
from src.cost_config import AGENT_TIMEOUTS
from src.observability.tracer import RunTracer
from src.observability.guardrails import GuardrailEngine, DEFAULT_GUARDRAILS
from src.observability.store import save_run

console = Console()


def load_csv(file_path: str) -> tuple[pd.DataFrame, str, int]:
    df = pd.read_csv(file_path)
    total_rows = len(df)
    preview = df.head(20).to_csv(index=False)
    return df, preview, total_rows


def _run_agent_with_timeout(agent_fn, args: dict, timeout_s: int, span):
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        future = ex.submit(agent_fn, **args)
        try:
            return future.result(timeout=timeout_s)
        except concurrent.futures.TimeoutError:
            span.finish_timeout()
            return None


def run_pipeline(file_path: str, routing_enabled: bool = False,
                 guardrails: GuardrailEngine = None,
                 api_key: str = None) -> PipelineResult:

    if api_key:
        os.environ["ANTHROPIC_API_KEY"] = api_key

    if guardrails is None:
        guardrails = DEFAULT_GUARDRAILS

    file_name = os.path.basename(file_path)
    mode = "with_router" if routing_enabled else "no_router"
    tracer = RunTracer(source=file_name, mode=mode)

    console.print(Panel.fit(
        f"[bold green]MULTI-AGENT DATA PIPELINE[/bold green]\n"
        f"[dim]Processing: {file_name} | Mode: {mode}[/dim]",
        border_style="green"
    ))

    df, preview, total_rows = load_csv(file_path)
    console.print(f"\n[cyan]Loaded {total_rows} rows — running in {'ROUTER' if routing_enabled else 'BASELINE'} mode[/cyan]\n")

    routing_decisions = []

    def get_model(agent_name: str) -> str:
        decision = route(agent_name, total_rows, routing_enabled)
        routing_decisions.append(RouterDecisionModel(
            agent_name=decision.agent_name,
            model=decision.model,
            model_label=decision.model_label,
            reason=decision.reason,
            routing_enabled=decision.routing_enabled,
        ))
        return decision.model

    # --- WAVE 1: parallel execution ---
    wave1_agents = {
        "cleaner":       (cleaner.run,       {"csv_preview": preview, "total_rows": total_rows}),
        "pii_anonymiser":(pii_anonymiser.run, {"csv_preview": preview, "total_rows": total_rows}),
        "validator":     (validator.run,      {"csv_preview": preview, "total_rows": total_rows}),
        "transformer":   (transformer.run,    {"csv_preview": preview, "total_rows": total_rows}),
        "anomaly":       (anomaly.run,        {"csv_preview": preview, "total_rows": total_rows}),
    }

    spans = {name: tracer.start_span(name, get_model(name)) for name in wave1_agents}

    console.print("[bold]Wave 1 — running 5 agents in parallel...[/bold]")

    wave1_results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            name: executor.submit(
                fn, **{**args, "model": spans[name].model, "span": spans[name]}
            )
            for name, (fn, args) in wave1_agents.items()
        }
        for name, future in futures.items():
            timeout_s = AGENT_TIMEOUTS.get(name, 20)
            try:
                wave1_results[name] = future.result(timeout=timeout_s)
            except concurrent.futures.TimeoutError:
                spans[name].finish_timeout()
                wave1_results[name] = None
                console.print(f"[red]  {name} timed out — fallback used[/red]")
            except Exception as e:
                spans[name].finish(0, 0, spans[name].model, "", "", False, str(e))
                wave1_results[name] = None

    for name in wave1_agents:
        status = spans[name].status
        cost = spans[name].cost_gbp
        latency = spans[name].latency_ms
        console.print(f"  [green]v[/green] {name:20s} {latency}ms  GBP{cost:.5f}  {spans[name].model.split('-')[1]}")

    # guardrail: budget check after wave 1
    budget_check = guardrails.check_budget(tracer.total_cost_gbp)
    if not budget_check.passed:
        console.print(f"[red bold]GUARDRAIL STOP: {budget_check.reason}[/red bold]")
        _finalise_guardrail_events(spans, budget_check)
        return _build_result(file_name, total_rows, wave1_results, None, tracer,
                             routing_decisions, mode, guardrails, "stopped_budget")

    # guardrail: PII check
    if wave1_results.get("pii_anonymiser"):
        pii_check = guardrails.check_pii(wave1_results["pii_anonymiser"].rows_affected)
        if pii_check.action in ("warn", "stop"):
            console.print(f"[yellow]GUARDRAIL: {pii_check.reason}[/yellow]")
            spans["pii_anonymiser"].guardrails_fired.append(pii_check.as_event("pii_anonymiser"))

    # guardrail: parse failures
    parse_fail_check = guardrails.check_parse_failures(tracer.parse_failures)
    if not parse_fail_check.passed:
        console.print(f"[red bold]GUARDRAIL STOP: {parse_fail_check.reason}[/red bold]")
        return _build_result(file_name, total_rows, wave1_results, None, tracer,
                             routing_decisions, mode, guardrails, "stopped_parse_failures")

    # --- WAVE 2: summariser (needs context from wave 1) ---
    context = _build_context(wave1_results)
    sum_model = get_model("summariser")
    sum_span = tracer.start_span("summariser", sum_model)

    console.print("\n[bold]Wave 2 — Summariser...[/bold]")
    sum_result = summariser.run(
        csv_preview=preview, total_rows=total_rows,
        context=context, model=sum_model, span=sum_span
    )
    console.print(f"  [green]v[/green] summariser           {sum_span.latency_ms}ms  GBP{sum_span.cost_gbp:.5f}")

    # guardrail: anomaly score
    if wave1_results.get("anomaly"):
        anom_check = guardrails.check_anomaly_score(wave1_results["anomaly"].anomaly_score)
        if anom_check.action == "warn":
            console.print(f"[yellow]GUARDRAIL: {anom_check.reason}[/yellow]")
            spans["anomaly"].guardrails_fired.append(anom_check.as_event("anomaly"))

    result = _build_result(file_name, total_rows, wave1_results, sum_result, tracer,
                           routing_decisions, mode, guardrails, "complete")
    save_run(tracer, status="complete")
    _print_summary(result)
    return result


def _build_context(wave1_results: dict) -> str:
    parts = []
    if wave1_results.get("cleaner"):
        r = wave1_results["cleaner"]
        parts.append(f"Cleaner: {len(r.issues_fixed)} issues fixed, {r.rows_affected} rows affected.")
    if wave1_results.get("pii_anonymiser"):
        r = wave1_results["pii_anonymiser"]
        parts.append(f"PII: {r.rows_affected} rows had PII ({', '.join(r.pii_types_detected) or 'none'}).")
    if wave1_results.get("validator"):
        r = wave1_results["validator"]
        parts.append(f"Validator: {r.completeness_score}% completeness, {len(r.violations)} violations.")
    if wave1_results.get("transformer"):
        r = wave1_results["transformer"]
        parts.append(f"Transformer: {r.rows_transformed} rows transformed, {len(r.new_columns)} new columns.")
    if wave1_results.get("anomaly"):
        r = wave1_results["anomaly"]
        parts.append(f"Anomaly: {r.anomaly_count} anomalies, risk score {r.anomaly_score}/10.")
    return "\n".join(parts)


def _build_result(file_name, total_rows, wave1, sum_result, tracer,
                  routing_decisions, mode, guardrails, status) -> PipelineResult:
    telemetry = []
    for span in tracer.spans:
        rd = next((r for r in routing_decisions if r.agent_name == span.agent_name), None)
        telemetry.append(AgentTelemetry(
            agent_name=span.agent_name,
            model=span.model,
            model_label=rd.model_label if rd else "Sonnet",
            input_tokens=span.input_tokens,
            output_tokens=span.output_tokens,
            cost_gbp=span.cost_gbp,
            latency_ms=span.latency_ms,
            status=span.status,
            parse_ok=span.parse_ok,
            error_message=span.error_message,
            guardrails_fired=span.guardrails_fired,
            routing_reason=rd.reason if rd else "",
        ))

    parse_ok_count = sum(1 for t in telemetry if t.parse_ok)
    quality = round(max(0, (parse_ok_count / max(len(telemetry), 1)) * 100
                        - tracer.timeout_count * 15), 1)

    return PipelineResult(
        file_name=file_name,
        total_rows=total_rows,
        cleaner=wave1.get("cleaner"),
        pii=wave1.get("pii_anonymiser"),
        validator=wave1.get("validator"),
        transformer=wave1.get("transformer"),
        anomaly=wave1.get("anomaly"),
        summariser=sum_result,
        status=status,
        run_id=tracer.run_id,
        mode=mode,
        telemetry=telemetry,
        routing_decisions=routing_decisions,
        total_cost_gbp=tracer.total_cost_gbp,
        total_latency_ms=tracer.total_latency_ms,
        guardrail_events=tracer.guardrail_events,
        quality_score=quality,
    )


def _finalise_guardrail_events(spans, check):
    for span in spans.values():
        span.guardrails_fired.append(check.as_event("pipeline"))


def _print_summary(result: PipelineResult):
    console.print("\n")
    table = Table(title="Pipeline Results", border_style="green")
    table.add_column("Agent", style="cyan")
    table.add_column("Model", style="yellow")
    table.add_column("Latency", style="white")
    table.add_column("Cost GBP", style="white")
    table.add_column("Status", style="white")

    for t in result.telemetry:
        table.add_row(
            t.agent_name, t.model_label,
            f"{t.latency_ms}ms",
            f"GBP{t.cost_gbp:.5f}",
            "ok" if t.parse_ok else "FAIL"
        )

    console.print(table)
    console.print(
        f"\n[bold green]Pipeline complete[/bold green] — "
        f"{result.total_rows} rows | "
        f"GBP{result.total_cost_gbp:.5f} | "
        f"{result.total_latency_ms}ms | "
        f"Quality: {result.quality_score}%\n"
    )
