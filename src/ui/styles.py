"""All CSS styles for the Multi-Agent Data Pipeline app."""

MAIN_CSS = """
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
"""
