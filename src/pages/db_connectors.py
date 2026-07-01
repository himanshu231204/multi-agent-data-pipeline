"""Database Connectors page — DB type selector, connection forms, and pipeline run."""

import json
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
        st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)

        # ── DB MODE SELECTOR ─────────────────────────────────
        st.markdown('<div class="section-label">Select Run Mode</div>', unsafe_allow_html=True)

        if "db_routing_on" not in st.session_state:
            st.session_state["db_routing_on"] = False
        db_routing_on = st.session_state["db_routing_on"]

        col_db, col_dr = st.columns(2)
        with col_db:
            dba = "active-baseline" if not db_routing_on else ""
            dbt = '<div class="selected-tick tick-baseline">&#10003;</div>' if not db_routing_on else ""
            html_db_b = (
                f'<div class="mode-card {dba}">'
                f'{dbt}'
                f'<div class="mode-card-badge badge-baseline">Baseline</div>'
                f'<div class="mode-card-title">Without Router</div>'
                f'<div class="mode-card-sub">All 6 agents use Sonnet. Maximum accuracy on your database data.</div>'
                f'<div class="mode-stats">'
                f'<div class="mode-stat"><span>6</span>Agents</div>'
                f'<div class="mode-stat"><span>Sonnet</span>All</div>'
                f'<div class="mode-stat"><span>Max</span>Quality</div>'
                f'</div></div>'
            )
            st.markdown(html_db_b, unsafe_allow_html=True)
            if st.button("Select: Without Router (Baseline)", key="db_sel_baseline", use_container_width=True):
                st.session_state["db_routing_on"] = False
                st.rerun()

        with col_dr:
            dra = "active-router" if db_routing_on else ""
            drt = '<div class="selected-tick tick-router">&#10003;</div>' if db_routing_on else ""
            html_db_r = (
                f'<div class="mode-card {dra}">'
                f'{drt}'
                f'<div class="mode-card-badge badge-router">Smart Router</div>'
                f'<div class="mode-card-title">With Router</div>'
                f'<div class="mode-card-sub">Simple agents &#8594; Haiku, complex agents &#8594; Sonnet. ~70% cheaper.</div>'
                f'<div class="mode-stats">'
                f'<div class="mode-stat"><span>4</span>Haiku</div>'
                f'<div class="mode-stat"><span>2</span>Sonnet</div>'
                f'<div class="mode-stat"><span>~70%</span>Cheaper</div>'
                f'</div></div>'
            )
            st.markdown(html_db_r, unsafe_allow_html=True)
            if st.button("Select: With Router (Save 70%)", key="db_sel_router", use_container_width=True):
                st.session_state["db_routing_on"] = True
                st.rerun()

        db_routing_on = st.session_state["db_routing_on"]
        db_mode_label = "With Router" if db_routing_on else "Without Router (Baseline)"
        st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)

        # ── DB AUTH & CREDITS ────────────────────────────────
        st.markdown('<div class="section-label">GitHub Access &amp; Free Credits</div>', unsafe_allow_html=True)
        db_active_user, db_byok_key, db_credits_info = auth_section("db")
        if not db_active_user:
            anon_credit_banner(visitor_fp)

        st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)

        if st.button(f"▶ Run Pipeline on DB Data — {db_mode_label}", use_container_width=True, type="primary"):
            run_ok, run_mode = check_can_run(db_active_user, db_byok_key, visitor_fp)
            if not run_ok:
                st.error("No free runs remaining. Enter your GitHub username above, add your API key, or fork the repo.")
            else:
                api_key_to_use = db_byok_key or None
                with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
                    df.to_csv(tmp.name, index=False)
                    tmp_path = tmp.name
                guardrail_cfg = st.session_state.get("guardrail_config", {})
                guardrails = GuardrailEngine(**guardrail_cfg) if guardrail_cfg else GuardrailEngine()
                with st.spinner(f"Running pipeline ({db_mode_label})..."):
                    result = run_pipeline(tmp_path, routing_enabled=db_routing_on, guardrails=guardrails, api_key=api_key_to_use)
                os.unlink(tmp_path)
                record_run_anon_or_user(db_active_user, run_mode, visitor_fp)
                st.success(f"Done — GBP {result.total_cost_gbp:.5f} · {result.total_latency_ms}ms")
                display_result_tabs(result)

    st.markdown('</div>', unsafe_allow_html=True)
