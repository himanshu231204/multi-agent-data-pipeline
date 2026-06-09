import re
import pandas as pd
from src.models import PIIAnonymiserResult

# PII patterns
PATTERNS = {
    "email":       (r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                    lambda m: m.split('@')[0][0] + "***@***.com"),
    "phone":       (r'(\+?\d[\d\s\-().]{7,}\d)',
                    lambda m: re.sub(r'\d', '*', m[:-2]) + m[-2:]),
    "postcode":    (r'\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b',
                    lambda m: m[:3] + "***"),
    "card_number": (r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b',
                    lambda m: "**** **** **** " + m.replace(" ","").replace("-","")[-4:]),
}

def anonymise_text(text: str) -> tuple[str, list]:
    """Anonymise PII in a string, return cleaned text and list of findings."""
    findings = []
    for pii_type, (pattern, replacement) in PATTERNS.items():
        matches = re.findall(pattern, str(text), re.IGNORECASE)
        if matches:
            findings.append(f"{pii_type}: {len(matches)} found")
            text = re.sub(pattern,
                         lambda m: replacement(m.group()),
                         str(text),
                         flags=re.IGNORECASE)
    return text, findings

def run(csv_preview: str, total_rows: int) -> "PIIAnonymiserResult":
    print("[PII Anonymiser] Starting...")
    lines = csv_preview.strip().split("\n")
    cleaned_lines = []
    all_findings = []
    rows_affected = 0
    
    for i, line in enumerate(lines):
        cleaned_line, findings = anonymise_text(line)
        cleaned_lines.append(cleaned_line)
        if findings:
            rows_affected += 1
            all_findings.extend([f"Row {i}: {f}" for f in findings])
            
    cleaned_preview = "\n".join(cleaned_lines)
    pii_types = list({f.split(":")[0].strip() for f in all_findings})
    
    print(f"[PII Anonymiser] Done — {rows_affected} rows had PII")
    
    return PIIAnonymiserResult(
        pii_found=all_findings,
        rows_affected=rows_affected,
        pii_types_detected=pii_types,
        anonymised_preview=cleaned_preview
    )