import streamlit as st
import os
import sys

from dotenv import load_dotenv

load_dotenv()

# Load secrets from Streamlit Cloud if running in cloud environment
for _key in ["ANTHROPIC_API_KEY", "ELEVENLABS_API_KEY"]:
    if _key not in os.environ:
        try:
            if _key in st.secrets:
                os.environ[_key] = st.secrets[_key]
        except Exception:
            pass  # No secrets.toml file — rely on env vars or .env
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.observability.store import init_db
from src.ui.styles import MAIN_CSS
from src.ui.layout import render_topbar, render_hero, render_agents_strip, render_footer
from src.ui.auth import get_client_ip, is_vpn, get_fingerprint, render_vpn_block

st.set_page_config(
    page_title="Multi-Agent Pipeline · Britcore.AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown(MAIN_CSS, unsafe_allow_html=True)
render_topbar()
render_hero()
render_agents_strip()

mode = st.radio(
    "Mode",
    ["📄 CSV Pipeline", "📑 PDF Intelligence", "🔌 Database Connectors"],
    horizontal=True,
    label_visibility="collapsed"
)

st.markdown('<div style="height:1px;background:linear-gradient(90deg,transparent,rgba(56,189,248,0.2),transparent);margin:0 48px;"></div>', unsafe_allow_html=True)

init_db()

# ── IP FINGERPRINT + VPN BLOCK ───────────────────────────────────────────────
_CLIENT_IP = get_client_ip()

if is_vpn(_CLIENT_IP):
    render_vpn_block()

VISITOR_FP = get_fingerprint()

# ── PAGE DISPATCH ────────────────────────────────────────────────────────────
if mode == "📄 CSV Pipeline":
    from src.pages.csv_pipeline import render
    render(VISITOR_FP)

elif mode == "📑 PDF Intelligence":
    from src.pages.pdf_intelligence import render
    render(VISITOR_FP)

elif mode == "🔌 Database Connectors":
    from src.pages.db_connectors import render
    render(VISITOR_FP)

render_footer()
