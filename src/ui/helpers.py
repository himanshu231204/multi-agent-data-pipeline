"""Display helper functions for pipeline results, cost cards, and comparison tables."""

import streamlit as st
import pandas as pd


def display_result_tabs(result):
    if not result:
        return
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Rows Fixed", result.cleaner.rows_affected if result.cleaner else 0)
    c2.metric("PII Rows", result.pii.rows_affected if result.pii else 0)
    c3.metric("Completeness", f"{result.validator.completeness_score if result.validator else 0}%")
    c4.metric("Transformed", result.transformer.rows_transformed if result.transformer else 0)
    c5.metric("Anomalies", result.anomaly.anomaly_count if result.anomaly else 0)
    c6.metric("Quality", f"{result.quality_score}%")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        ["Cleaner", "PII", "Validator", "Transformer", "Anomaly", "Summariser"]
    )
    with tab1:
        if result.cleaner:
            for issue in result.cleaner.issues_fixed:
                st.markdown(f"- {issue}")
    with tab2:
        if result.pii:
            if result.pii.pii_types_detected:
                st.warning(f"PII types: {', '.join(result.pii.pii_types_detected)}")
            for f in result.pii.pii_found:
                st.markdown(f"- {f}")
    with tab3:
        if result.validator:
            st.markdown(f"**Completeness:** {result.validator.completeness_score}%")
            for v in result.validator.violations:
                st.error(v)
    with tab4:
        if result.transformer:
            for t in result.transformer.transformations_applied:
                st.markdown(f"- {t}")
    with tab5:
        if result.anomaly:
            st.markdown(f"**Risk score:** {result.anomaly.anomaly_score}/10")
            for a in result.anomaly.anomalies:
                st.warning(a)
    with tab6:
        if result.summariser:
            st.info(result.summariser.summary)
            st.json(result.summariser.key_stats)
            for r in result.summariser.recommendations:
                st.markdown(f"- {r}")


def display_cost_card(result, label: str):
    if not result:
        return
    st.markdown(f"**{label}**")
    st.metric("Total Cost", f"GBP {result.total_cost_gbp:.5f}")
    st.metric("Latency", f"{result.total_latency_ms}ms")
    st.metric("Mode", result.mode)
    if result.telemetry:
        rows = [{"Agent": t.agent_name, "Model": t.model_label,
                 "Cost GBP": f"{t.cost_gbp:.5f}", "Latency ms": t.latency_ms,
                 "Status": "ok" if t.parse_ok else "FAIL"}
                for t in result.telemetry]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def comparison_table(baseline, routed):
    if not baseline or not routed:
        return
    st.markdown("### Cost Comparison")
    rows = []
    for bt in baseline.telemetry:
        rt_match = next((r for r in routed.telemetry if r.agent_name == bt.agent_name), None)
        saving = ((bt.cost_gbp - rt_match.cost_gbp) / bt.cost_gbp * 100) if rt_match and bt.cost_gbp > 0 else 0
        rows.append({
            "Agent": bt.agent_name,
            "Without Router": f"GBP {bt.cost_gbp:.5f} ({bt.model_label})",
            "With Router": f"GBP {rt_match.cost_gbp:.5f} ({rt_match.model_label})" if rt_match else "-",
            "Saving": f"{saving:.0f}%" if saving else "-",
        })
    rows.append({
        "Agent": "TOTAL",
        "Without Router": f"GBP {baseline.total_cost_gbp:.5f}",
        "With Router": f"GBP {routed.total_cost_gbp:.5f}",
        "Saving": f"{(baseline.total_cost_gbp - routed.total_cost_gbp) / baseline.total_cost_gbp * 100:.0f}%" if baseline.total_cost_gbp > 0 else "-",
    })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    lat_saving = (baseline.total_latency_ms - routed.total_latency_ms) / baseline.total_latency_ms * 100 if baseline.total_latency_ms > 0 else 0
    c1, c2, c3 = st.columns(3)
    c1.metric("Cost saved", f"{(baseline.total_cost_gbp - routed.total_cost_gbp):.5f} GBP")
    c2.metric("Latency saved", f"{lat_saving:.0f}%")
    c3.metric("Quality delta", f"{routed.quality_score - baseline.quality_score:+.1f}%")
