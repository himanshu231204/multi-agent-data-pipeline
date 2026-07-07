"""Generate a formatted PDF report from PDF pipeline analysis results."""
from fpdf import FPDF
from datetime import datetime
import io


# ── Latin-1 sanitiser ─────────────────────────────────────────────────────────
_UNICODE_SUBS = {
    '—': '-',    # em dash
    '–': '-',    # en dash
    '‘': "'",    # left single quote
    '’': "'",    # right single quote
    '“': '"',    # left double quote
    '”': '"',    # right double quote
    '•': '*',    # bullet
    '‣': '*',    # triangular bullet
    '…': '...',  # horizontal ellipsis
    ' ': ' ',    # non-breaking space
    '·': '.',    # middle dot
}

def _safe(text) -> str:
    """Replace non-Latin-1 chars so Helvetica core font renders without error."""
    if not isinstance(text, str):
        text = str(text)
    for ch, rep in _UNICODE_SUBS.items():
        text = text.replace(ch, rep)
    return text.encode('latin-1', errors='replace').decode('latin-1')


# ── Colours ───────────────────────────────────────────────────────────────────
NAVY   = (13,  27,  62)
PURPLE = (107, 63, 160)
WHITE  = (255, 255, 255)
LIGHT  = (248, 250, 252)
MUTED  = (100, 116, 139)
RED    = (220,  38,  38)
AMBER  = (217, 119,   6)
GREEN  = ( 22, 163,  74)
DARK   = ( 15,  23,  42)


