"""CSV Pipeline page — mode selector, upload, run, and comparison."""

import os
import tempfile

import streamlit as st
import pandas as pd

from src.pipeline import run_pipeline
from src.observability.guardrails import GuardrailEngine
from src.ui.auth import auth_section, check_can_run, record_run_anon_or_user, anon_credit_banner
from src.ui.helpers import display_result_tabs


def render(visitor_fp: str):
    st.markdown('<div class="section-pad">', unsafe_allow_html=True)

    # ── SECTION 1: PIPELINE MODE SELECTOR ──────────────────
    st.markdown('<div class="section-label">Choose Pipeline Mode</div>', unsafe_allow_html=True)

    routing_on = st.session_state.get("routing_on", False)

    col_b, col_r = st.columns(2)

    with col_b:
        baseline_active = "active-baseline" if not routing_on else ""
        baseline_tick = '<div class="selected-tick tick-baseline">&#10003;</div>' if not routing_on else ""
        html_b = (
            f'<div class="mode-card {baseline_active}">'
            f'{baseline_tick}'
            f'<div class="mode-card-badge badge-baseline">Baseline</div>'
            f'<div class="mode-card-title">&#9889; Without Router</div>'
            f'<div class="mode-card-sub">All 6 agents use Claude Sonnet &mdash; maximum accuracy, no shortcuts.</div>'
            f'<div class="mode-stats">'
            f'<span class="mode-stat stat-cost-high">~&pound;0.27 / run</span>'
            f'<span class="mode-stat stat-speed-slow">~14s</span>'
            f'<span class="mode-stat stat-model">All Sonnet</span>'
            f'</div></div>'
        )
        st.markdown(html_b, unsafe_allow_html=True)
        if st.button("Select: Without Router (Baseline)", use_container_width=True, key="sel_baseline"):
            st.session_state["routing_on"] = False
            st.rerun()

    with col_r:
        router_active = "active-router" if routing_on else ""
        router_tick = '<div class="selected-tick tick-router">&#10003;</div>' if routing_on else ""
        html_r = (
            f'<div class="mode-card {router_active}">'
            f'{router_tick}'
            f'<div class="mode-card-badge badge-router">Smart Router</div>'
            f'<div class="mode-card-title">&#128260; With Router</div>'
            f'<div class="mode-card-sub">Simple agents use Haiku (fast, cheap), complex agents use Sonnet (quality). 70% cheaper.</div>'
            f'<div class="mode-stats">'
            f'<span class="mode-stat stat-cost-low">~&pound;0.08 / run</span>'
            f'<span class="mode-stat stat-speed-fast">~5s</span>'
            f'<span class="mode-stat stat-model">Haiku + Sonnet</span>'
            f'</div></div>'
        )
        st.markdown(html_r, unsafe_allow_html=True)
        if st.button("Select: With Router (Save 70%)", use_container_width=True, key="sel_router"):
            st.session_state["routing_on"] = True
            st.rerun()

    routing_on = st.session_state.get("routing_on", False)
    mode_label = "WITH ROUTER" if routing_on else "WITHOUT ROUTER"

    st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)

    # ── SECTION 2: GITHUB ACCESS & CREDITS ─────────────────
    st.markdown('<div class="section-label">GitHub Access &amp; Free Credits</div>', unsafe_allow_html=True)
    active_user, byok_key, credits_info = auth_section("csv")

    # ── OBSERVABILITY DASHBOARD PROMO ──────────────────────
    st.markdown("""
<div class="dash-promo">
<div class="dash-promo-left">
<div class="dash-promo-title">📡 Observability Dashboard</div>
<div class="dash-promo-sub">Every pipeline run is automatically traced &mdash; costs, latency, agent prompts, raw responses and guardrail events are all logged in real time.</div>
<div class="dash-feature-pills">
<span class="dash-pill">&#128202; Live Monitor</span>
<span class="dash-pill">&#128202; Run History</span>
<span class="dash-pill">&#128178; Cost Analytics</span>
<span class="dash-pill">&#127919; Agent Performance</span>
<span class="dash-pill">&#128737; Guardrails Log</span>
<span class="dash-pill">&#9881; Settings</span>
</div>
</div>
</div>
""", unsafe_allow_html=True)
    st.page_link("pages/observability.py", label="Open Observability Dashboard", icon="📡")

    st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)

    # ── SECTION 4: UPLOAD & RUN ─────────────────────────────
    st.markdown('<div class="section-label">Upload Your Dataset</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Drop CSV here", type=["csv"], label_visibility="collapsed")
    use_demo = st.checkbox("Use demo dataset — retail transactions with intentional data quality issues")

    df = None
    if use_demo and os.path.exists("demo/sample_data.csv"):
        df = pd.read_csv("demo/sample_data.csv")
        st.success(f"Demo loaded — {len(df)} rows · {len(df.columns)} columns")
        st.dataframe(df, use_container_width=True, height=200)
    elif uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.success(f"Loaded — {len(df)} rows · {len(df.columns)} columns")
        st.dataframe(df, use_container_width=True, height=200)

    if not active_user:
        anon_credit_banner(visitor_fp)

    if df is not None:
        run_btn_label = f"▶ Run Pipeline — {mode_label}"
        if st.button(run_btn_label, use_container_width=True):
            run_ok, run_mode = check_can_run(active_user, byok_key, visitor_fp)
            if not run_ok:
                st.error("No free runs remaining. Enter your GitHub username above, add your API key, or fork the repo for lifetime access.")
            else:
                api_key_to_use = byok_key or None
                with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
                    df.to_csv(tmp.name, index=False)
                    tmp_path = tmp.name

                guardrail_cfg = st.session_state.get("guardrail_config", {})
                guardrails = GuardrailEngine(**guardrail_cfg) if guardrail_cfg else GuardrailEngine()

                with st.spinner(f"Running pipeline ({mode_label})..."):
                    result = run_pipeline(
                        tmp_path,
                        routing_enabled=routing_on,
                        guardrails=guardrails,
                        api_key=api_key_to_use,
                    )
                os.unlink(tmp_path)

                record_run_anon_or_user(active_user, run_mode, visitor_fp)

                # store result in session state keyed by mode
                if routing_on:
                    st.session_state["run_routed"] = result
                else:
                    st.session_state["run_baseline"] = result

                st.success(
                    f"Done — GBP {result.total_cost_gbp:.5f} · "
                    f"{result.total_latency_ms}ms · "
                    f"Quality: {result.quality_score}%"
                )
                display_result_tabs(result)

    # ── COMPARISON PANEL ────────────────────────────────────
    baseline_result = st.session_state.get("run_baseline")
    routed_result   = st.session_state.get("run_routed")

    if baseline_result or routed_result:
        st.markdown('<div style="height:32px;"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-label">Cost Dashboard</div>', unsafe_allow_html=True)

        # ── Both runs complete: redirect to dashboard ──────────
        if baseline_result and routed_result:
            st.markdown("""
<div class="compare-note">
<div class="compare-note-header">
<span style="font-size:26px;">&#9989;</span>
<span class="compare-note-title">Both runs complete &mdash; open the Dashboard to compare!</span>
</div>
<div class="compare-note-sub">
Both runs are saved. The Observability Dashboard shows the full side-by-side breakdown &mdash; exact agent traces, token counts, Haiku vs Sonnet cost savings, latency waterfall and any guardrail events.
</div>
<div class="dash-features-grid">
<div class="dash-feat-card"><div class="dash-feat-icon">&#128225;</div><div class="dash-feat-name">Live Monitor</div><div class="dash-feat-desc">Agent waterfall with latency bars. Inspect every prompt &amp; response.</div></div>
<div class="dash-feat-card"><div class="dash-feat-icon">&#128203;</div><div class="dash-feat-name">Run History</div><div class="dash-feat-desc">All past runs in SQLite. Drill into any run to see per-agent spans.</div></div>
<div class="dash-feat-card"><div class="dash-feat-icon">&#128178;</div><div class="dash-feat-name">Cost Analytics</div><div class="dash-feat-desc">Spend over time, Haiku vs Sonnet breakdown, cost by mode.</div></div>
<div class="dash-feat-card"><div class="dash-feat-icon">&#127919;</div><div class="dash-feat-name">Agent Performance</div><div class="dash-feat-desc">Reliability %, avg latency and parse failure rate per agent.</div></div>
<div class="dash-feat-card"><div class="dash-feat-icon">&#128737;</div><div class="dash-feat-name">Guardrails Log</div><div class="dash-feat-desc">Every guardrail event with severity, value vs threshold and action taken.</div></div>
<div class="dash-feat-card"><div class="dash-feat-icon">&#9881;</div><div class="dash-feat-name">Settings</div><div class="dash-feat-desc">Tune budget cap, timeouts, PII limits and parse failure thresholds live.</div></div>
</div>
</div>
""", unsafe_allow_html=True)
            st.page_link("pages/observability.py", label="Open Observability Dashboard — compare both runs →", icon="📡")

        # ── Only one run: prompt to run the other ──────────────
        else:
            missing = "WITH ROUTER" if baseline_result else "WITHOUT ROUTER"
            st.info(f"Run the pipeline **{missing}** to unlock the full dashboard comparison.")

    st.markdown('</div>', unsafe_allow_html=True)
