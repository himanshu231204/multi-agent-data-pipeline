"""PDF Intelligence page — mode selector, upload, sequential agent runs, and results."""

import io
import json
import os

import streamlit as st

from src.agents import summariser
from src.observability.store import save_run
from src.observability.tracer import RunTracer
from src.ui.auth import auth_section, check_can_run, record_run_anon_or_user, anon_credit_banner


def render(visitor_fp: str):
    st.markdown('<div class="section-pad">', unsafe_allow_html=True)

    # ── PDF MODE SELECTOR ────────────────────────────────────
    st.markdown('<div class="section-label">Select Run Mode</div>', unsafe_allow_html=True)

    if "pdf_routing_on" not in st.session_state:
        st.session_state["pdf_routing_on"] = False
    pdf_routing_on = st.session_state["pdf_routing_on"]

    col_pb, col_pr = st.columns(2)
    with col_pb:
        pb_active = "active-baseline" if not pdf_routing_on else ""
        pb_tick = '<div class="selected-tick tick-baseline">&#10003;</div>' if not pdf_routing_on else ""
        html_pb = (
            f'<div class="mode-card {pb_active}">'
            f'{pb_tick}'
            f'<div class="mode-card-badge badge-baseline">Baseline</div>'
            f'<div class="mode-card-title">Without Router</div>'
            f'<div class="mode-card-sub">All 5 PDF agents use Sonnet (quality). Full reasoning on every agent.</div>'
            f'<div class="mode-stats">'
            f'<div class="mode-stat"><span>5</span>Agents</div>'
            f'<div class="mode-stat"><span>Sonnet</span>All</div>'
            f'<div class="mode-stat"><span>Max</span>Quality</div>'
            f'</div></div>'
        )
        st.markdown(html_pb, unsafe_allow_html=True)
        if st.button("Select: Without Router (Baseline)", key="pdf_sel_baseline", use_container_width=True):
            st.session_state["pdf_routing_on"] = False
            st.rerun()

    with col_pr:
        pr_active = "active-router" if pdf_routing_on else ""
        pr_tick = '<div class="selected-tick tick-router">&#10003;</div>' if pdf_routing_on else ""
        html_pr = (
            f'<div class="mode-card {pr_active}">'
            f'{pr_tick}'
            f'<div class="mode-card-badge badge-router">Smart Router</div>'
            f'<div class="mode-card-title">With Router</div>'
            f'<div class="mode-card-sub">Parser &amp; Entity &#8594; Haiku. Risk, Actions &amp; Summary &#8594; Sonnet. ~60% cheaper.</div>'
            f'<div class="mode-stats">'
            f'<div class="mode-stat"><span>2</span>Haiku</div>'
            f'<div class="mode-stat"><span>3</span>Sonnet</div>'
            f'<div class="mode-stat"><span>~60%</span>Cheaper</div>'
            f'</div></div>'
        )
        st.markdown(html_pr, unsafe_allow_html=True)
        if st.button("Select: With Router", key="pdf_sel_router", use_container_width=True):
            st.session_state["pdf_routing_on"] = True
            st.rerun()

    st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)

    # ── PDF AUTH & CREDITS ───────────────────────────────────
    st.markdown('<div class="section-label">GitHub Access &amp; Free Credits</div>', unsafe_allow_html=True)
    pdf_active_user, pdf_byok_key, pdf_credits_info = auth_section("pdf")
    if not pdf_active_user:
        anon_credit_banner(visitor_fp)

    # ── PDF UPLOAD ───────────────────────────────────────────
    st.markdown('<div class="section-label">Upload a PDF document</div>', unsafe_allow_html=True)
    pdf_file = st.file_uploader("Drop PDF here", type=["pdf"], label_visibility="collapsed")
    use_demo_pdf = st.checkbox("Use demo PDF — Project Alpha Q1 2024 quarterly review report")
    if use_demo_pdf and os.path.exists("demo/sample_report.pdf"):
        with open("demo/sample_report.pdf", "rb") as f:
            pdf_file = io.BytesIO(f.read())
            pdf_file.name = "sample_report.pdf"
        st.success("Demo PDF loaded — Project Alpha Q1 2024 Report")

    # Determine run_key before pdf_file block so it's available for result display
    run_key = "run_pdf_routed" if pdf_routing_on else "run_pdf_baseline"

    if pdf_file:
        try:
            from pypdf import PdfReader
            from src.agents import pdf_parser, entity_extractor, risk_detector, action_extractor

            reader = PdfReader(io.BytesIO(pdf_file.read()))
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""

            total_pages = len(reader.pages)
            word_count = len(text.split())
            st.success(f"PDF loaded — {total_pages} pages · {word_count} words")

            with st.expander("Preview extracted text"):
                st.text(text[:2000] + "..." if len(text) > 2000 else text)

            # router assigns models
            SONNET = "claude-sonnet-4-6"
            HAIKU  = "claude-haiku-4-5-20251001"
            if pdf_routing_on:
                m_parser   = HAIKU
                m_entity   = HAIKU
                m_risk     = SONNET
                m_action   = SONNET
                m_summary  = SONNET
                mode_label = "With Router"
            else:
                m_parser = m_entity = m_risk = m_action = m_summary = SONNET
                mode_label = "Without Router (Baseline)"

            if st.button(f"▶ Run PDF Pipeline — {mode_label}", use_container_width=True, type="primary"):
                run_ok, run_mode = check_can_run(pdf_active_user, pdf_byok_key, visitor_fp)
                if not run_ok:
                    st.error("No free runs remaining. Enter your GitHub username above, add your API key, or fork the repo for lifetime access.")
                    st.stop()

                _api = pdf_byok_key or None
                preview  = text[:3000]
                progress = st.progress(0)
                tracer = RunTracer(source="pdf", mode="router" if pdf_routing_on else "baseline")

                with st.status(f"Agent 1/5 — PDF Parser ({m_parser.split('-')[1].title()})", expanded=False) as s:
                    sp1 = tracer.start_span("pdf_parser", m_parser)
                    parser_result = pdf_parser.run(preview, total_pages, model=m_parser, api_key=_api, span=sp1)
                    s.update(label="✅ Agent 1/5 — PDF Parser complete", state="complete")
                progress.progress(0.2)

                with st.status(f"Agent 2/5 — Entity Extractor ({m_entity.split('-')[1].title()})", expanded=False) as s:
                    sp2 = tracer.start_span("entity_extractor", m_entity)
                    entity_result = entity_extractor.run(preview, total_pages, model=m_entity, api_key=_api, span=sp2)
                    s.update(label="✅ Agent 2/5 — Entity Extractor complete", state="complete")
                progress.progress(0.4)

                with st.status(f"Agent 3/5 — Risk Detector ({m_risk.split('-')[1].title()})", expanded=False) as s:
                    sp3 = tracer.start_span("risk_detector", m_risk)
                    risk_result = risk_detector.run(preview, total_pages, model=m_risk, api_key=_api, span=sp3)
                    s.update(label="✅ Agent 3/5 — Risk Detector complete", state="complete")
                progress.progress(0.6)

                with st.status(f"Agent 4/5 — Action Extractor ({m_action.split('-')[1].title()})", expanded=False) as s:
                    sp4 = tracer.start_span("action_extractor", m_action)
                    action_result = action_extractor.run(preview, total_pages, model=m_action, api_key=_api, span=sp4)
                    s.update(label="✅ Agent 4/5 — Action Extractor complete", state="complete")
                progress.progress(0.8)

                ctx = (
                    f"Document type: {parser_result.document_type}. "
                    f"Entities: {entity_result.total_entities}. "
                    f"Risk level: {risk_result.risk_level}, score: {risk_result.overall_risk_score}/10. "
                    f"Actions: {action_result.total_actions}."
                )
                with st.status(f"Agent 5/5 — Summariser ({m_summary.split('-')[1].title()})", expanded=False) as s:
                    sp5 = tracer.start_span("summariser", m_summary)
                    summariser_result = summariser.run(preview, total_pages, ctx, model=m_summary, span=sp5)
                    s.update(label="✅ Agent 5/5 — Summariser complete", state="complete")
                progress.progress(1.0)

                save_run(tracer)
                record_run_anon_or_user(pdf_active_user, run_mode, visitor_fp)

                # store run snapshot for comparison
                st.session_state[run_key] = {
                    "mode": mode_label,
                    "total_pages": total_pages,
                    "word_count": word_count,
                    "entities": entity_result.total_entities,
                    "risk_level": risk_result.risk_level,
                    "risk_score": risk_result.overall_risk_score,
                    "actions": action_result.total_actions,
                    "insights": len(summariser_result.recommendations),
                    "models": {
                        "parser": m_parser, "entity": m_entity,
                        "risk": m_risk, "action": m_action, "summary": m_summary
                    },
                    "parser": parser_result, "entity": entity_result,
                    "risk": risk_result, "action": action_result,
                    "summary": summariser_result,
                }

        except Exception as e:
            st.error(f"Error reading PDF: {e}")

    # ── Show last run result — persists after navigating to dashboard ────────
    cur = st.session_state.get(run_key)
    if cur:
        st.markdown("---")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Pages", cur["total_pages"])
        c2.metric("Entities", cur["entities"])
        c3.metric("Risk Score", f"{cur['risk_score']}/10")
        c4.metric("Actions", cur["actions"])
        c5.metric("Insights", cur["insights"])

        tab1, tab2, tab3, tab4, tab5 = st.tabs(
            ["📄 Parser", "🔍 Entities", "⚠️ Risks", "✅ Actions", "📊 Summary"]
        )
        r_parser  = cur["parser"]
        r_entity  = cur["entity"]
        r_risk    = cur["risk"]
        r_action  = cur["action"]
        r_summary = cur["summary"]

        with tab1:
            st.markdown(f"**Document type:** {r_parser.document_type}")
            st.markdown(f"**Language:** {r_parser.language}  **Quality:** {r_parser.document_quality}")
            st.markdown(f"**Has tables:** {'✅' if r_parser.has_tables else '❌'}  **Has numbers:** {'✅' if r_parser.has_numbers else '❌'}")
            if r_parser.key_topics:
                st.markdown("**Key topics:** " + " · ".join(r_parser.key_topics))
            for n in (r_parser.parsing_notes or []):
                st.info(n)

        with tab2:
            col1, col2 = st.columns(2)
            with col1:
                for label, items in [("People", r_entity.people), ("Organisations", r_entity.organisations), ("Locations", r_entity.locations)]:
                    if items:
                        st.markdown(f"**{label}:**")
                        for x in items: st.markdown(f"- {x}")
            with col2:
                for label, items in [("Dates", r_entity.dates), ("Amounts", r_entity.amounts), ("Emails", r_entity.emails)]:
                    if items:
                        st.markdown(f"**{label}:**")
                        for x in items: st.markdown(f"- {x}")

        with tab3:
            st.markdown(f"**Risk level:** `{r_risk.risk_level.upper()}`  **Score:** {r_risk.overall_risk_score}/10  **PII:** {'⚠️ Yes' if r_risk.pii_detected else '✅ No'}")
            if r_risk.pii_types: st.warning(f"PII types: {', '.join(r_risk.pii_types)}")
            for label, items, fn in [("Compliance risks", r_risk.compliance_risks, st.error), ("Legal risks", r_risk.legal_risks, st.warning), ("Financial risks", r_risk.financial_risks, st.warning)]:
                if items:
                    st.markdown(f"**{label}:**")
                    for x in items: fn(x)
            if r_risk.recommendations:
                st.markdown("**Recommendations:**")
                for x in r_risk.recommendations: st.markdown(f"→ {x}")

        with tab4:
            if r_action.priority_actions:
                st.markdown("**Priority actions:**")
                for a in r_action.priority_actions: st.error(f"🔴 {a}")
            if r_action.action_items:
                st.markdown("**All actions:**")
                for a in r_action.action_items: st.markdown(f"- {a}")
            if r_action.decisions_made:
                st.markdown("**Decisions:**")
                for d in r_action.decisions_made: st.success(d)
            for label, items in [("Deadlines", r_action.deadlines), ("Owners", r_action.owners)]:
                if items:
                    st.markdown(f"**{label}:**")
                    for x in items: st.markdown(f"- {x}")

        with tab5:
            st.info(r_summary.summary)
            st.json(r_summary.key_stats)
            for x in r_summary.recommendations: st.markdown(f"→ {x}")

        safe_mode = cur["mode"].replace(" ", "_").replace("(", "").replace(")", "")
        try:
            from src.report_generator import generate_pdf_report
            pdf_bytes = generate_pdf_report(cur)
            st.download_button(
                label="⬇️ Download Full Analysis Report (PDF)",
                data=pdf_bytes,
                file_name=f"pdf_analysis_{safe_mode}.pdf",
                mime="application/pdf",
                use_container_width=True,
                type="primary",
            )
        except Exception as _pdf_err:
            st.warning(f"PDF generation failed: {_pdf_err} — falling back to JSON")
            full_results = {
                "mode": cur["mode"], "total_pages": cur["total_pages"],
                "word_count": cur["word_count"], "models_used": cur["models"],
                "parser": r_parser.model_dump(), "entities": r_entity.model_dump(),
                "risks": r_risk.model_dump(), "actions": r_action.model_dump(),
                "summary": r_summary.model_dump(),
            }
            st.download_button(
                label="⬇️ Download Full PDF Analysis (JSON fallback)",
                data=json.dumps(full_results, indent=2),
                file_name=f"pdf_analysis_{safe_mode}.json",
                mime="application/json", use_container_width=True
            )
        # single-run dashboard link
        st.page_link("pages/observability.py", label="View this run in Observability Dashboard →", icon="📡")

    # ── PDF COMPARISON REDIRECT ──────────────────────────────
    pdf_base = st.session_state.get("run_pdf_baseline")
    pdf_rout = st.session_state.get("run_pdf_routed")

    if pdf_base and pdf_rout:
        st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)
        st.markdown("""
<div class="compare-note">
<div class="compare-note-header">
<span style="font-size:24px;">&#9989;</span>
<span class="compare-note-title">Both PDF runs complete &mdash; compare in the Dashboard!</span>
</div>
<div class="compare-note-sub">
Both runs are saved to the Observability Dashboard. Open it to see the full side-by-side agent waterfall &mdash; exact tokens, latency per agent, Haiku vs Sonnet cost breakdown, and all guardrail events.
</div>
<div class="dash-features-grid">
<div class="dash-feat-card"><div class="dash-feat-icon">&#128225;</div><div class="dash-feat-name">Live Monitor</div><div class="dash-feat-desc">Agent waterfall with latency &amp; cost per span</div></div>
<div class="dash-feat-card"><div class="dash-feat-icon">&#128178;</div><div class="dash-feat-name">Cost Analytics</div><div class="dash-feat-desc">Haiku vs Sonnet spend &mdash; see exact savings %</div></div>
<div class="dash-feat-card"><div class="dash-feat-icon">&#127919;</div><div class="dash-feat-name">Agent Performance</div><div class="dash-feat-desc">Reliability &amp; latency per agent across both runs</div></div>
<div class="dash-feat-card"><div class="dash-feat-icon">&#128203;</div><div class="dash-feat-name">Run History</div><div class="dash-feat-desc">Drill into any run to inspect raw prompts &amp; responses</div></div>
<div class="dash-feat-card"><div class="dash-feat-icon">&#128737;</div><div class="dash-feat-name">Guardrails Log</div><div class="dash-feat-desc">All guardrail events with severity &amp; action taken</div></div>
<div class="dash-feat-card"><div class="dash-feat-icon">&#9881;</div><div class="dash-feat-name">Settings</div><div class="dash-feat-desc">Tune thresholds live &mdash; applies to next run</div></div>
</div>
</div>
""", unsafe_allow_html=True)
        st.page_link("pages/observability.py", label="Open Observability Dashboard — compare both runs →", icon="📡")
    elif pdf_base or pdf_rout:
        missing = "WITH ROUTER" if pdf_base else "WITHOUT ROUTER"
        st.info(f"Run the PDF pipeline **{missing}** to unlock the full dashboard comparison.")

    st.markdown('</div>', unsafe_allow_html=True)
