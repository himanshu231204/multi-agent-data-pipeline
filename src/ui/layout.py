"""Shared HTML layout components: topbar, hero, agents strip."""

import streamlit as st


def render_topbar():
    st.markdown(
        """
<div class="topbar">
    <div>
        <div class="pipe-title">⚡ MULTI-AGENT DATA PIPELINE</div>
        <div class="pipe-sub">6 autonomous AI agents · CSV · PDF · Databases · github.com/harshitboots</div>
    </div>
    <div class="brand-right">
        <div class="live-badge"><span class="live-dot"></span> LIVE</div>
        <div class="v-badge">v2.0.0</div>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_hero():
    st.markdown(
        """
<div class="hero">
<div class="hero-inner">
<div class="hero-left">
    <div class="hero-eyebrow">Open Source &middot; AI Conference Demo</div>
    <h1>Your messy data,<br><span class="grad">cleaned autonomously.</span></h1>
    <p class="hero-sub">
        Upload any CSV, PDF, or connect your database &mdash; 6 specialised AI agents
        clean, anonymise, validate, transform, detect anomalies and summarise your data in seconds.
    </p>
    <div class="hero-stats">
        <span class="stat-pill blue">&#9889; 6 AI Agents</span>
        <span class="stat-pill purple">&#128256; Smart Router &mdash; Haiku + Sonnet</span>
        <span class="stat-pill green">&#128640; 63% Faster with Parallel Exec</span>
        <span class="stat-pill amber">&#128176; ~70% Cost Reduction</span>
    </div>
</div>
<div class="hero-right">
<div class="dpcard">
<div class="dpcard-header">
<span class="dpcard-icon">&#128225;</span>
<span class="dpcard-title">Observability Dashboard</span>
<span class="dpcard-live">LIVE</span>
</div>
<div class="dpcard-feat"><span class="dpcard-feat-icon">&#128225;</span><div><div class="dpcard-feat-name">Live Monitor</div><div class="dpcard-feat-desc">Agent waterfall with latency bars &mdash; inspect every prompt &amp; response</div></div></div>
<div class="dpcard-feat"><span class="dpcard-feat-icon">&#128203;</span><div><div class="dpcard-feat-name">Run History</div><div class="dpcard-feat-desc">All past runs stored in SQLite &mdash; drill into any run&#39;s agent spans</div></div></div>
<div class="dpcard-feat"><span class="dpcard-feat-icon">&#128178;</span><div><div class="dpcard-feat-name">Cost Analytics</div><div class="dpcard-feat-desc">Haiku vs Sonnet spend, savings % &amp; cost-per-run trend chart</div></div></div>
<div class="dpcard-feat"><span class="dpcard-feat-icon">&#127919;</span><div><div class="dpcard-feat-name">Agent Performance</div><div class="dpcard-feat-desc">Reliability %, avg latency &amp; parse failure rate per agent</div></div></div>
<div class="dpcard-feat"><span class="dpcard-feat-icon">&#128737;</span><div><div class="dpcard-feat-name">Guardrails Log</div><div class="dpcard-feat-desc">Budget cap, PII limit, parse failures &amp; timeout events with severity</div></div></div>
<div class="dpcard-feat"><span class="dpcard-feat-icon">&#9881;</span><div><div class="dpcard-feat-name">Settings</div><div class="dpcard-feat-desc">Tune budget, timeouts &amp; thresholds live without restarting</div></div></div>
<div class="dpcard-lock">
<span>&#128274;</span>
<span>Complete <strong>both runs</strong> (Without Router + With Router) below to see this dashboard fully populated with real data &mdash; then compare side by side.</span>
</div>
<a href="/observability" target="_self" class="dpcard-btn">Open Dashboard &#8594;</a>
</div>
</div>
</div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_agents_strip():
    st.markdown(
        """
<div class="agents-strip">
    <div class="agents-title">Pipeline Agents — Wave 1 runs in parallel · Wave 2 synthesises</div>
    <div class="ac"><div class="ac-num">01 · WAVE 1</div><div class="ac-icon">🧹</div><div class="ac-name">Cleaner</div><div class="ac-desc">Fixes nulls, date formats & inconsistencies across all rows</div><div class="ac-model">Haiku · Fast</div></div>
    <div class="ac"><div class="ac-num">02 · WAVE 1</div><div class="ac-icon">🔒</div><div class="ac-name">PII Anonymiser</div><div class="ac-desc">Masks emails, phones, postcodes & card numbers</div><div class="ac-model">Regex · Free</div></div>
    <div class="ac"><div class="ac-num">03 · WAVE 1</div><div class="ac-icon">🛡️</div><div class="ac-name">Validator</div><div class="ac-desc">Checks schema, data types & completeness score</div><div class="ac-model">Sonnet · Quality</div></div>
    <div class="ac"><div class="ac-num">04 · WAVE 1</div><div class="ac-icon">⚡</div><div class="ac-name">Transformer</div><div class="ac-desc">Derives new columns & standardises values</div><div class="ac-model">Haiku · Fast</div></div>
    <div class="ac"><div class="ac-num">05 · WAVE 1</div><div class="ac-icon">📡</div><div class="ac-name">Anomaly Detector</div><div class="ac-desc">Finds outliers, impossible values & suspicious patterns</div><div class="ac-model">Sonnet · Quality</div></div>
    <div class="ac"><div class="ac-num">06 · WAVE 2</div><div class="ac-icon">📊</div><div class="ac-name">Summariser</div><div class="ac-desc">Generates business insights & recommendations from all agents</div><div class="ac-model">Sonnet · Quality</div></div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_footer():
    st.markdown(
        """
<div class="footer">
    <div class="footer-left">
        <span class="footer-dot"></span>
        Multi-Agent Data Pipeline · Open Source · github.com/harshitboots
    </div>
    <div class="footer-right">v2.0.0 · <span>MIT License</span></div>
</div>
""",
        unsafe_allow_html=True,
    )
