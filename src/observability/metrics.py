from src.observability.store import get_agent_stats, get_budget, get_runs, get_spans


def run_quality_score(run_id: str) -> float:
    spans = get_spans(run_id)
    if not spans:
        return 0.0
    total = len(spans)
    parse_ok = sum(1 for s in spans if s["parse_ok"])
    timeouts = sum(1 for s in spans if s["status"] == "timeout")
    errors = sum(1 for s in spans if s["status"] == "error")
    score = (parse_ok / total) * 100
    score -= timeouts * 15
    score -= errors * 10
    return max(0.0, round(score, 1))


def cost_trend(limit: int = 20) -> list[dict]:
    runs = get_runs(limit)
    return [
        {
            "run_id": r["run_id"],
            "timestamp": r["timestamp"],
            "cost_gbp": r["total_cost_gbp"],
            "mode": r["mode"],
        }
        for r in reversed(runs)
    ]


def agent_performance_table() -> list[dict]:
    stats = get_agent_stats()
    result = []
    for s in stats:
        runs = s["runs"] or 1
        result.append(
            {
                "agent": s["agent_name"],
                "runs": runs,
                "avg_latency_s": round((s["avg_latency_ms"] or 0) / 1000, 2),
                "avg_cost_gbp": round(s["avg_cost_gbp"] or 0, 5),
                "parse_fail_pct": round((s["parse_failures"] or 0) / runs * 100, 1),
                "error_rate_pct": round((s["errors"] or 0) / runs * 100, 1),
                "timeout_rate_pct": round((s["timeouts"] or 0) / runs * 100, 1),
                "reliability_pct": round(
                    max(
                        0,
                        100 - ((s["errors"] or 0) + (s["timeouts"] or 0)) / runs * 100,
                    ),
                    1,
                ),
            }
        )
    return result


def model_usage_breakdown() -> dict:
    runs = get_runs(200)
    haiku_cost = 0.0
    sonnet_cost = 0.0
    for r in runs:
        spans = get_spans(r["run_id"])
        for s in spans:
            if "haiku" in s["model"].lower():
                haiku_cost += s["cost_gbp"]
            else:
                sonnet_cost += s["cost_gbp"]
    return {"haiku_gbp": round(haiku_cost, 4), "sonnet_gbp": round(sonnet_cost, 4)}


def summary_stats() -> dict:
    budget = get_budget()
    runs = get_runs(200)
    if not runs:
        return {
            "total_runs": 0,
            "total_cost_gbp": 0,
            "avg_cost_gbp": 0,
            "avg_latency_s": 0,
            "success_rate_pct": 100,
        }
    costs = [r["total_cost_gbp"] for r in runs]
    latencies = [r["total_latency_ms"] for r in runs]
    successes = sum(1 for r in runs if r["status"] == "complete")
    return {
        "total_runs": budget["run_count"],
        "total_cost_gbp": round(budget["total_spent_gbp"], 4),
        "avg_cost_gbp": round(sum(costs) / len(costs), 4),
        "avg_latency_s": round(sum(latencies) / len(latencies) / 1000, 2),
        "success_rate_pct": round(successes / len(runs) * 100, 1),
    }
