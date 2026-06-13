import streamlit as st
import pandas as pd
import json
import os
import sys
import base64
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.agents import cleaner, validator, transformer, anomaly, summariser

st.set_page_config(
    page_title="Multi-Agent Pipeline · Britcore.AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;500;700;800&display=swap');

html, body, [class*="css"], .stApp {
    background-color: #060910 !important;
    color: #e2e8f0 !important;
    font-family: 'Syne', sans-serif !important;
}

header[data-testid="stHeader"] { display: none !important; }
section[data-testid="stSidebar"] { display: none !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }

.topbar {
    background: #080c14;
    border-bottom: 1px solid #0f1f35;
    padding: 20px 48px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    min-height: 72px;
}

.brand-right {
    display: flex;
    align-items: center;
    gap: 14px;
    border: 0.5px solid #0f1f35;
    padding: 10px 20px;
    border-radius: 28px;
    background: #060910;
}

.pipe-title {
    font-family: 'Space Mono', monospace;
    font-size: 15px;
    color: #38bdf8;
    font-weight: 700;
    letter-spacing: 0.06em;
}

.pipe-sub {
    font-size: 12px;
    color: #94a3b8;
    font-family: 'Space Mono', monospace;
    margin-top: 4px;
}

.hero {
    padding: 48px 48px 36px;
    border-bottom: 1px solid #0f1f35;
    background: #080c14;
}

.hero h1 {
    font-size: 42px;
    font-weight: 800;
    color: #f8fafc;
    letter-spacing: -0.03em;
    line-height: 1.15;
    margin: 0 0 12px 0;
}

.hero h1 em { color: #fbbf24; font-style: normal; }
.hero p { font-size: 14px; color: #94a3b8; font-family: 'Space Mono', monospace; margin: 0; }

.agents-strip {
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 10px;
    padding: 24px 48px;
    border-bottom: 1px solid #0f1f35;
    background: #060910;
}

.ac {
    background: #080c14;
    border: 0.5px solid #0f1f35;
    border-radius: 12px;
    padding: 14px 12px;
    text-align: center;
}

.ac-num { font-family: 'Space Mono', monospace; font-size: 10px; color: #2a3a4a; margin-bottom: 8px; }
.ac-icon { font-size: 22px; margin-bottom: 8px; display: block; }
.ac-name { font-family: 'Space Mono', monospace; font-size: 9px; font-weight: 700; letter-spacing: 0.08em; color: #2a4a5a; text-transform: uppercase; margin-bottom: 4px; }
.ac-desc { font-size: 11px; color: #3a5a6a; line-height: 1.4; }

.ac:nth-child(1) { border-color: #38bdf844; background: #071a2c; }
.ac:nth-child(1) .ac-num, .ac:nth-child(1) .ac-name { color: #38bdf8; }
.ac:nth-child(2) { border-color: #facc1544; background: #2e2608; }
.ac:nth-child(2) .ac-num, .ac:nth-child(2) .ac-name { color: #facc15; }
.ac:nth-child(3) { border-color: #a78bfa44; background: #191228; }
.ac:nth-child(3) .ac-num, .ac:nth-child(3) .ac-name { color: #a78bfa; }
.ac:nth-child(4) { border-color: #34d39944; background: #061f11; }
.ac:nth-child(4) .ac-num, .ac:nth-child(4) .ac-name { color: #34d399; }
.ac:nth-child(5) { border-color: #fb718544; background: #2c0a14; }
.ac:nth-child(5) .ac-num, .ac:nth-child(5) .ac-name { color: #fb7185; }

.mode-tabs {
    display: flex;
    gap: 0;
    padding: 0 48px;
    border-bottom: 1px solid #0f1f35;
    background: #080c14;
}

.mode-tab {
    padding: 16px 28px;
    font-family: 'Space Mono', monospace;
    font-size: 12px;
    color: #3a5a6a;
    cursor: pointer;
    border-bottom: 2px solid transparent;
    letter-spacing: 0.05em;
    font-weight: 700;
    text-transform: uppercase;
}

.mode-tab.active { color: #38bdf8; border-bottom-color: #38bdf8; }

.section-pad { padding: 28px 48px; }
.section-label {
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 16px;
    padding-bottom: 8px;
    border-bottom: 0.5px solid #0f1f35;
}

.connector-grid {
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 10px;
    margin-bottom: 24px;
}

.connector-card {
    background: #080c14;
    border: 0.5px solid #0f1f35;
    border-radius: 12px;
    padding: 16px;
    text-align: center;
    cursor: pointer;
    transition: border-color 0.2s;
}

.connector-card:hover { border-color: #38bdf844; }
.connector-card.selected { border-color: #38bdf8; background: #071a2c; }
.connector-card .cc-icon { font-size: 28px; margin-bottom: 8px; display: block; }
.connector-card .cc-name { font-family: 'Space Mono', monospace; font-size: 10px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.06em; }
.connector-card.selected .cc-name { color: #38bdf8; }

.conn-form {
    background: #080c14;
    border: 0.5px solid #0f1f35;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 20px;
}

.conn-form-title {
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    color: #38bdf8;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 16px;
}

div[data-testid="metric-container"] {
    background: #080c14 !important;
    border: 0.5px solid #0f1f35 !important;
    border-radius: 12px !important;
    padding: 20px !important;
}

div[data-testid="metric-container"] label {
    color: #94a3b8 !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 10px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}

div[data-testid="stMetricValue"] {
    color: #00ff88 !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 32px !important;
    font-weight: 700 !important;
}

.stTextInput > div > div > input {
    background: #060910 !important;
    border: 0.5px solid #0f1f35 !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 12px !important;
}

.stSelectbox > div > div {
    background: #060910 !important;
    border: 0.5px solid #0f1f35 !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
}

.stButton > button {
    background: #38bdf8 !important;
    color: #060910 !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Space Mono', monospace !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    letter-spacing: 0.06em !important;
    padding: 14px 28px !important;
    width: 100% !important;
}

.stButton > button:hover { opacity: 0.85 !important; }

.stTabs [data-baseweb="tab-list"] { background: #080c14 !important; border-bottom: 0.5px solid #0f1f35 !important; }
.stTabs [data-baseweb="tab"] { font-family: 'Space Mono', monospace !important; font-size: 11px !important; color: #94a3b8 !important; background: transparent !important; padding: 10px 16px !important; }
.stTabs [aria-selected="true"] { color: #38bdf8 !important; border-bottom: 2px solid #38bdf8 !important; }
.stTabs [data-baseweb="tab-panel"] { background: #080c14 !important; border: 0.5px solid #0f1f35 !important; border-top: none !important; border-radius: 0 0 12px 12px !important; padding: 20px !important; }

.stProgress > div > div > div { background: #38bdf8 !important; }

.footer {
    padding: 20px 48px;
    border-top: 1px solid #0f1f35;
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #080c14;
    margin-top: 40px;
}

.footer-left { font-family: 'Space Mono', monospace; font-size: 11px; color: #38bdf8; display: flex; align-items: center; gap: 8px; }
.footer-dot { width: 7px; height: 7px; border-radius: 50%; background: #38bdf8; display: inline-block; }
.footer-right { font-family: 'Space Mono', monospace; font-size: 10px; color: #3a5a6a; }
.footer-right span { color: #00e5ff; }
</style>
""", unsafe_allow_html=True)

def get_logo_b64():
    if os.path.exists("britcore_logo.png"):
        with open("britcore_logo.png", "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

logo_b64 = get_logo_b64()
logo_img = f'<img src="data:image/png;base64,{logo_b64}" style="height:40px;width:auto;">' if logo_b64 else '<span style="font-family:Space Mono,monospace;font-size:16px;font-weight:700;color:#00e5ff;">Britcore.AI</span>'

st.markdown(f"""
<div class="topbar">
    <div>
        <div class="pipe-title">⚡ MULTI-AGENT DATA PIPELINE</div>
        <div class="pipe-sub">5-agent autonomous data processor · github.com/harshitboots</div>
    </div>
    <div class="brand-right">{logo_img}</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <h1>Your data,<br><em>processed autonomously.</em></h1>
    <p>CSV · PDF · Databases — 5 AI agents clean, validate, transform, detect anomalies & summarise</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="agents-strip">
    <div class="ac"><div class="ac-num">01</div><div class="ac-icon">🧹</div><div class="ac-name">Cleaner</div><div class="ac-desc">Fixes nulls, formats & inconsistencies</div></div>
    <div class="ac"><div class="ac-num">02</div><div class="ac-icon">🛡</div><div class="ac-name">Validator</div><div class="ac-desc">Checks schema, types & constraints</div></div>
    <div class="ac"><div class="ac-num">03</div><div class="ac-icon">⚡</div><div class="ac-name">Transformer</div><div class="ac-desc">Derives columns & standardises data</div></div>
    <div class="ac"><div class="ac-num">04</div><div class="ac-icon">📡</div><div class="ac-name">Anomaly</div><div class="ac-desc">Finds outliers & suspicious values</div></div>
    <div class="ac"><div class="ac-num">05</div><div class="ac-icon">📊</div><div class="ac-name">Summariser</div><div class="ac-desc">Generates insights & recommendations</div></div>
</div>
""", unsafe_allow_html=True)

mode = st.radio(
    "Mode",
    ["📄 CSV Pipeline", "📑 PDF Intelligence", "🔌 Database Connectors"],
    horizontal=True,
    label_visibility="collapsed"
)

st.markdown('<div style="height:1px;background:#0f1f35;margin:0 48px;"></div>', unsafe_allow_html=True)

def run_pipeline_ui(df):
    total_rows = len(df)
    preview = df.head(20).to_csv(index=False)
    progress = st.progress(0)

    with st.status("Agent 1 / 5 — Cleaner", expanded=False) as s:
        cleaner_result = cleaner.run(preview, total_rows)
        s.update(label="✅ Agent 1 / 5 — Cleaner complete", state="complete")
    progress.progress(20)

    with st.status("Agent 2 / 5 — Validator", expanded=False) as s:
        validator_result = validator.run(preview, total_rows)
        s.update(label="✅ Agent 2 / 5 — Validator complete", state="complete")
    progress.progress(40)

    with st.status("Agent 3 / 5 — Transformer", expanded=False) as s:
        transformer_result = transformer.run(preview, total_rows)
        s.update(label="✅ Agent 3 / 5 — Transformer complete", state="complete")
    progress.progress(60)

    with st.status("Agent 4 / 5 — Anomaly Detector", expanded=False) as s:
        anomaly_result = anomaly.run(preview, total_rows)
        s.update(label="✅ Agent 4 / 5 — Anomaly Detector complete", state="complete")
    progress.progress(80)

    context = f"Cleaner: {len(cleaner_result.issues_fixed)} issues. Validator: {validator_result.completeness_score}%. Transformer: {len(transformer_result.transformations_applied)} transforms. Anomaly: {anomaly_result.anomaly_count} found."

    with st.status("Agent 5 / 5 — Summariser", expanded=False) as s:
        summariser_result = summariser.run(preview, total_rows, context)
        s.update(label="✅ Agent 5 / 5 — Summariser complete", state="complete")
    progress.progress(100)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Rows Fixed", cleaner_result.rows_affected)
    c2.metric("Completeness", f"{validator_result.completeness_score}%")
    c3.metric("Transformed", transformer_result.rows_transformed)
    c4.metric("Anomalies", anomaly_result.anomaly_count)
    c5.metric("Recommendations", len(summariser_result.recommendations))

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🧹 Cleaner", "🛡 Validator", "⚡ Transformer", "📡 Anomaly", "📊 Summariser"])

    with tab1:
        for issue in cleaner_result.issues_fixed:
            st.markdown(f"- {issue}")
        if cleaner_result.cleaned_columns:
            st.info(f"Cleaned columns: {', '.join(cleaner_result.cleaned_columns)}")

    with tab2:
        st.markdown(f"**Schema valid:** {'✅ Yes' if validator_result.schema_ok else '❌ No'}")
        st.markdown(f"**Completeness:** {validator_result.completeness_score}%")
        for v in validator_result.violations:
            st.error(v)
        for c in validator_result.passed_checks:
            st.success(c)

    with tab3:
        for t in transformer_result.transformations_applied:
            st.markdown(f"- {t}")
        if transformer_result.new_columns:
            st.info(f"New columns: {', '.join(transformer_result.new_columns)}")

    with tab4:
        st.markdown(f"**Risk score:** {anomaly_result.anomaly_score}/10")
        for a in anomaly_result.anomalies:
            st.warning(a)

    with tab5:
        st.info(summariser_result.summary)
        st.json(summariser_result.key_stats)
        for r in summariser_result.recommendations:
            st.markdown(f"→ {r}")

    full_results = {
        "total_rows": total_rows,
        "cleaner": cleaner_result.model_dump(),
        "validator": validator_result.model_dump(),
        "transformer": transformer_result.model_dump(),
        "anomaly": anomaly_result.model_dump(),
        "summariser": summariser_result.model_dump()
    }

    st.download_button(
        label="⬇️ Download Results as JSON",
        data=json.dumps(full_results, indent=2),
        file_name="pipeline_results.json",
        mime="application/json",
        use_container_width=True
    )

if mode == "📄 CSV Pipeline":
    st.markdown('<div class="section-pad">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Upload your dataset</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Drop CSV here", type=["csv"], label_visibility="collapsed")
    use_demo = st.checkbox("Use demo dataset — retail transactions with intentional data quality issues")

    if use_demo and os.path.exists("demo/sample_data.csv"):
        df = pd.read_csv("demo/sample_data.csv")
        st.success(f"Demo loaded — {len(df)} rows · {len(df.columns)} columns")
        st.dataframe(df, use_container_width=True, height=240)
    elif uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.success(f"Loaded — {len(df)} rows · {len(df.columns)} columns")
        st.dataframe(df, use_container_width=True, height=240)

    if use_demo or uploaded_file:
        if st.button("⚡ RUN PIPELINE — ALL 5 AGENTS →"):
            df = pd.read_csv("demo/sample_data.csv") if use_demo else pd.read_csv(uploaded_file)
            run_pipeline_ui(df)

    st.markdown('</div>', unsafe_allow_html=True)

elif mode == "📑 PDF Intelligence":
    st.markdown('<div class="section-pad">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Upload a PDF document</div>', unsafe_allow_html=True)

    pdf_file = st.file_uploader("Drop PDF here", type=["pdf"], label_visibility="collapsed")
    use_demo_pdf = st.checkbox("Use demo PDF — Project Alpha Q1 2024 quarterly review report")
    if use_demo_pdf and os.path.exists("demo/sample_report.pdf"):
        with open("demo/sample_report.pdf", "rb") as f:
            import io
            pdf_file = io.BytesIO(f.read())
            pdf_file.name = "sample_report.pdf"
        st.success("Demo PDF loaded — Project Alpha Q1 2024 Report")

    if pdf_file:
        try:
            from pypdf import PdfReader
            from src.agents import pdf_parser, entity_extractor, risk_detector, action_extractor
            import io

            reader = PdfReader(io.BytesIO(pdf_file.read()))
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""

            total_pages = len(reader.pages)
            word_count = len(text.split())

            st.success(f"PDF loaded — {total_pages} pages · {word_count} words")

            with st.expander("Preview extracted text"):
                st.text(text[:2000] + "..." if len(text) > 2000 else text)

            if st.button("⚡ RUN PDF PIPELINE — ALL 5 AGENTS →"):
                preview = text[:3000]
                progress = st.progress(0)

                with st.status("Agent 1 / 5 — PDF Parser", expanded=False) as s:
                    parser_result = pdf_parser.run(preview, total_pages)
                    s.update(label="✅ Agent 1 / 5 — PDF Parser complete", state="complete")
                progress.progress(20)

                with st.status("Agent 2 / 5 — Entity Extractor", expanded=False) as s:
                    entity_result = entity_extractor.run(preview, total_pages)
                    s.update(label="✅ Agent 2 / 5 — Entity Extractor complete", state="complete")
                progress.progress(40)

                with st.status("Agent 3 / 5 — Risk Detector", expanded=False) as s:
                    risk_result = risk_detector.run(preview, total_pages)
                    s.update(label="✅ Agent 3 / 5 — Risk Detector complete", state="complete")
                progress.progress(60)

                with st.status("Agent 4 / 5 — Action Extractor", expanded=False) as s:
                    action_result = action_extractor.run(preview, total_pages)
                    s.update(label="✅ Agent 4 / 5 — Action Extractor complete", state="complete")
                progress.progress(80)

                context = f"""
                Document type: {parser_result.document_type}.
                Entities found: {entity_result.total_entities}.
                Risk level: {risk_result.risk_level}, score: {risk_result.overall_risk_score}/10.
                Actions found: {action_result.total_actions}.
                Risk recommendations: {len(risk_result.recommendations)}.
                """

                with st.status("Agent 5 / 5 — Summariser", expanded=False) as s:
                    summariser_result = summariser.run(preview, total_pages, context)
                    s.update(label="✅ Agent 5 / 5 — Summariser complete", state="complete")
                progress.progress(100)

                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("Pages", total_pages)
                c2.metric("Entities", entity_result.total_entities)
                c3.metric("Risk Score", f"{risk_result.overall_risk_score}/10")
                c4.metric("Actions", action_result.total_actions)
                c5.metric("Insights", len(summariser_result.recommendations))

                tab1, tab2, tab3, tab4, tab5 = st.tabs([
                    "📄 Parser", "🔍 Entities", "⚠️ Risks", "✅ Actions", "📊 Summary"
                ])

                with tab1:
                    st.markdown(f"**Document type:** {parser_result.document_type}")
                    st.markdown(f"**Language:** {parser_result.language}")
                    st.markdown(f"**Quality:** {parser_result.document_quality}")
                    st.markdown(f"**Has tables:** {'✅' if parser_result.has_tables else '❌'}")
                    st.markdown(f"**Has numbers:** {'✅' if parser_result.has_numbers else '❌'}")
                    if parser_result.key_topics:
                        st.markdown("**Key topics:**")
                        for t in parser_result.key_topics:
                            st.markdown(f"- {t}")
                    if parser_result.parsing_notes:
                        for n in parser_result.parsing_notes:
                            st.info(n)

                with tab2:
                    col1, col2 = st.columns(2)
                    with col1:
                        if entity_result.people:
                            st.markdown("**People:**")
                            for p in entity_result.people:
                                st.markdown(f"- {p}")
                        if entity_result.organisations:
                            st.markdown("**Organisations:**")
                            for o in entity_result.organisations:
                                st.markdown(f"- {o}")
                        if entity_result.locations:
                            st.markdown("**Locations:**")
                            for l in entity_result.locations:
                                st.markdown(f"- {l}")
                    with col2:
                        if entity_result.dates:
                            st.markdown("**Dates:**")
                            for d in entity_result.dates:
                                st.markdown(f"- {d}")
                        if entity_result.amounts:
                            st.markdown("**Amounts:**")
                            for a in entity_result.amounts:
                                st.markdown(f"- {a}")
                        if entity_result.emails:
                            st.markdown("**Emails:**")
                            for e in entity_result.emails:
                                st.markdown(f"- {e}")

                with tab3:
                    st.markdown(f"**Risk level:** {risk_result.risk_level.upper()}")
                    st.markdown(f"**Overall risk score:** {risk_result.overall_risk_score}/10")
                    st.markdown(f"**PII detected:** {'⚠️ Yes' if risk_result.pii_detected else '✅ No'}")
                    if risk_result.pii_types:
                        st.warning(f"PII types found: {', '.join(risk_result.pii_types)}")
                    if risk_result.compliance_risks:
                        st.markdown("**Compliance risks:**")
                        for r in risk_result.compliance_risks:
                            st.error(r)
                    if risk_result.legal_risks:
                        st.markdown("**Legal risks:**")
                        for r in risk_result.legal_risks:
                            st.warning(r)
                    if risk_result.financial_risks:
                        st.markdown("**Financial risks:**")
                        for r in risk_result.financial_risks:
                            st.warning(r)
                    if risk_result.recommendations:
                        st.markdown("**Recommendations:**")
                        for r in risk_result.recommendations:
                            st.markdown(f"→ {r}")

                with tab4:
                    if action_result.priority_actions:
                        st.markdown("**Priority actions:**")
                        for a in action_result.priority_actions:
                            st.error(f"🔴 {a}")
                    if action_result.action_items:
                        st.markdown("**All action items:**")
                        for a in action_result.action_items:
                            st.markdown(f"- {a}")
                    if action_result.decisions_made:
                        st.markdown("**Decisions made:**")
                        for d in action_result.decisions_made:
                            st.success(d)
                    if action_result.deadlines:
                        st.markdown("**Deadlines:**")
                        for d in action_result.deadlines:
                            st.warning(d)
                    if action_result.owners:
                        st.markdown("**Owners:**")
                        for o in action_result.owners:
                            st.markdown(f"- {o}")

                with tab5:
                    st.info(summariser_result.summary)
                    st.json(summariser_result.key_stats)
                    for r in summariser_result.recommendations:
                        st.markdown(f"→ {r}")

                full_results = {
                    "total_pages": total_pages,
                    "word_count": word_count,
                    "parser": parser_result.model_dump(),
                    "entities": entity_result.model_dump(),
                    "risks": risk_result.model_dump(),
                    "actions": action_result.model_dump(),
                    "summary": summariser_result.model_dump()
                }

                st.download_button(
                    label="⬇️ Download Full PDF Analysis as JSON",
                    data=json.dumps(full_results, indent=2),
                    file_name="pdf_analysis_results.json",
                    mime="application/json",
                    use_container_width=True
                )

        except Exception as e:
            st.error(f"Error reading PDF: {e}")

    st.markdown('</div>', unsafe_allow_html=True)

elif mode == "🔌 Database Connectors":
    st.markdown('<div class="section-pad">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Select your database</div>', unsafe_allow_html=True)

    db_type = st.selectbox(
        "Database",
        ["Azure Databricks", "Snowflake", "PostgreSQL", "MySQL", "BigQuery", "DuckDB"],
        label_visibility="collapsed"
    )

    st.markdown('<div class="conn-form">', unsafe_allow_html=True)
    st.markdown(f'<div class="conn-form-title">🔌 {db_type} Connection</div>', unsafe_allow_html=True)

    df = None

    if db_type == "Azure Databricks":
        col1, col2 = st.columns(2)
        with col1:
            host = st.text_input("Workspace URL", placeholder="adb-xxxxx.azuredatabricks.net")
            http_path = st.text_input("HTTP Path", placeholder="/sql/1.0/warehouses/xxxxx")
        with col2:
            token = st.text_input("Personal Access Token", type="password", placeholder="dapi...")
            table = st.text_input("Table Name", placeholder="catalog.schema.table")

        if st.button("🔌 Connect & Fetch Table"):
            if host and token and http_path and table:
                try:
                    from src.connectors.databricks import fetch_table
                    with st.spinner("Connecting to Databricks..."):
                        df = fetch_table(host, token, http_path, table)
                    st.success(f"Connected — {len(df)} rows fetched from {table}")
                    st.dataframe(df, use_container_width=True, height=240)
                except Exception as e:
                    st.error(f"Connection failed: {e}")
            else:
                st.warning("Please fill all fields")

    elif db_type == "Snowflake":
        col1, col2 = st.columns(2)
        with col1:
            account = st.text_input("Account", placeholder="xy12345.eu-west-1")
            database = st.text_input("Database", placeholder="MY_DATABASE")
            table = st.text_input("Table", placeholder="MY_TABLE")
        with col2:
            user = st.text_input("Username", placeholder="my_user")
            password = st.text_input("Password", type="password")
            schema = st.text_input("Schema", placeholder="PUBLIC")

        if st.button("🔌 Connect & Fetch Table"):
            if account and user and password and database and schema and table:
                try:
                    from src.connectors.snowflake_conn import fetch_table
                    with st.spinner("Connecting to Snowflake..."):
                        df = fetch_table(account, user, password, database, schema, table)
                    st.success(f"Connected — {len(df)} rows fetched")
                    st.dataframe(df, use_container_width=True, height=240)
                except Exception as e:
                    st.error(f"Connection failed: {e}")
            else:
                st.warning("Please fill all fields")

    elif db_type == "PostgreSQL":
        col1, col2 = st.columns(2)
        with col1:
            host = st.text_input("Host", placeholder="localhost")
            database = st.text_input("Database", placeholder="my_database")
            table = st.text_input("Table", placeholder="my_table")
        with col2:
            port = st.text_input("Port", value="5432")
            user = st.text_input("Username", placeholder="postgres")
            password = st.text_input("Password", type="password")

        if st.button("🔌 Connect & Fetch Table"):
            if host and database and user and password and table:
                try:
                    from src.connectors.postgres import fetch_table
                    with st.spinner("Connecting to PostgreSQL..."):
                        df = fetch_table(host, int(port), database, user, password, table)
                    st.success(f"Connected — {len(df)} rows fetched")
                    st.dataframe(df, use_container_width=True, height=240)
                except Exception as e:
                    st.error(f"Connection failed: {e}")
            else:
                st.warning("Please fill all fields")

    elif db_type == "MySQL":
        col1, col2 = st.columns(2)
        with col1:
            host = st.text_input("Host", placeholder="localhost")
            database = st.text_input("Database", placeholder="my_database")
            table = st.text_input("Table", placeholder="my_table")
        with col2:
            port = st.text_input("Port", value="3306")
            user = st.text_input("Username", placeholder="root")
            password = st.text_input("Password", type="password")

        if st.button("🔌 Connect & Fetch Table"):
            if host and database and user and password and table:
                try:
                    from src.connectors.mysql import fetch_table
                    with st.spinner("Connecting to MySQL..."):
                        df = fetch_table(host, int(port), database, user, password, table)
                    st.success(f"Connected — {len(df)} rows fetched")
                    st.dataframe(df, use_container_width=True, height=240)
                except Exception as e:
                    st.error(f"Connection failed: {e}")
            else:
                st.warning("Please fill all fields")

    elif db_type == "BigQuery":
        col1, col2 = st.columns(2)
        with col1:
            project_id = st.text_input("Project ID", placeholder="my-gcp-project")
            dataset = st.text_input("Dataset", placeholder="my_dataset")
            table = st.text_input("Table", placeholder="my_table")
        with col2:
            credentials_file = st.file_uploader("Service Account JSON", type=["json"])

        if st.button("🔌 Connect & Fetch Table"):
            if project_id and dataset and table and credentials_file:
                try:
                    from src.connectors.bigquery import fetch_table
                    credentials_json = json.load(credentials_file)
                    with st.spinner("Connecting to BigQuery..."):
                        df = fetch_table(project_id, credentials_json, dataset, table)
                    st.success(f"Connected — {len(df)} rows fetched")
                    st.dataframe(df, use_container_width=True, height=240)
                except Exception as e:
                    st.error(f"Connection failed: {e}")
            else:
                st.warning("Please fill all fields")

    elif db_type == "DuckDB":
        col1, col2 = st.columns(2)
        with col1:
            database = st.text_input("Database File", placeholder="/path/to/my_database.duckdb")
        with col2:
            table = st.text_input("Table", placeholder="my_table")

        if st.button("🔌 Connect & Fetch Table"):
            if database and table:
                try:
                    from src.connectors.duckdb_conn import fetch_table
                    with st.spinner("Connecting to DuckDB..."):
                        df = fetch_table(database, table)
                    st.success(f"Connected — {len(df)} rows fetched")
                    st.dataframe(df, use_container_width=True, height=240)
                except Exception as e:
                    st.error(f"Connection failed: {e}")
            else:
                st.warning("Please fill all fields")

    st.markdown('</div>', unsafe_allow_html=True)

    if df is not None and not df.empty:
        st.markdown('<div style="margin-top:8px;"></div>', unsafe_allow_html=True)
        if st.button("⚡ RUN PIPELINE ON THIS DATA — ALL 5 AGENTS →"):
            run_pipeline_ui(df)

    st.markdown('</div>', unsafe_allow_html=True)

st.markdown(f"""
<div class="footer">
    <div class="footer-left">
        <span class="footer-dot"></span>
        Multi-Agent Data Pipeline · Open Source · github.com/harshitboots
    </div>
    <div class="footer-right">powered by <span>Britcore.AI</span></div>
</div>
""", unsafe_allow_html=True)