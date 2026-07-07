import re
import time
from src.models import PIIAnonymiserResult

PATTERNS = {
    "email":       (r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                    lambda m: m.split('@')[0][0] + "***@***.com"),
    "phone":       (r'(\+?\d[\d\s\-().]{7,}\d)',
                    lambda m: re.sub(r'\d', '*', m[:-2]) + m[-2:]),
    "postcode":    (r'\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b',
                    lambda m: m[:3] + "***"),
    "card_number": (r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b',
                    lambda m: "**** **** **** " + m.replace(" ", "").replace("-", "")[-4:]),
}


def anonymise_text(text: str) -> tuple[str, list]:
    findings = []
    for pii_type, (pattern, replacement) in PATTERNS.items():
        matches = re.findall(pattern, str(text), re.IGNORECASE)
        if matches:
            findings.append(f"{pii_type}: {len(matches)} found")
            text = re.sub(pattern, lambda m: replacement(m.group()), str(text), flags=re.IGNORECASE)
    return text, findings


def run(csv_preview: str, total_rows: int,
        model: str = None, span=None) -> PIIAnonymiserResult:
    t0 = time.time()
    lines = csv_preview.strip().split("\n")
    cleaned_lines, all_findings = [], []
    rows_affected = 0

    for i, line in enumerate(lines):
        cleaned_line, findings = anonymise_text(line)
        cleaned_lines.append(cleaned_line)
        if findings:
            rows_affected += 1
            all_findings.extend([f"Row {i}: {f}" for f in findings])

    cleaned_preview = "\n".join(cleaned_lines)
    pii_types = sorted({f.split(": ")[1].strip() for f in all_findings if len(f.split(": ")) > 1})

    result = PIIAnonymiserResult(
        pii_found=all_findings,
        rows_affected=rows_affected,
        pii_types_detected=pii_types,
        anonymised_preview=cleaned_preview,
    )

    if span:
        latency_ms = int((time.time() - t0) * 1000)
        span.latency_ms = latency_ms
        span.input_tokens = 0
        span.output_tokens = 0
        span.cost_gbp = 0.0
        span.model = "regex-engine"
        span.raw_response = f"Regex scan: {rows_affected} rows affected"
        span.parsed_output = str(result.model_dump())
        span.parse_ok = True
        span.status = "complete"

    return result
