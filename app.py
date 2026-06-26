import streamlit as st
import pandas as pd
import json
import os
import sys
import base64
import tempfile
from dotenv import load_dotenv

load_dotenv()

# Load secrets from Streamlit Cloud if running in cloud environment
for _key in ["ANTHROPIC_API_KEY", "ELEVENLABS_API_KEY"]:
    if _key not in os.environ and hasattr(st, "secrets") and _key in st.secrets:
        os.environ[_key] = st.secrets[_key]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.agents import cleaner, validator, transformer, anomaly, summariser, pii_anonymiser
from src.pipeline import run_pipeline
from src.auth.credits import (
    get_or_create_user, get_credits, record_run, refresh_github_status, can_run,
    make_fingerprint, get_anon_runs, record_anon_run, FREE_ANON_RUNS,
)
from src.auth.github_api import get_repo_stats, validate_username, has_followed
from src.observability.store import init_db, save_run
from src.observability.tracer import RunTracer
from src.observability.guardrails import GuardrailEngine

st.set_page_config(
    page_title="Multi-Agent Pipeline · Britcore.AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Inter:wght@400;500;600;700;800;900&display=swap');

@keyframes pulse-live {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}
@keyframes float-up {
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0); }
}

html, body, [class*="css"], .stApp {
    background-color: #f8fafc !important;
    color: #0f172a !important;
    font-family: 'Inter', sans-serif !important;
}
header[data-testid="stHeader"] { display: none !important; }
section[data-testid="stSidebar"] { display: none !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* ── TOPBAR ─────────────────────────────────────────────── */
.topbar {
    background: #ffffff;
    border-bottom: 1px solid #e2e8f0;
    padding: 14px 48px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    min-height: 64px;
    box-shadow: 0 1px 12px rgba(0,0,0,0.06);
}
.pipe-title {
    font-family: 'Space Mono', monospace;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.07em;
    background: linear-gradient(90deg, #0ea5e9, #7c3aed);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.pipe-sub {
    font-size: 11px;
    color: #94a3b8;
    font-family: 'Space Mono', monospace;
    margin-top: 2px;
}
.live-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-radius: 20px;
    padding: 5px 12px;
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    color: #16a34a;
    font-weight: 700;
    letter-spacing: 0.06em;
}
.live-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: #16a34a;
    animation: pulse-live 1.8s ease-in-out infinite;
    display: inline-block;
}
.brand-right { display: flex; align-items: center; gap: 12px; }
.v-badge {
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    color: #7c3aed;
    background: #f5f3ff;
    border: 1px solid #ddd6fe;
    border-radius: 6px;
    padding: 3px 8px;
}