class ReportPDF(FPDF):
    def __init__(self, title: str, mode: str):
        super().__init__()
        self.title_text = title
        self.mode_text  = mode
        self.set_auto_page_break(auto=True, margin=18)
        self.set_margins(18, 18, 18)

    # Auto-sanitise every text string so Helvetica (Latin-1) never chokes
    def cell(self, *args, **kwargs):
        args = list(args)
        if len(args) > 2:
            args[2] = _safe(args[2])
        elif 'txt' in kwargs:
            kwargs['txt'] = _safe(kwargs['txt'])
        return super().cell(*args, **kwargs)

    def multi_cell(self, *args, **kwargs):
        args = list(args)
        if len(args) > 2:
            args[2] = _safe(args[2])
        elif 'txt' in kwargs:
            kwargs['txt'] = _safe(kwargs['txt'])
        return super().multi_cell(*args, **kwargs)

    def header(self):
        self.set_fill_color(*NAVY)
        self.rect(0, 0, 210, 12, "F")
        self.set_fill_color(*PURPLE)
        self.rect(0, 12, 210, 3, "F")
        self.set_xy(self.l_margin, 18)

    def footer(self):
        self.set_y(-14)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*MUTED)
        self.cell(0, 8,
                  f"Multi-Agent Data Pipeline  ·  Generated {datetime.utcnow().strftime('%d %b %Y %H:%M')} UTC  ·  Page {self.page_no()}",
                  align="C")

    # ── Helpers ───────────────────────────────────────────────────────────────
    def cover_block(self, pages: int, words: int, mode: str, models: dict):
        self.set_xy(self.l_margin, 22)
        # Title
        self.set_font("Helvetica", "B", 22)
        self.set_text_color(*NAVY)
        self.cell(0, 10, "PDF Intelligence Report", ln=True)
        self.set_font("Helvetica", "", 11)
        self.set_text_color(*MUTED)
        self.cell(0, 7, f"Mode: {mode}  ·  {pages} pages  ·  {words:,} words", ln=True)
        self.cell(0, 6, f"Generated: {datetime.utcnow().strftime('%d %b %Y, %H:%M UTC')}", ln=True)
        self.ln(4)
        # Model pills row
        model_labels = {
            "pdf_parser":      ("PDF Parser",       models.get("parser", "")),
            "entity_extractor":("Entity Extractor", models.get("entity", "")),
            "risk_detector":   ("Risk Detector",    models.get("risk",   "")),
            "action_extractor":("Action Extractor", models.get("action", "")),
            "summariser":      ("Summariser",        models.get("summary", "")),
        }
        self.set_font("Helvetica", "B", 8)
        for agent, (label, m) in model_labels.items():
            is_haiku = "haiku" in m.lower()
            self.set_fill_color(*(224, 242, 254) if is_haiku else (237, 233, 254))
            self.set_text_color(*(14, 116, 144) if is_haiku else (109, 40, 217))
            self.cell(33, 6, f"{label}: {'Haiku' if is_haiku else 'Sonnet'}", border=0, fill=True)
            self.cell(1, 6, "")
        self.ln(10)
        self.set_draw_color(*PURPLE)
        self.set_line_width(0.4)
        self.line(18, self.get_y(), 192, self.get_y())
        self.ln(6)

    def section_heading(self, text: str, color=NAVY):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*color)
        self.set_fill_color(*LIGHT)
        self.cell(0, 9, f"  {text}", ln=True, fill=True)
        self.ln(2)

    def kv(self, key: str, value: str, bold_val: bool = False):
        val_w = self.w - self.l_margin - self.r_margin - 45  # 129 mm
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*MUTED)
        self.cell(45, 6, key.upper())
        self.set_font("Helvetica", "B" if bold_val else "", 9)
        self.set_text_color(*DARK)
        self.multi_cell(val_w, 6, str(value))
        self.set_x(self.l_margin)

    def bullet(self, text: str, color=DARK, indent: int = 4):
        txt_w = self.w - self.l_margin - self.r_margin - indent - 4  # remaining after bullet cell
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*color)
        self.set_x(self.l_margin + indent)
        self.cell(4, 6, "*")
        self.multi_cell(txt_w, 6, str(text))
        self.set_x(self.l_margin)

    def risk_badge(self, level: str, score: float):
        level_upper = level.upper()
        if level_upper in ("HIGH", "CRITICAL"):
            bg, fg = (254, 226, 226), RED
        elif level_upper == "MEDIUM":
            bg, fg = (255, 243, 205), AMBER
        else:
            bg, fg = (220, 252, 231), GREEN
        self.set_font("Helvetica", "B", 11)
        self.set_fill_color(*bg)
        self.set_text_color(*fg)
        self.cell(50, 10, f"  {level_upper}  ({score}/10)", fill=True, border=0, ln=True)
        self.ln(2)

    def two_col_list(self, items: list, label: str):
        if not items:
            return
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*MUTED)
        self.cell(0, 6, label.upper(), ln=True)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*DARK)
        mid = (len(items) + 1) // 2
        left, right = items[:mid], items[mid:]
        max_rows = max(len(left), len(right))
        r_col_w = self.w - self.l_margin - self.r_margin - 4 - 82 - 4  # 84 mm
        for i in range(max_rows):
            l_text = left[i]  if i < len(left)  else ""
            r_text = right[i] if i < len(right) else ""
            self.set_x(self.l_margin)
            self.cell(4, 5, "*" if l_text else "")
            self.cell(82, 5, l_text[:50] + ("..." if len(l_text) > 50 else ""))
            self.cell(4, 5, "*" if r_text else "")
            self.multi_cell(r_col_w, 5, r_text[:50] + ("..." if len(r_text) > 50 else ""))
            self.set_x(self.l_margin)
        self.ln(3)


