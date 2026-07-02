import pandas as pd
import streamlit as st

from src.observability.metrics import (
    agent_performance_table,
    cost_trend,
    model_usage_breakdown,
    run_quality_score,
    summary_stats,
)
from src.observability.store import (
    get_budget,
    get_guardrail_events,
    get_runs,
    get_spans,
    init_db,
)

st.set_page_config(
    page_title="Observability · Multi-Agent Pipeline",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
html, body, [class*="css"], .stApp { background-color: #060910 !important; color: #e2e8f0 !important; }
header[data-testid="stHeader"] { display: none !important; }
.block-container { padding: 24px 48px !important; max-width: 100% !important; }
div[data-testid="metric-container"] {
    background: #080c14 !important; border: 0.5px solid #0f1f35 !important;
    border-radius: 12px !important; padding: 16px !important;
}
div[data-testid="stMetricValue"] { color: #00ff88 !important; font-family: monospace !important; font-size: 28px !important; }
.stTabs [data-baseweb="tab"] { font-family: monospace !important; font-size: 11px !important; color: #94a3b8 !important; }
.stTabs [aria-selected="true"] { color: #38bdf8 !important; border-bottom: 2px solid #38bdf8 !important; }
</style>
""",
    unsafe_allow_html=True,
)

init_db()

# ── GUIDE STYLES ─────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&family=Space+Mono:wght@400;700&display=swap');
html, body, [class*="css"], .stApp { background: #f8fafc !important; color: #0f172a !important; font-family: 'Inter', sans-serif !important; }
header[data-testid="stHeader"] { display: none !important; }
.block-container { padding: 28px 40px !important; max-width: 100% !important; }
div[data-testid="metric-container"] {
    background: #ffffff !important; border: 1px solid #e2e8f0 !important;
    border-radius: 12px !important; padding: 16px !important;
}
div[data-testid="stMetricValue"] { color: #0ea5e9 !important; font-family: 'Space Mono', monospace !important; font-size: 26px !important; }
div[data-testid="stMetricLabel"] { color: #64748b !important; font-size: 11px !important; font-weight: 600 !important; }
.stTabs [data-baseweb="tab"] { font-family: 'Space Mono', monospace !important; font-size: 11px !important; color: #64748b !important; background: transparent !important; }
.stTabs [aria-selected="true"] { color: #0ea5e9 !important; border-bottom: 2px solid #0ea5e9 !important; }
.stTabs [data-baseweb="tab-list"] { background: #ffffff !important; border-bottom: 1px solid #e2e8f0 !important; border-radius: 10px 10px 0 0 !important; padding: 0 8px !important; }
.guide-banner {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    border-radius: 20px;
    padding: 32px 36px 28px;
    margin-bottom: 28px;
    position: relative;
    overflow: hidden;
}
.guide-banner::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 4px;
    background: linear-gradient(90deg, #0ea5e9, #7c3aed, #db2777);
}
.guide-banner-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 24px;
}
.guide-banner-title {
    font-size: 22px;
    font-weight: 900;
    color: #f8fafc;
    letter-spacing: -0.02em;
}
.guide-banner-sub {
    font-size: 13px;
    color: #94a3b8;
    margin-top: 4px;
}
.guide-back-btn {
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    color: #38bdf8;
    background: rgba(56,189,248,0.12);
    border: 1px solid rgba(56,189,248,0.25);
    border-radius: 8px;
    padding: 7px 14px;
    text-decoration: none;
    white-space: nowrap;
}
.guide-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 14px;
    margin-bottom: 20px;
}
.guide-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 14px;
    padding: 16px 18px;
}
.guide-card-head {
    display: flex;
    align-items: center;
    gap: 9px;
    margin-bottom: 10px;
}
.guide-card-icon { font-size: 18px; }
.guide-card-name { font-size: 13px; font-weight: 800; color: #f1f5f9; }
.guide-card-tab { font-family: 'Space Mono', monospace; font-size: 9px; font-weight: 700; padding: 2px 7px; border-radius: 6px; margin-left: auto; }
.tab-live    { background: rgba(56,189,248,0.15); color: #38bdf8; }
.tab-hist    { background: rgba(124,58,237,0.15); color: #a78bfa; }
.tab-cost    { background: rgba(16,185,129,0.15); color: #34d399; }
.tab-agent   { background: rgba(251,146,60,0.15); color: #fb923c; }
.tab-guard   { background: rgba(239,68,68,0.15);  color: #f87171; }
.tab-set     { background: rgba(148,163,184,0.15); color: #94a3b8; }
.guide-card ul { margin: 0; padding: 0 0 0 2px; list-style: none; }
.guide-card ul li {
    font-size: 11.5px;
    color: #94a3b8;
    line-height: 1.6;
    padding: 3px 0;
    padding-left: 14px;
    position: relative;
}
.guide-card ul li::before { content: '›'; position: absolute; left: 0; color: #475569; font-weight: 700; }
.guide-guardrails {
    background: rgba(239,68,68,0.06);
    border: 1px solid rgba(239,68,68,0.20);
    border-radius: 14px;
    padding: 16px 20px;
}
.guide-guardrails-title {
    font-size: 13px;
    font-weight: 800;
    color: #fca5a5;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.guardrail-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
}
.gr-item {
    background: rgba(0,0,0,0.20);
    border-radius: 10px;
    padding: 10px 12px;
    border: 1px solid rgba(239,68,68,0.15);
}
.gr-name  { font-size: 11px; font-weight: 700; color: #fca5a5; margin-bottom: 3px; }
.gr-desc  { font-size: 10.5px; color: #6b7280; line-height: 1.4; }
.gr-sev   { font-size: 9px; font-weight: 700; margin-top: 5px; font-family: 'Space Mono', monospace; }
.sev-warn { color: #fbbf24; }
.sev-err  { color: #f87171; }
</style>
""",
    unsafe_allow_html=True,
)

# ── HEADER + GUIDE BANNER ────────────────────────────────────────────────────
runs_count = len(get_runs(limit=100))

st.markdown(
    f"""
<div class="guide-banner">
<div class="guide-banner-top">
<div>
<div class="guide-banner-title">&#128225; Observability Dashboard</div>
<div class="guide-banner-sub">Real-time traces &mdash; cost analytics &mdash; agent performance &mdash; guardrails &mdash; every run logged to SQLite &nbsp;&#183;&nbsp; <strong style="color:#38bdf8;">{runs_count} run{"s" if runs_count != 1 else ""} recorded</strong></div>
</div>
<a href="/" target="_self" class="guide-back-btn">&#8592; Back to Pipeline</a>
</div>

<div class="guide-grid">
<div class="guide-card">
<div class="guide-card-head"><span class="guide-card-icon">&#128225;</span><span class="guide-card-name">Live Monitor</span><span class="guide-card-tab tab-live">TAB 1</span></div>
<ul>
<li>Shows agent waterfall for the <em>most recent</em> run</li>
<li>Latency bar per agent &mdash; spot slowest agent at a glance</li>
<li>Cost in GBP per agent span with model used</li>
<li>Agent Inspector: click any agent to read the exact prompt sent and raw model response</li>
<li>Quality score (0&ndash;100) computed from completeness + anomaly rate</li>
</ul>
</div>
<div class="guide-card">
<div class="guide-card-head"><span class="guide-card-icon">&#128203;</span><span class="guide-card-name">Run History</span><span class="guide-card-tab tab-hist">TAB 2</span></div>
<ul>
<li>Full table of every pipeline run stored in SQLite</li>
<li>Select any past run to inspect its individual agent spans</li>
<li>Columns: run ID, mode (baseline/router), total cost, latency, status</li>
<li>Drill into a run to see token counts, parse success, and exact model used</li>
<li>Useful to compare run quality over time or across modes</li>
</ul>
</div>
<div class="guide-card">
<div class="guide-card-head"><span class="guide-card-icon">&#128178;</span><span class="guide-card-name">Cost Analytics</span><span class="guide-card-tab tab-cost">TAB 3</span></div>
<ul>
<li>Total spend in GBP across all recorded runs</li>
<li>Haiku vs Sonnet token split &mdash; see router savings in numbers</li>
<li>Cost-per-run trend bar chart (spot regressions)</li>
<li>Router mode vs baseline mode average cost side-by-side</li>
<li>Model usage breakdown: input tokens vs output tokens per model</li>
</ul>
</div>
<div class="guide-card">
<div class="guide-card-head"><span class="guide-card-icon">&#127919;</span><span class="guide-card-name">Agent Performance</span><span class="guide-card-tab tab-agent">TAB 4</span></div>
<ul>
<li>Reliability % per agent (successful parses &divide; total runs)</li>
<li>Average latency per agent &mdash; identify bottlenecks</li>
<li>Parse failure rate &mdash; how often agent output failed to deserialise</li>
<li>Timeout rate &mdash; which agents are hitting the time limit</li>
<li>Helps decide whether to swap a Sonnet agent to Haiku or vice versa</li>
</ul>
</div>
<div class="guide-card">
<div class="guide-card-head"><span class="guide-card-icon">&#128737;</span><span class="guide-card-name">Guardrails Log</span><span class="guide-card-tab tab-guard">TAB 5</span></div>
<ul>
<li>Every guardrail event fired across all runs shown in a table</li>
<li>Columns: run ID, guardrail name, severity, value vs threshold, action taken</li>
<li>Severity levels: WARNING (logged only) and ERROR (run blocked)</li>
<li>4 active guardrails: Budget Cap, PII Density, Parse Failures, Agent Timeout</li>
<li>Use this to tune thresholds in the Settings tab</li>
</ul>
</div>
<div class="guide-card">
<div class="guide-card-head"><span class="guide-card-icon">&#9881;</span><span class="guide-card-name">Settings</span><span class="guide-card-tab tab-set">TAB 6</span></div>
<ul>
<li>Set max budget cap (GBP) &mdash; pipeline aborts if exceeded</li>
<li>Max allowed PII density (% of rows with PII) before raising an alert</li>
<li>Max parse failures before a run is marked as degraded</li>
<li>Per-agent timeout in seconds &mdash; prevents runaway LLM calls</li>
<li>Changes persist to SQLite immediately &mdash; no restart needed</li>
</ul>
</div>
</div>

<div class="guide-guardrails">
<div class="guide-guardrails-title">&#128737; How Guardrails Work</div>
<div class="guardrail-row">
<div class="gr-item">
<div class="gr-name">&#128176; Budget Cap</div>
<div class="gr-desc">Total GBP cost of a run is checked after every agent. If it breaches the cap the run is halted and remaining agents are skipped.</div>
<div class="gr-sev sev-err">SEVERITY: ERROR</div>
</div>
<div class="gr-item">
<div class="gr-name">&#128100; PII Density</div>
<div class="gr-desc">After the PII Anonymiser runs, the % of rows containing PII is checked. If above threshold an alert is raised and PII fields are double-masked.</div>
<div class="gr-sev sev-warn">SEVERITY: WARNING</div>
</div>
<div class="gr-item">
<div class="gr-name">&#10060; Parse Failures</div>
<div class="gr-desc">Each agent output is deserialised into a typed Pydantic model. If more than N agents fail to parse their response, the run is flagged as degraded.</div>
<div class="gr-sev sev-warn">SEVERITY: WARNING</div>
</div>
<div class="gr-item">
<div class="gr-name">&#9200; Agent Timeout</div>
<div class="gr-desc">Each agent has a per-agent timeout. If the LLM call exceeds it the agent is marked as timed-out and the pipeline continues with partial results.</div>
<div class="gr-sev sev-err">SEVERITY: ERROR</div>
</div>
</div>
</div>
</div>
""",
    unsafe_allow_html=True,
)

# ── TABS ─────────────────────────────────────────────────────────────────────
(
    tab_compare,
    tab_live,
    tab_history,
    tab_cost,
    tab_agents,
    tab_guardrails,
    tab_settings,
) = st.tabs(
    [
        "⚖️ Compare Runs",
        "📡 Live Monitor",
        "📋 Run History",
        "💰 Cost Analytics",
        "🎯 Agent Performance",
        "🛡️ Guardrails Log",
        "⚙️ Settings",
    ]
)

# ── TAB 0: COMPARE RUNS ──────────────────────────────────────────────────────
with tab_compare:
    all_runs = get_runs(limit=100)
    baseline_runs = [r for r in all_runs if r["mode"] == "baseline"]
    router_runs = [r for r in all_runs if r["mode"] == "router"]

    if not all_runs:
        st.info("No runs recorded yet. Run the pipeline from the main page first.")
    elif len(all_runs) == 1:
        r = all_runs[0]
        st.markdown(f"### Single run — {r['mode'].title()} mode")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Run ID", r["run_id"])
        c2.metric("Total Cost", f"GBP {r['total_cost_gbp']:.5f}")
        c3.metric("Latency", f"{r['total_latency_ms']}ms")
        c4.metric("Source", r["source"])
        c5.metric("Status", r["status"])
        spans = get_spans(r["run_id"])
        if spans:
            st.markdown("#### Agent breakdown")
            df_single = pd.DataFrame(
                [
                    {
                        "Agent": s["agent_name"],
                        "Model": s["model"].split("-")[1]
                        if "-" in s["model"]
                        else s["model"],
                        "Tokens In": s["input_tokens"],
                        "Tokens Out": s["output_tokens"],
                        "Cost (GBP)": f"{s['cost_gbp']:.5f}",
                        "Latency (ms)": s["latency_ms"],
                        "Parse OK": "✓" if s["parse_ok"] else "✗",
                    }
                    for s in spans
                ]
            )
            st.dataframe(df_single, use_container_width=True, hide_index=True)
        st.info(
            "Run the pipeline again with the **other mode** (Baseline ↔ Router) to unlock side-by-side comparison."
        )
    else:
        # pick the most recent baseline vs most recent router run
        b = baseline_runs[0] if baseline_runs else None
        r = router_runs[0] if router_runs else None

        if b and r:
            st.markdown("### ⚖️ Baseline vs Router — side-by-side")
            col_b, col_r = st.columns(2)
            for col, run, label, color in [
                (col_b, b, "Without Router (Baseline)", "#0ea5e9"),
                (col_r, r, "With Router", "#7c3aed"),
            ]:
                with col:
                    st.markdown(
                        f'<div style="border-top:4px solid {color};border-radius:12px 12px 0 0;'
                        f'background:#f8fafc;padding:14px 18px 6px;">'
                        f'<strong style="color:{color};font-size:14px;">{label}</strong></div>',
                        unsafe_allow_html=True,
                    )
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Cost (GBP)", f"{run['total_cost_gbp']:.5f}")
                    m2.metric("Latency", f"{run['total_latency_ms']}ms")
                    m3.metric("Source", run["source"])
                    spans = get_spans(run["run_id"])
                    if spans:
                        haiku_count = sum(1 for s in spans if "haiku" in s["model"])
                        sonnet_count = sum(1 for s in spans if "sonnet" in s["model"])
                        total_tokens = sum(
                            s["input_tokens"] + s["output_tokens"] for s in spans
                        )
                        st.markdown(
                            f"**Models:** {haiku_count}× Haiku · {sonnet_count}× Sonnet  "
                            f"**Tokens:** {total_tokens:,}  "
                            f"**Parse failures:** {run['parse_failures']}"
                        )
                        df_spans = pd.DataFrame(
                            [
                                {
                                    "Agent": s["agent_name"],
                                    "Model": "Haiku"
                                    if "haiku" in s["model"]
                                    else "Sonnet",
                                    "Cost": f"{s['cost_gbp']:.5f}",
                                    "ms": s["latency_ms"],
                                    "✓": "✓" if s["parse_ok"] else "✗",
                                }
                                for s in spans
                            ]
                        )
                        st.dataframe(
                            df_spans, use_container_width=True, hide_index=True
                        )

            # Savings summary
            if b["total_cost_gbp"] > 0:
                cost_saved = b["total_cost_gbp"] - r["total_cost_gbp"]
                cost_pct = cost_saved / b["total_cost_gbp"] * 100
                lat_saved = b["total_latency_ms"] - r["total_latency_ms"]
                lat_pct = (
                    lat_saved / b["total_latency_ms"] * 100
                    if b["total_latency_ms"] > 0
                    else 0
                )
                st.markdown("---")
                sc1, sc2, sc3 = st.columns(3)
                sc1.metric("Cost saved", f"GBP {cost_saved:.5f}", f"{cost_pct:.0f}%")
                sc2.metric("Latency saved", f"{lat_saved}ms", f"{lat_pct:.0f}%")
                sc3.metric(
                    "Parse failures delta",
                    f"{r['parse_failures'] - b['parse_failures']:+d}",
                )
        elif b:
            st.info(
                "Only **Baseline** runs found. Run the pipeline once **With Router** to unlock comparison."
            )
        else:
            st.info(
                "Only **Router** runs found. Run the pipeline once **Without Router** to unlock comparison."
            )

# ── TAB 1: LIVE MONITOR ──────────────────────────────────────────────────────
with tab_live:
    st.subheader("Last Run — Live Trace")
    runs = get_runs(limit=1)
    if not runs:
        st.info("No runs yet. Run the pipeline from the main page.")
    else:
        r = runs[0]
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Run ID", r["run_id"])
        c2.metric("Total Cost", f"GBP {r['total_cost_gbp']:.5f}")
        c3.metric("Latency", f"{r['total_latency_ms']}ms")
        c4.metric("Mode", r["mode"])
        c5.metric("Status", r["status"])

        spans = get_spans(r["run_id"])
        quality = run_quality_score(r["run_id"])
        st.markdown(f"**Quality score:** {quality}%")

        if spans:
            st.markdown("#### Agent Waterfall")
            max_lat = max(s["latency_ms"] for s in spans) or 1
            for s in spans:
                bar_frac = s["latency_ms"] / max_lat
                status_icon = "✓" if s["parse_ok"] else "✗"
                timeout_icon = " ⏱️ TIMEOUT" if s["status"] == "timeout" else ""
                model_short = (
                    s["model"].split("-")[1] if "-" in s["model"] else s["model"]
                )
                st.markdown(
                    f"`{status_icon}` **{s['agent_name']}**  "
                    f"`{s['latency_ms']}ms`  `GBP {s['cost_gbp']:.5f}`  "
                    f"`{model_short}`{timeout_icon}"
                )
                st.progress(bar_frac)

            st.markdown("#### Agent Inspector")
            agent_names = [s["agent_name"] for s in spans]
            selected = st.selectbox(
                "Select agent to inspect", agent_names, key="inspector_select"
            )
            span = next(s for s in spans if s["agent_name"] == selected)

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Model:** {span['model']}")
                st.markdown(
                    f"**Tokens in:** {span['input_tokens']}  **out:** {span['output_tokens']}"
                )
                st.markdown(f"**Cost:** GBP {span['cost_gbp']:.5f}")
                st.markdown(f"**Latency:** {span['latency_ms']}ms")
                st.markdown(f"**Parse ok:** {'Yes' if span['parse_ok'] else 'FAILED'}")
                if span["error_message"]:
                    st.error(f"Error: {span['error_message']}")
            with col2:
                if span["system_prompt"]:
                    with st.expander("System Prompt"):
                        st.text(span["system_prompt"])
                if span["raw_response"]:
                    with st.expander("Raw Response"):
                        st.text(span["raw_response"])
                if span["parsed_output"]:
                    with st.expander("Parsed Output"):
                        st.text(span["parsed_output"])

        guardrails_fired = r.get("guardrail_events", 0)
        if guardrails_fired:
            st.warning(f"{guardrails_fired} guardrail event(s) fired in this run")

    if st.button("Refresh", key="refresh_live"):
        st.rerun()

# ── TAB 2: RUN HISTORY ───────────────────────────────────────────────────────
with tab_history:
    st.subheader("All Runs")
    runs = get_runs(limit=100)
    if not runs:
        st.info("No runs yet.")
    else:
        df_runs = pd.DataFrame(runs)
        df_runs["quality"] = [run_quality_score(r["run_id"]) for r in runs]
        df_runs["cost_gbp"] = df_runs["total_cost_gbp"].map(lambda x: f"GBP {x:.5f}")
        df_runs["latency_s"] = (df_runs["total_latency_ms"] / 1000).map(
            lambda x: f"{x:.1f}s"
        )
        display_cols = [
            "run_id",
            "timestamp",
            "source",
            "mode",
            "cost_gbp",
            "latency_s",
            "parse_failures",
            "guardrail_events",
            "quality",
            "status",
        ]
        st.dataframe(df_runs[display_cols], use_container_width=True, hide_index=True)

        st.markdown("#### Inspect a run")
        run_ids = [r["run_id"] for r in runs]
        sel_run = st.selectbox("Select run", run_ids, key="history_select")
        if sel_run:
            spans = get_spans(sel_run)
            if spans:
                df_spans = pd.DataFrame(spans)
                df_spans["cost_gbp"] = df_spans["cost_gbp"].map(
                    lambda x: f"GBP {x:.5f}"
                )
                st.dataframe(
                    df_spans[
                        [
                            "agent_name",
                            "model",
                            "input_tokens",
                            "output_tokens",
                            "cost_gbp",
                            "latency_ms",
                            "status",
                            "parse_ok",
                        ]
                    ],
                    use_container_width=True,
                    hide_index=True,
                )

# ── TAB 3: COST ANALYTICS ────────────────────────────────────────────────────
with tab_cost:
    st.subheader("Cost Analytics")
    stats = summary_stats()
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Runs", stats["total_runs"])
    c2.metric("Total Spend", f"GBP {stats['total_cost_gbp']:.4f}")
    c3.metric("Avg Cost / Run", f"GBP {stats['avg_cost_gbp']:.4f}")
    c4.metric("Avg Latency", f"{stats['avg_latency_s']}s")
    c5.metric("Success Rate", f"{stats['success_rate_pct']}%")

    trend = cost_trend(limit=30)
    if trend:
        st.markdown("#### Cost per run over time")
        df_trend = pd.DataFrame(trend)
        st.line_chart(df_trend.set_index("timestamp")["cost_gbp"])

    model_breakdown = model_usage_breakdown()
    st.markdown("#### Model spend breakdown")
    col1, col2 = st.columns(2)
    col1.metric("Haiku total", f"GBP {model_breakdown['haiku_gbp']:.4f}")
    col2.metric("Sonnet total", f"GBP {model_breakdown['sonnet_gbp']:.4f}")
    total_model = model_breakdown["haiku_gbp"] + model_breakdown["sonnet_gbp"]
    if total_model > 0:
        haiku_pct = model_breakdown["haiku_gbp"] / total_model * 100
        st.markdown(
            f"Haiku: {haiku_pct:.0f}% of spend  |  Sonnet: {100 - haiku_pct:.0f}%"
        )

    runs = get_runs(200)
    if runs:
        st.markdown("#### Cost by mode (baseline vs routed)")
        df_mode = (
            pd.DataFrame(runs)
            .groupby("mode")["total_cost_gbp"]
            .agg(["sum", "mean", "count"])
        )
        df_mode.columns = ["Total GBP", "Avg GBP", "Runs"]
        st.dataframe(df_mode, use_container_width=True)

# ── TAB 4: AGENT PERFORMANCE ─────────────────────────────────────────────────
with tab_agents:
    st.subheader("Agent Performance (last 200 runs)")
    perf = agent_performance_table()
    if not perf:
        st.info("No data yet.")
    else:
        df_perf = pd.DataFrame(perf)
        df_perf.columns = [c.replace("_", " ").title() for c in df_perf.columns]
        st.dataframe(df_perf, use_container_width=True, hide_index=True)

        st.markdown("#### Reliability by agent")
        if "Agent" in df_perf.columns and "Reliability Pct" in df_perf.columns:
            st.bar_chart(df_perf.set_index("Agent")["Reliability Pct"])

        st.markdown("#### Avg latency by agent (seconds)")
        if "Avg Latency S" in df_perf.columns:
            st.bar_chart(df_perf.set_index("Agent")["Avg Latency S"])

# ── TAB 5: GUARDRAILS LOG ────────────────────────────────────────────────────
with tab_guardrails:
    st.subheader("Guardrails Event Log")
    events = get_guardrail_events(limit=200)
    if not events:
        st.success("No guardrail events yet.")
    else:
        for e in events:
            severity = e.get("severity", "info")
            icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(severity, "⚪")
            bg = {"critical": "#fef2f2", "warning": "#fffbeb", "info": "#f0f9ff"}.get(
                severity, "#f8fafc"
            )
            bdr = {"critical": "#ef4444", "warning": "#f59e0b", "info": "#38bdf8"}.get(
                severity, "#e2e8f0"
            )
            st.markdown(
                f'<div style="border-left:4px solid {bdr};padding:10px 14px;margin:6px 0;'
                f'background:{bg};border-radius:8px;font-size:12px;">'
                f"{icon} <b>{e['guardrail_type']}</b> &mdash; agent: {e['agent_name']} &mdash; "
                f"value: <code>{e['value']}</code> vs threshold: <code>{e['threshold']}</code> &mdash; action: <b>{e['action']}</b>"
                f'<br><span style="color:#94a3b8;font-size:10px;">{e["timestamp"]} &nbsp;·&nbsp; run {e["run_id"]}</span>'
                f"</div>",
                unsafe_allow_html=True,
            )

# ── TAB 6: SETTINGS ──────────────────────────────────────────────────────────
with tab_settings:
    st.subheader("Guardrail Settings")
    st.markdown("Configure thresholds — changes apply to the next pipeline run.")

    with st.form("guardrail_form"):
        c1, c2 = st.columns(2)
        with c1:
            budget_cap = st.number_input(
                "Budget cap per run (GBP)", value=0.50, step=0.05, min_value=0.01
            )
            agent_timeout = st.number_input(
                "Agent timeout (seconds)", value=30, step=5, min_value=5
            )
            min_completeness = st.number_input(
                "Min completeness score (%)", value=60.0, step=5.0
            )
        with c2:
            max_pii_rows = st.number_input(
                "Max PII rows (0 = warn always)", value=0, step=1
            )
            max_parse_failures = st.number_input(
                "Max parse failures before abort", value=3, step=1
            )
            anomaly_warn = st.number_input(
                "Anomaly score warn threshold (0-10)", value=9.0, step=0.5
            )

        guardrails_enabled = st.checkbox("Guardrails enabled", value=True)
        submitted = st.form_submit_button("Save settings")
        if submitted:
            st.session_state["guardrail_config"] = {
                "budget_cap_gbp": budget_cap,
                "agent_timeout_s": int(agent_timeout),
                "min_completeness": min_completeness,
                "max_pii_rows": int(max_pii_rows),
                "max_parse_failures": int(max_parse_failures),
                "anomaly_score_warn": anomaly_warn,
                "enabled": guardrails_enabled,
            }
            st.success("Settings saved — will apply to next run")

    st.markdown("---")
    budget = get_budget()
    st.markdown(
        f"**Global spend so far:** GBP {budget['total_spent_gbp']:.4f} across {budget['run_count']} runs"
    )
