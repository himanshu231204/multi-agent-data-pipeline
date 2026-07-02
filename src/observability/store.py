import json
import os
import sqlite3
from datetime import datetime

from src.observability.tracer import RunTracer

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "pipeline_runs.db")


def _conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                timestamp TEXT,
                source TEXT,
                mode TEXT,
                total_cost_gbp REAL,
                total_latency_ms INTEGER,
                total_input_tokens INTEGER,
                total_output_tokens INTEGER,
                agent_count INTEGER,
                parse_failures INTEGER,
                timeout_count INTEGER,
                guardrail_events INTEGER,
                status TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS agent_spans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT,
                agent_name TEXT,
                model TEXT,
                input_tokens INTEGER,
                output_tokens INTEGER,
                cost_gbp REAL,
                latency_ms INTEGER,
                status TEXT,
                parse_ok INTEGER,
                system_prompt TEXT,
                user_message TEXT,
                raw_response TEXT,
                parsed_output TEXT,
                error_message TEXT,
                guardrails_fired TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS guardrail_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT,
                agent_name TEXT,
                guardrail_type TEXT,
                value TEXT,
                threshold TEXT,
                action TEXT,
                severity TEXT,
                timestamp TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS budget (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                total_spent_gbp REAL DEFAULT 0,
                run_count INTEGER DEFAULT 0,
                last_updated TEXT
            )
        """)
        c.execute(
            "INSERT OR IGNORE INTO budget (id, total_spent_gbp, run_count, last_updated) VALUES (1, 0, 0, ?)",
            (datetime.utcnow().isoformat(),),
        )


def save_run(tracer: RunTracer, status: str = "complete"):
    init_db()
    ts = datetime.utcnow().isoformat()
    with _conn() as c:
        c.execute(
            """
            INSERT OR REPLACE INTO runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
            (
                tracer.run_id,
                ts,
                tracer.source,
                tracer.mode,
                tracer.total_cost_gbp,
                tracer.total_latency_ms,
                tracer.total_input_tokens,
                tracer.total_output_tokens,
                len(tracer.spans),
                tracer.parse_failures,
                tracer.timeout_count,
                len(tracer.guardrail_events),
                status,
            ),
        )
        for span in tracer.spans:
            c.execute(
                """
                INSERT INTO agent_spans
                (run_id, agent_name, model, input_tokens, output_tokens, cost_gbp,
                 latency_ms, status, parse_ok, system_prompt, user_message,
                 raw_response, parsed_output, error_message, guardrails_fired)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
                (
                    span.run_id,
                    span.agent_name,
                    span.model,
                    span.input_tokens,
                    span.output_tokens,
                    span.cost_gbp,
                    span.latency_ms,
                    span.status,
                    int(span.parse_ok),
                    span.system_prompt,
                    span.user_message,
                    span.raw_response,
                    span.parsed_output,
                    span.error_message,
                    json.dumps(span.guardrails_fired),
                ),
            )
            for g in span.guardrails_fired:
                c.execute(
                    """
                    INSERT INTO guardrail_events
                    (run_id, agent_name, guardrail_type, value, threshold, action, severity, timestamp)
                    VALUES (?,?,?,?,?,?,?,?)
                """,
                    (
                        span.run_id,
                        span.agent_name,
                        g.get("type", ""),
                        str(g.get("value", "")),
                        str(g.get("threshold", "")),
                        g.get("action", ""),
                        g.get("severity", "info"),
                        ts,
                    ),
                )
        c.execute(
            """
            UPDATE budget SET
                total_spent_gbp = total_spent_gbp + ?,
                run_count = run_count + 1,
                last_updated = ?
            WHERE id = 1
        """,
            (tracer.total_cost_gbp, ts),
        )


def get_runs(limit: int = 50):
    init_db()
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM runs ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()
    cols = [
        "run_id",
        "timestamp",
        "source",
        "mode",
        "total_cost_gbp",
        "total_latency_ms",
        "total_input_tokens",
        "total_output_tokens",
        "agent_count",
        "parse_failures",
        "timeout_count",
        "guardrail_events",
        "status",
    ]
    return [dict(zip(cols, r, strict=False)) for r in rows]


def get_spans(run_id: str):
    init_db()
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM agent_spans WHERE run_id=? ORDER BY id", (run_id,)
        ).fetchall()
    cols = [
        "id",
        "run_id",
        "agent_name",
        "model",
        "input_tokens",
        "output_tokens",
        "cost_gbp",
        "latency_ms",
        "status",
        "parse_ok",
        "system_prompt",
        "user_message",
        "raw_response",
        "parsed_output",
        "error_message",
        "guardrails_fired",
    ]
    return [dict(zip(cols, r, strict=False)) for r in rows]


def get_guardrail_events(limit: int = 100):
    init_db()
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM guardrail_events ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    cols = [
        "id",
        "run_id",
        "agent_name",
        "guardrail_type",
        "value",
        "threshold",
        "action",
        "severity",
        "timestamp",
    ]
    return [dict(zip(cols, r, strict=False)) for r in rows]


def get_budget():
    init_db()
    with _conn() as c:
        row = c.execute(
            "SELECT total_spent_gbp, run_count FROM budget WHERE id=1"
        ).fetchone()
    return (
        {"total_spent_gbp": row[0], "run_count": row[1]}
        if row
        else {"total_spent_gbp": 0, "run_count": 0}
    )


def get_agent_stats():
    init_db()
    with _conn() as c:
        rows = c.execute("""
            SELECT agent_name,
                   COUNT(*) as runs,
                   AVG(latency_ms) as avg_latency_ms,
                   AVG(cost_gbp) as avg_cost_gbp,
                   SUM(CASE WHEN parse_ok=0 THEN 1 ELSE 0 END) as parse_failures,
                   SUM(CASE WHEN status='error' THEN 1 ELSE 0 END) as errors,
                   SUM(CASE WHEN status='timeout' THEN 1 ELSE 0 END) as timeouts
            FROM agent_spans GROUP BY agent_name
        """).fetchall()
    cols = [
        "agent_name",
        "runs",
        "avg_latency_ms",
        "avg_cost_gbp",
        "parse_failures",
        "errors",
        "timeouts",
    ]
    return [dict(zip(cols, r, strict=False)) for r in rows]