/* ── HERO ────────────────────────────────────────────────── */
.hero {
    padding: 52px 48px 40px;
    background: linear-gradient(135deg, #ffffff 0%, #f0f9ff 40%, #faf5ff 100%);
    border-bottom: 1px solid #e2e8f0;
    animation: float-up 0.4s ease-out;
}
.hero-inner {
    display: grid;
    grid-template-columns: 1fr 380px;
    gap: 48px;
    align-items: center;
}
.hero-eyebrow {
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.12em;
    color: #0ea5e9;
    text-transform: uppercase;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 10px;
}
.hero-eyebrow::before {
    content: '';
    display: inline-block;
    width: 24px; height: 2px;
    background: linear-gradient(90deg, #0ea5e9, transparent);
    border-radius: 2px;
}
.hero h1 {
    font-size: 50px;
    font-weight: 900;
    line-height: 1.1;
    letter-spacing: -0.03em;
    margin: 0 0 6px 0;
    color: #0f172a;
}
.hero h1 .grad {
    background: linear-gradient(135deg, #0ea5e9 0%, #7c3aed 55%, #db2777 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hero-sub {
    font-size: 15px;
    color: #475569;
    margin: 14px 0 26px;
    line-height: 1.65;
    max-width: 520px;
}
.hero-stats { display: flex; gap: 10px; flex-wrap: wrap; }
/* ── DASHBOARD PREVIEW CARD (hero right) ─────────────────── */
.dpcard {
    background: #ffffff;
    border: 1.5px solid #e2e8f0;
    border-radius: 20px;
    padding: 24px 24px 20px;
    box-shadow: 0 4px 24px rgba(14,165,233,0.10), 0 1px 4px rgba(0,0,0,0.06);
    position: relative;
    overflow: hidden;
}
.dpcard::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 4px;
    background: linear-gradient(90deg, #0ea5e9, #7c3aed, #db2777);
}
.dpcard-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 16px;
}
.dpcard-icon { font-size: 20px; }
.dpcard-title {
    font-size: 14px;
    font-weight: 800;
    color: #0f172a;
    flex: 1;
    letter-spacing: -0.01em;
}
.dpcard-live {
    font-family: 'Space Mono', monospace;
    font-size: 9px;
    font-weight: 700;
    background: #dcfce7;
    color: #16a34a;
    padding: 3px 8px;
    border-radius: 20px;
    letter-spacing: 0.08em;
}
.dpcard-feat {
    display: flex;
    align-items: flex-start;
    gap: 9px;
    padding: 8px 10px;
    border-radius: 9px;
    margin-bottom: 5px;
    background: #f8fafc;
    border: 1px solid #f1f5f9;
    font-size: 12px;
    color: #374151;
    line-height: 1.4;
}
.dpcard-feat-icon {
    font-size: 14px;
    flex-shrink: 0;
    margin-top: 1px;
}
.dpcard-feat-name { font-weight: 700; color: #0f172a; font-size: 12px; }
.dpcard-feat-desc { color: #64748b; font-size: 11px; }
.dpcard-lock {
    margin-top: 14px;
    background: linear-gradient(135deg, #fffbeb, #fef3c7);
    border: 1.5px solid #fcd34d;
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 11.5px;
    color: #92400e;
    font-weight: 600;
    display: flex;
    align-items: flex-start;
    gap: 8px;
    line-height: 1.5;
}
.dpcard-btn {
    display: block;
    margin-top: 14px;
    background: linear-gradient(135deg, #0ea5e9, #7c3aed);
    color: #ffffff !important;
    text-decoration: none;
    border-radius: 10px;
    padding: 11px 18px;
    font-size: 13px;
    font-weight: 700;
    text-align: center;
    letter-spacing: -0.01em;
    transition: opacity 0.15s;
}
.dpcard-btn:hover { opacity: 0.88; color: #ffffff !important; text-decoration: none; }
.stat-pill {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    padding: 7px 14px;
    border-radius: 10px;
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    font-weight: 700;
}
.stat-pill.blue   { background: #eff6ff;  border: 1px solid #bfdbfe; color: #1d4ed8; }
.stat-pill.purple { background: #f5f3ff;  border: 1px solid #ddd6fe; color: #6d28d9; }
.stat-pill.green  { background: #f0fdf4;  border: 1px solid #bbf7d0; color: #15803d; }
.stat-pill.amber  { background: #fffbeb;  border: 1px solid #fde68a; color: #b45309; }

/* ── AGENT CARDS ─────────────────────────────────────────── */
.agents-strip {
    display: grid;
    grid-template-columns: repeat(6, minmax(0, 1fr));
    gap: 14px;
    padding: 28px 48px;
    background: #f8fafc;
    border-bottom: 1px solid #e2e8f0;
}
.agents-title {
    grid-column: 1 / -1;
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.1em;
    color: #94a3b8;
    text-transform: uppercase;
    margin-bottom: 4px;
}
.ac {
    background: #ffffff;
    border-radius: 16px;
    padding: 20px 14px 18px;
    text-align: center;
    border: 1px solid #e2e8f0;
    box-shadow: 0 1px 8px rgba(0,0,0,0.05);
    transition: transform 0.2s, box-shadow 0.2s;
    position: relative;
    overflow: hidden;
}
.ac::after {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: var(--ac-color);
    border-radius: 16px 16px 0 0;
}
.ac:hover { transform: translateY(-4px); box-shadow: 0 8px 28px rgba(0,0,0,0.10); }

.ac-num {
    font-family: 'Space Mono', monospace;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.1em;
    color: var(--ac-color);
    margin-bottom: 10px;
    opacity: 0.8;
}
.ac-icon { font-size: 28px; margin-bottom: 10px; display: block; }
.ac-name {
    font-family: 'Space Mono', monospace;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.08em;
    color: var(--ac-color);
    text-transform: uppercase;
    margin-bottom: 6px;
}
.ac-desc { font-size: 11px; color: #64748b; line-height: 1.5; }
.ac-model {
    margin-top: 10px;
    font-family: 'Space Mono', monospace;
    font-size: 8px;
    color: var(--ac-color);
    background: var(--ac-bg);
    border: 1px solid var(--ac-border);
    border-radius: 5px;
    padding: 2px 7px;
    display: inline-block;
    letter-spacing: 0.06em;
    font-weight: 700;
}

.ac:nth-child(2) { --ac-color:#0ea5e9; --ac-bg:#eff6ff; --ac-border:#bfdbfe; }
.ac:nth-child(3) { --ac-color:#d97706; --ac-bg:#fffbeb; --ac-border:#fde68a; }
.ac:nth-child(4) { --ac-color:#7c3aed; --ac-bg:#f5f3ff; --ac-border:#ddd6fe; }
.ac:nth-child(5) { --ac-color:#059669; --ac-bg:#f0fdf4; --ac-border:#bbf7d0; }
.ac:nth-child(6) { --ac-color:#e11d48; --ac-bg:#fff1f2; --ac-border:#fecdd3; }
.ac:nth-child(7) { --ac-color:#9333ea; --ac-bg:#faf5ff; --ac-border:#e9d5ff; }

/* ── SECTION LABELS ──────────────────────────────────────── */
.section-pad { padding: 28px 48px; }
.section-label {
    display: flex;
    align-items: center;
    gap: 10px;
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 18px;
}
.section-label::before {
    content: '';
    display: inline-block;
    width: 3px; height: 14px;
    background: linear-gradient(180deg, #0ea5e9, #7c3aed);
    border-radius: 2px;
}

/* ── METRICS ─────────────────────────────────────────────── */
div[data-testid="metric-container"] {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 14px !important;
    padding: 20px !important;
    box-shadow: 0 1px 8px rgba(0,0,0,0.05) !important;
}
div[data-testid="metric-container"] label {
    color: #64748b !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 10px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}
div[data-testid="stMetricValue"] {
    color: #0ea5e9 !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 28px !important;
    font-weight: 700 !important;
}

/* ── INPUTS ──────────────────────────────────────────────── */
.stTextInput > div > div > input {
    background: #ffffff !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 10px !important;
    color: #0f172a !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 12px !important;
}
.stTextInput > div > div > input:focus {
    border-color: #0ea5e9 !important;
    box-shadow: 0 0 0 3px rgba(14,165,233,0.15) !important;
}
.stSelectbox > div > div {
    background: #ffffff !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 10px !important;
    color: #0f172a !important;
}

/* ── RUN BUTTON ──────────────────────────────────────────── */
.stButton > button {
    background: linear-gradient(135deg, #0ea5e9, #7c3aed) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 12px !important;
    font-family: 'Space Mono', monospace !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    letter-spacing: 0.06em !important;
    padding: 14px 28px !important;
    width: 100% !important;
    box-shadow: 0 4px 14px rgba(14,165,233,0.35) !important;
    transition: box-shadow 0.2s, transform 0.15s !important;
}
.stButton > button:hover {
    box-shadow: 0 6px 22px rgba(14,165,233,0.45) !important;
    transform: translateY(-1px) !important;
}

/* ── TABS ────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: #ffffff !important;
    border-bottom: 1px solid #e2e8f0 !important;
    border-radius: 10px 10px 0 0 !important;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Space Mono', monospace !important;
    font-size: 11px !important;
    color: #64748b !important;
    background: transparent !important;
    padding: 10px 18px !important;
}
.stTabs [aria-selected="true"] {
    color: #0ea5e9 !important;
    border-bottom: 2px solid #0ea5e9 !important;
}
.stTabs [data-baseweb="tab-panel"] {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-top: none !important;
    border-radius: 0 0 12px 12px !important;
    padding: 20px !important;
}

/* ── TOGGLE ──────────────────────────────────────────────── */
.stToggle > label { color: #475569 !important; font-size: 13px !important; }

/* ── PROGRESS ────────────────────────────────────────────── */
.stProgress > div > div > div {
    background: linear-gradient(90deg, #0ea5e9, #7c3aed) !important;
}

/* ── DATAFRAME ───────────────────────────────────────────── */
.stDataFrame { border: 1px solid #e2e8f0 !important; border-radius: 10px !important; }

/* ── CONN FORM ───────────────────────────────────────────── */
.conn-form {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: 0 1px 8px rgba(0,0,0,0.05);
}
.conn-form-title {
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    background: linear-gradient(90deg, #0ea5e9, #7c3aed);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 16px;
}

/* ── FOOTER ──────────────────────────────────────────────── */
.footer {
    padding: 20px 48px;
    border-top: 1px solid #e2e8f0;
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #ffffff;
    margin-top: 40px;
}
.footer-left {
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    background: linear-gradient(90deg, #0ea5e9, #7c3aed);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    display: flex;
    align-items: center;
    gap: 8px;
}
.footer-dot { width: 7px; height: 7px; border-radius: 50%; background: #16a34a; display: inline-block; animation: pulse-live 2s ease-in-out infinite; }
.footer-right { font-family: 'Space Mono', monospace; font-size: 10px; color: #94a3b8; }
.footer-right span { color: #7c3aed; }

/* ── DASHBOARD PROMO ─────────────────────────────────────── */
.dash-promo {
    background: linear-gradient(135deg, #f0f9ff 0%, #f5f3ff 100%);
    border: 1px solid #bfdbfe;
    border-left: 4px solid #0ea5e9;
    border-radius: 14px;
    padding: 20px 24px;
    margin: 24px 0 8px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;
}
.dash-promo-left { flex: 1; }
.dash-promo-title { font-size: 15px; font-weight: 800; color: #0f172a; margin-bottom: 4px; }
.dash-promo-sub   { font-size: 12px; color: #475569; line-height: 1.5; }
.dash-feature-pills { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 10px; }
.dash-pill {
    font-family: 'Space Mono', monospace;
    font-size: 9px;
    font-weight: 700;
    padding: 3px 9px;
    border-radius: 5px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    color: #475569;
}

/* ── COMPARE NOTE ────────────────────────────────────────── */
.compare-note {
    background: linear-gradient(135deg, #f0fdf4 0%, #f0f9ff 100%);
    border: 2px solid #34d399;
    border-radius: 16px;
    padding: 24px 28px;
    margin-bottom: 24px;
}
.compare-note-header { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.compare-note-title  { font-size: 17px; font-weight: 900; color: #065f46; letter-spacing: -0.01em; }
.compare-note-sub    { font-size: 13px; color: #047857; margin-bottom: 16px; line-height: 1.6; }
.dash-features-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    margin-bottom: 16px;
}
.dash-feat-card {
    background: #ffffff;
    border: 1px solid #d1fae5;
    border-radius: 10px;
    padding: 12px 14px;
}
.dash-feat-icon  { font-size: 18px; margin-bottom: 4px; }
.dash-feat-name  { font-size: 12px; font-weight: 700; color: #065f46; margin-bottom: 2px; }
.dash-feat-desc  { font-size: 11px; color: #6b7280; line-height: 1.4; }

/* ── MODE SELECTOR ───────────────────────────────────────── */
.mode-selector {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
    margin-bottom: 8px;
}
.mode-card {
    border-radius: 16px;
    padding: 20px 22px;
    border: 2px solid #e2e8f0;
    background: #ffffff;
    cursor: pointer;
    transition: all 0.2s;
    position: relative;
    overflow: hidden;
}
.mode-card.active-baseline {
    border-color: #0ea5e9;
    background: linear-gradient(135deg, #f0f9ff, #ffffff);
    box-shadow: 0 4px 20px rgba(14,165,233,0.15);
}
.mode-card.active-router {
    border-color: #7c3aed;
    background: linear-gradient(135deg, #f5f3ff, #ffffff);
    box-shadow: 0 4px 20px rgba(124,58,237,0.15);
}
.mode-card-badge {
    display: inline-block;
    font-family: 'Space Mono', monospace;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 3px 8px;
    border-radius: 6px;
    margin-bottom: 10px;
}
.badge-baseline { background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; }
.badge-router   { background: #f5f3ff; color: #6d28d9; border: 1px solid #ddd6fe; }
.badge-selected { background: #dcfce7; color: #15803d; border: 1px solid #bbf7d0; }
.mode-card-title { font-size: 17px; font-weight: 800; color: #0f172a; margin-bottom: 6px; letter-spacing: -0.01em; }
.mode-card-sub   { font-size: 12px; color: #64748b; margin-bottom: 14px; line-height: 1.5; }
.mode-stats { display: flex; gap: 10px; flex-wrap: wrap; }
.mode-stat {
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    font-weight: 700;
    padding: 4px 10px;
    border-radius: 6px;
}
.stat-cost-high { background:#fff1f2; color:#be123c; border:1px solid #fecdd3; }
.stat-cost-low  { background:#f0fdf4; color:#15803d; border:1px solid #bbf7d0; }
.stat-speed-slow{ background:#fffbeb; color:#b45309; border:1px solid #fde68a; }
.stat-speed-fast{ background:#f0fdf4; color:#15803d; border:1px solid #bbf7d0; }
.stat-model     { background:#f8fafc; color:#475569; border:1px solid #e2e8f0; }
.selected-tick {
    position: absolute;
    top: 14px; right: 16px;
    width: 22px; height: 22px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 12px;
}
.tick-baseline { background:#0ea5e9; color:#fff; }
.tick-router   { background:#7c3aed; color:#fff; }

/* ── GITHUB TIERS ────────────────────────────────────────── */
.tier-section {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 18px;
    padding: 24px 26px;
    margin-bottom: 20px;
    box-shadow: 0 1px 8px rgba(0,0,0,0.05);
}
.tier-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 18px;
}
.tier-title {
    font-size: 15px;
    font-weight: 800;
    color: #0f172a;
    letter-spacing: -0.01em;
}
.tier-subtitle { font-size: 12px; color: #64748b; margin-top: 2px; }
.repo-stats { display: flex; gap: 10px; }
.repo-stat {
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    padding: 5px 12px;
    border-radius: 8px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    color: #475569;
}
.tier-cards { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; }
.tier-card {
    border-radius: 14px;
    padding: 18px 16px;
    border: 1px solid #e2e8f0;
    background: #f8fafc;
    text-align: center;
    position: relative;
}
.tier-card.tier-free     { border-color: #bfdbfe; background: #eff6ff; }
.tier-card.tier-star     { border-color: #fde68a; background: #fffbeb; }
.tier-card.tier-lifetime { border-color: #ddd6fe; background: #f5f3ff; }
.tier-icon  { font-size: 28px; margin-bottom: 8px; }
.tier-name  { font-family: 'Space Mono', monospace; font-size: 10px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 4px; }
.tier-free .tier-name     { color: #1d4ed8; }
.tier-star .tier-name     { color: #b45309; }
.tier-lifetime .tier-name { color: #6d28d9; }
.tier-runs  { font-size: 26px; font-weight: 900; letter-spacing: -0.03em; margin: 6px 0 4px; }
.tier-free .tier-runs     { color: #1d4ed8; }
.tier-star .tier-runs     { color: #b45309; }
.tier-lifetime .tier-runs { color: #6d28d9; }
.tier-desc  { font-size: 11px; color: #64748b; line-height: 1.5; }
.tier-action {
    display: inline-block;
    margin-top: 10px;
    font-family: 'Space Mono', monospace;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    padding: 4px 10px;
    border-radius: 6px;
    text-decoration: none;
}
.tier-free .tier-action     { background:#dbeafe; color:#1d4ed8; }
.tier-star .tier-action     { background:#fef3c7; color:#b45309; }
.tier-lifetime .tier-action { background:#ede9fe; color:#6d28d9; }

/* ── BYOK CARD ───────────────────────────────────────────── */
.byok-card {
    border-radius: 16px;
    padding: 22px 24px;
    background: linear-gradient(135deg, #fefce8, #fffbeb);
    border: 2px solid #fbbf24;
    box-shadow: 0 4px 20px rgba(251,191,36,0.15);
    margin-bottom: 20px;
}
.byok-header { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
.byok-title  { font-size: 16px; font-weight: 800; color: #78350f; letter-spacing: -0.01em; }
.byok-sub    { font-size: 12px; color: #92400e; margin-bottom: 14px; line-height: 1.5; }
.byok-tag {
    display: inline-block;
    font-family: 'Space Mono', monospace;
    font-size: 9px;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 5px;
    background: #fef3c7;
    border: 1px solid #fde68a;
    color: #92400e;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
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
""", unsafe_allow_html=True)

st.markdown("""
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
""", unsafe_allow_html=True)

st.markdown("""
<div class="agents-strip">
    <div class="agents-title">Pipeline Agents — Wave 1 runs in parallel · Wave 2 synthesises</div>
    <div class="ac"><div class="ac-num">01 · WAVE 1</div><div class="ac-icon">🧹</div><div class="ac-name">Cleaner</div><div class="ac-desc">Fixes nulls, date formats & inconsistencies across all rows</div><div class="ac-model">Haiku · Fast</div></div>
    <div class="ac"><div class="ac-num">02 · WAVE 1</div><div class="ac-icon">🔒</div><div class="ac-name">PII Anonymiser</div><div class="ac-desc">Masks emails, phones, postcodes & card numbers</div><div class="ac-model">Regex · Free</div></div>
    <div class="ac"><div class="ac-num">03 · WAVE 1</div><div class="ac-icon">🛡️</div><div class="ac-name">Validator</div><div class="ac-desc">Checks schema, data types & completeness score</div><div class="ac-model">Sonnet · Quality</div></div>
    <div class="ac"><div class="ac-num">04 · WAVE 1</div><div class="ac-icon">⚡</div><div class="ac-name">Transformer</div><div class="ac-desc">Derives new columns & standardises values</div><div class="ac-model">Haiku · Fast</div></div>
    <div class="ac"><div class="ac-num">05 · WAVE 1</div><div class="ac-icon">📡</div><div class="ac-name">Anomaly Detector</div><div class="ac-desc">Finds outliers, impossible values & suspicious patterns</div><div class="ac-model">Sonnet · Quality</div></div>
    <div class="ac"><div class="ac-num">06 · WAVE 2</div><div class="ac-icon">📊</div><div class="ac-name">Summariser</div><div class="ac-desc">Generates business insights & recommendations from all agents</div><div class="ac-model">Sonnet · Quality</div></div>
</div>
""", unsafe_allow_html=True)

mode = st.radio(
    "Mode",
    ["📄 CSV Pipeline", "📑 PDF Intelligence", "🔌 Database Connectors"],
    horizontal=True,
    label_visibility="collapsed"
)

st.markdown('<div style="height:1px;background:linear-gradient(90deg,transparent,rgba(56,189,248,0.2),transparent);margin:0 48px;"></div>', unsafe_allow_html=True)

def _display_result_tabs(result):
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


def _display_cost_card(result, label: str):
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


def _comparison_table(baseline, routed):
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

init_db()

# ── IP FINGERPRINT + VPN BLOCK ───────────────────────────────────────────────
def _get_client_ip() -> str:
    try:
        headers = st.context.headers
        return (
            headers.get("x-forwarded-for", "").split(",")[0].strip()
            or headers.get("x-real-ip", "")
            or ""
        )
    except Exception:
        return ""

def _is_vpn(ip: str) -> bool:
    """Check ip-api.com free endpoint. Returns True if proxy/VPN/datacenter."""
    if not ip or ip in ("127.0.0.1", "::1", "localhost") or ip.startswith("192.168.") or ip.startswith("10."):
        return False
    if st.session_state.get("vpn_checked_ip") == ip:
        return st.session_state.get("vpn_result", False)
    try:
        import requests as _req
        r = _req.get(
            f"https://ip-api.com/json/{ip}?fields=status,proxy,hosting",
            timeout=3
        )
        if r.status_code == 200:
            data = r.json()
            result = data.get("proxy", False) or data.get("hosting", False)
        else:
            result = False
    except Exception:
        result = False
    st.session_state["vpn_checked_ip"] = ip
    st.session_state["vpn_result"] = result
    return result

def _get_fingerprint() -> str:
    if "visitor_fp" not in st.session_state:
        try:
            headers = st.context.headers
            ip = _get_client_ip() or headers.get("host", "local")
            ua = headers.get("user-agent", "unknown")
        except Exception:
            ip, ua = "local", "unknown"
        st.session_state["visitor_fp"] = make_fingerprint(ip, ua)
    return st.session_state["visitor_fp"]

_CLIENT_IP  = _get_client_ip()

# Block VPN/proxy users at startup
if _is_vpn(_CLIENT_IP):
    st.markdown("""
<style>
html,body,[class*="css"],.stApp{background:#0f172a!important;}
.vpn-block{max-width:480px;margin:120px auto;background:#1e293b;border:1.5px solid #ef4444;
border-radius:20px;padding:40px 36px;text-align:center;}
.vpn-title{font-size:22px;font-weight:900;color:#f8fafc;margin:16px 0 10px;}
.vpn-sub{font-size:14px;color:#94a3b8;line-height:1.6;}
</style>
<div class="vpn-block">
<div style="font-size:48px;">🚫</div>
<div class="vpn-title">VPN / Proxy Detected</div>
<div class="vpn-sub">This demo is not available over VPN or proxy connections.<br>
Please disable your VPN and reload the page.</div>
</div>
""", unsafe_allow_html=True)
    st.stop()

VISITOR_FP = _get_fingerprint()

# ── SHARED AUTH HELPER ────────────────────────────────────────────────────────
def _auth_section(tab_prefix: str):
    """
    Renders GitHub credits + BYOK block. Shares session_state so the user only
    verifies once — switching tabs keeps them logged in.
    Returns (active_user: str, byok_key: str, credits_info: dict | None)
    """
    try:
        stats = get_repo_stats()
        stars_txt = f"⭐ {stats['stars']} stars"
        forks_txt = f"🍴 {stats['forks']} forks"
    except Exception:
        stars_txt, forks_txt = "⭐ Stars", "🍴 Forks"

    st.markdown(f"""
<div class="tier-section">
<div class="tier-header">
<div>
<div class="tier-title">Free to use &mdash; earn more runs on GitHub</div>
<div class="tier-subtitle">Enter your GitHub username to activate credits &middot; no sign-up required &middot; works across all modes</div>
</div>
<div class="repo-stats">
<span class="repo-stat">{stars_txt}</span>
<span class="repo-stat">{forks_txt}</span>
</div>
</div>
<div class="tier-cards">
<div class="tier-card tier-free">
<div class="tier-icon">&#128483;</div>
<div class="tier-name">Free</div>
<div class="tier-runs">2 runs</div>
<div class="tier-desc">Just enter your GitHub username below. Works for CSV, PDF &amp; Database modes.</div>
<span class="tier-action">Enter username &rarr;</span>
</div>
<div class="tier-card tier-star">
<div class="tier-icon">&#11088;</div>
<div class="tier-name">Star + Follow</div>
<div class="tier-runs">+3 runs</div>
<div class="tier-desc">Star the repo &amp; follow @harshitboots on GitHub to get 5 total runs.</div>
<a class="tier-action" href="https://github.com/harshitboots/multi-agent-data-pipeline" target="_blank">Star on GitHub &rarr;</a>
</div>
<div class="tier-card tier-lifetime">
<div class="tier-icon">&#9854;</div>
<div class="tier-name">Lifetime</div>
<div class="tier-runs">Unlimited</div>
<div class="tier-desc">Fork the repo + follow @harshitboots. Every new version is yours forever.</div>
<a class="tier-action" href="https://github.com/harshitboots/multi-agent-data-pipeline/fork" target="_blank">Fork the repo &rarr;</a>
</div>
</div>
</div>
""", unsafe_allow_html=True)

    gh_col, status_col = st.columns([1, 1])
    with gh_col:
        github_username = st.text_input(
            "Your GitHub username",
            placeholder="e.g. harshitboots",
            key="gh_user",
            label_visibility="visible",
            value=st.session_state.get("github_user", ""),
        )
        if github_username and st.button("Verify & Check Credits", key=f"{tab_prefix}_check_credits", use_container_width=True):
            with st.spinner("Checking GitHub..."):
                if validate_username(github_username):
                    refresh_github_status(github_username)
                    st.session_state["github_user"] = github_username
                    st.success("GitHub verified ✓")
                else:
                    st.error("GitHub username not found")

    active_user = st.session_state.get("github_user", github_username or "")
    byok_key = ""
    credits_info = None

    if active_user:
        credits_info = get_credits(active_user)
        with status_col:
            if credits_info["lifetime"]:
                st.success("♾️ **Lifetime access** — Fork + Follow verified. Unlimited runs.")
            elif credits_info["remaining_free"] > 0:
                bars = "🟢" * credits_info["remaining_free"] + "⚪" * (credits_info["max_free_runs"] - credits_info["remaining_free"])
                st.info(
                    f"**{credits_info['remaining_free']} run(s) remaining** {bars}\n\n"
                    f"{credits_info['runs_used']} of {credits_info['max_free_runs']} used · "
                    + ("⭐ Star bonus active" if credits_info["has_starred"] else "⭐ Star to get +3 runs")
                )
            else:
                st.warning("Free runs used — add your API key below or fork the repo for lifetime access")

            if credits_info["has_starred"] and not credits_info["has_followed"]:
                st.info("💡 Also follow @harshitboots to unlock the +3 star bonus")

    st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)

    show_byok = (credits_info and credits_info["needs_byok"]) or st.checkbox(
        "I want to use my own Anthropic API key", key=f"{tab_prefix}_show_byok"
    )
    if show_byok:
        st.markdown("""
<div class="byok-card">
<div class="byok-header">
<span style="font-size:22px;">&#128273;</span>
<span class="byok-title">Bring Your Own Key</span>
<span class="byok-tag">Unlimited Runs</span>
</div>
<div class="byok-sub">
Paste your Anthropic API key below to run with no credit limits.<br>
<strong>Your key is never stored</strong> &mdash; it lives only in this browser session and is gone when you close the tab.
</div>
</div>
""", unsafe_allow_html=True)
        byok_key = st.text_input(
            "Anthropic API key (sk-ant-...)",
            type="password",
            placeholder="sk-ant-api03-...",
            key=f"{tab_prefix}_byok_key",
            help="Get your key at console.anthropic.com — session only, never saved",
        )
        if byok_key:
            st.session_state["byok_api_key"] = byok_key
            st.success("🔑 Key loaded — you have unlimited runs this session")
    else:
        byok_key = st.session_state.get("byok_api_key", "")

    return active_user, byok_key, credits_info


def _check_can_run(active_user: str, byok_key: str) -> tuple[bool, str]:
    """Returns (ok, mode). Allows 2 anonymous runs per device before requiring GitHub or BYOK."""
    if byok_key:
        return True, "byok"
    if active_user:
        return can_run(active_user, None)
    used = get_anon_runs(VISITOR_FP)
    if used < FREE_ANON_RUNS:
        return True, "anon"
    return False, "no_credits"

def _record_run_anon_or_user(active_user: str, run_mode: str):
    if run_mode == "anon":
        record_anon_run(VISITOR_FP)
    elif active_user and run_mode == "free":
        record_run(active_user)

def _anon_credit_banner():
    used = get_anon_runs(VISITOR_FP)
    remaining = max(0, FREE_ANON_RUNS - used)
    if remaining > 0:
        bars = "🟢" * remaining + "⚪" * (FREE_ANON_RUNS - remaining)
        st.info(f"**{remaining} free run(s) remaining** {bars} — No login needed. Enter your GitHub username above to unlock more.")
    else:
        st.warning("Free runs used — enter your GitHub username above to get more, or add your Anthropic API key.")


if mode == "📄 CSV Pipeline":
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
    active_user, byok_key, credits_info = _auth_section("csv")

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
        _anon_credit_banner()

    if df is not None:
        run_btn_label = f"▶ Run Pipeline — {mode_label}"
        if st.button(run_btn_label, use_container_width=True):
            run_ok, run_mode = _check_can_run(active_user, byok_key)
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

                _record_run_anon_or_user(active_user, run_mode)

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
                _display_result_tabs(result)

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

elif mode == "📑 PDF Intelligence":
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
    pdf_active_user, pdf_byok_key, pdf_credits_info = _auth_section("pdf")
    if not pdf_active_user:
        _anon_credit_banner()

    # ── PDF UPLOAD ───────────────────────────────────────────
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
                run_key    = "run_pdf_routed"
            else:
                m_parser = m_entity = m_risk = m_action = m_summary = SONNET
                mode_label = "Without Router (Baseline)"
                run_key    = "run_pdf_baseline"

            if st.button(f"▶ Run PDF Pipeline — {mode_label}", use_container_width=True, type="primary"):
                run_ok, run_mode = _check_can_run(pdf_active_user, pdf_byok_key)
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
                _record_run_anon_or_user(pdf_active_user, run_mode)

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
        db_active_user, db_byok_key, db_credits_info = _auth_section("db")
        if not db_active_user:
            _anon_credit_banner()

        st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)

        if st.button(f"▶ Run Pipeline on DB Data — {db_mode_label}", use_container_width=True, type="primary"):
            run_ok, run_mode = _check_can_run(db_active_user, db_byok_key)
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
                _record_run_anon_or_user(db_active_user, run_mode)
                st.success(f"Done — GBP {result.total_cost_gbp:.5f} · {result.total_latency_ms}ms")
                _display_result_tabs(result)

    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("""
<div class="footer">
    <div class="footer-left">
        <span class="footer-dot"></span>
        Multi-Agent Data Pipeline · Open Source · github.com/harshitboots
    </div>
    <div class="footer-right">v2.0.0 · <span>MIT License</span></div>
</div>
""", unsafe_allow_html=True)
