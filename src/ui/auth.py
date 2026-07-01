"""Authentication, credits, VPN detection, and fingerprinting helpers."""

import streamlit as st

from src.auth.credits import (
    get_or_create_user, get_credits, record_run, refresh_github_status, can_run,
    make_fingerprint, get_anon_runs, record_anon_run, FREE_ANON_RUNS,
)
from src.auth.github_api import get_repo_stats, validate_username, has_followed


def get_client_ip() -> str:
    try:
        headers = st.context.headers
        return (
            headers.get("x-forwarded-for", "").split(",")[0].strip()
            or headers.get("x-real-ip", "")
            or ""
        )
    except Exception:
        return ""


def is_vpn(ip: str) -> bool:
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


def get_fingerprint() -> str:
    if "visitor_fp" not in st.session_state:
        try:
            headers = st.context.headers
            ip = get_client_ip() or headers.get("host", "local")
            ua = headers.get("user-agent", "unknown")
        except Exception:
            ip, ua = "local", "unknown"
        st.session_state["visitor_fp"] = make_fingerprint(ip, ua)
    return st.session_state["visitor_fp"]


def render_vpn_block():
    """Render VPN block message and stop the app."""
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


def auth_section(tab_prefix: str):
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


def check_can_run(active_user: str, byok_key: str, visitor_fp: str) -> tuple[bool, str]:
    """Returns (ok, mode). Allows 2 anonymous runs per device before requiring GitHub or BYOK."""
    if byok_key:
        return True, "byok"
    if active_user:
        return can_run(active_user, None)
    used = get_anon_runs(visitor_fp)
    if used < FREE_ANON_RUNS:
        return True, "anon"
    return False, "no_credits"


def record_run_anon_or_user(active_user: str, run_mode: str, visitor_fp: str):
    if run_mode == "anon":
        record_anon_run(visitor_fp)
    elif active_user and run_mode == "free":
        record_run(active_user)


def anon_credit_banner(visitor_fp: str):
    used = get_anon_runs(visitor_fp)
    remaining = max(0, FREE_ANON_RUNS - used)
    if remaining > 0:
        bars = "🟢" * remaining + "⚪" * (FREE_ANON_RUNS - remaining)
        st.info(f"**{remaining} free run(s) remaining** {bars} — No login needed. Enter your GitHub username above to unlock more.")
    else:
        st.warning("Free runs used — enter your GitHub username above to get more, or add your Anthropic API key.")