def generate_pdf_report(cur: dict) -> bytes:
    """Build and return a PDF report as bytes given a result snapshot dict."""
    mode    = cur.get("mode", "Unknown")
    pages   = cur.get("total_pages", 0)
    words   = cur.get("word_count", 0)
    models  = cur.get("models", {})

    r_parser  = cur["parser"]
    r_entity  = cur["entity"]
    r_risk    = cur["risk"]
    r_action  = cur["action"]
    r_summary = cur["summary"]

    pdf = ReportPDF(title="PDF Intelligence Report", mode=mode)
    pdf.add_page()

    # ── Cover ─────────────────────────────────────────────────────────────────
    pdf.cover_block(pages, words, mode, models)

    # ── 1. Document Overview ──────────────────────────────────────────────────
    pdf.section_heading("1. Document Overview", NAVY)
    pdf.kv("Document type",  r_parser.document_type.title())
    pdf.kv("Language",       r_parser.language)
    pdf.kv("Quality",        r_parser.document_quality.title())
    pdf.kv("Has tables",     "Yes" if r_parser.has_tables  else "No")
    pdf.kv("Has numbers",    "Yes" if r_parser.has_numbers else "No")
    if r_parser.key_topics:
        pdf.kv("Key topics", "  ·  ".join(r_parser.key_topics))
    if r_parser.parsing_notes:
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(*MUTED)
        for note in r_parser.parsing_notes:
            pdf.cell(0, 5, f"Note: {note}", ln=True)
    pdf.ln(4)

    # ── 2. Entities ───────────────────────────────────────────────────────────
    pdf.section_heading("2. Entities Extracted", PURPLE)
    pdf.kv("Total entities", str(r_entity.total_entities))
    pdf.ln(2)
    for label, items in [
        ("People",        r_entity.people),
        ("Organisations", r_entity.organisations),
        ("Locations",     r_entity.locations),
        ("Dates",         r_entity.dates),
        ("Amounts",       r_entity.amounts),
        ("Emails",        r_entity.emails),
    ]:
        if items:
            pdf.two_col_list(items, label)
    pdf.ln(2)

    # ── 3. Risk Analysis ──────────────────────────────────────────────────────
    pdf.section_heading("3. Risk Analysis", RED)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*MUTED)
    pdf.cell(0, 6, "RISK LEVEL", ln=True)
    pdf.risk_badge(r_risk.risk_level, r_risk.overall_risk_score)
    pdf.kv("PII detected", "Yes — " + ", ".join(r_risk.pii_types) if r_risk.pii_detected and r_risk.pii_types else ("Yes" if r_risk.pii_detected else "No"), bold_val=r_risk.pii_detected)
    pdf.ln(3)
    for label, items, color in [
        ("Compliance risks", r_risk.compliance_risks, RED),
        ("Legal risks",      r_risk.legal_risks,      AMBER),
        ("Financial risks",  r_risk.financial_risks,  AMBER),
        ("Recommendations",  r_risk.recommendations,  GREEN),
    ]:
        if items:
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(*MUTED)
            pdf.cell(0, 6, label.upper(), ln=True)
            for item in items:
                pdf.bullet(item, color=color)
            pdf.ln(2)

    # ── 4. Action Items ───────────────────────────────────────────────────────
    pdf.section_heading("4. Action Items & Decisions", AMBER)
    pdf.kv("Total actions", str(r_action.total_actions))
    pdf.ln(2)
    if r_action.priority_actions:
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*RED)
        pdf.cell(0, 6, "PRIORITY ACTIONS", ln=True)
        for a in r_action.priority_actions:
            pdf.bullet(a, color=RED)
        pdf.ln(2)
    for label, items, color in [
        ("All action items", r_action.action_items, DARK),
        ("Decisions made",   r_action.decisions_made, GREEN),
        ("Deadlines",        r_action.deadlines, AMBER),
        ("Follow-ups",       r_action.follow_ups, PURPLE),
        ("Owners",           r_action.owners, MUTED),
    ]:
        if items:
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(*MUTED)
            pdf.cell(0, 6, label.upper(), ln=True)
            for item in items:
                pdf.bullet(item, color=color)
            pdf.ln(2)

    # ── 5. Executive Summary ──────────────────────────────────────────────────
    pdf.section_heading("5. Executive Summary", GREEN)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*DARK)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(pdf.w - pdf.l_margin - pdf.r_margin, 6, r_summary.summary or "No summary generated.")
    pdf.set_x(pdf.l_margin)
    pdf.ln(4)
    if r_summary.key_stats:
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*MUTED)
        pdf.cell(0, 6, "KEY STATISTICS", ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*DARK)
        for k, v in (r_summary.key_stats.items() if hasattr(r_summary.key_stats, "items") else []):
            pdf.kv(str(k), str(v))
        pdf.ln(2)
    if r_summary.recommendations:
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*MUTED)
        pdf.cell(0, 6, "RECOMMENDATIONS", ln=True)
        for rec in r_summary.recommendations:
            pdf.bullet(rec, color=GREEN)

    # ── Return bytes ──────────────────────────────────────────────────────────
    buf = io.BytesIO()
    pdf_bytes = pdf.output()
    return bytes(pdf_bytes)
