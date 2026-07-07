# Agent Documentation

> Complete reference for all 10 AI agents in the Multi-Agent Data Pipeline.

---

## Summary Table

| Agent | Icon | Pipeline | Wave | Model (Router) | Model (No Router) | Timeout | Max Tokens | LLM? |
|-------|------|----------|------|----------------|-------------------|---------|------------|------|
| Cleaner | 🧹 | CSV | 1 (parallel) | Haiku | Sonnet | 12s | 400 | Yes |
| PII Anonymiser | 🔒 | CSV | 1 (parallel) | regex-engine | regex-engine | N/A | 0 | **No** |
| Validator | 🛡️ | CSV | 1 (parallel) | Sonnet | Sonnet | 18s | 600 | Yes |
| Transformer | ⚡ | CSV | 1 (parallel) | Haiku | Sonnet | 12s | 400 | Yes |
| Anomaly Detector | 📡 | CSV | 1 (parallel) | Sonnet | Sonnet | 18s | 550 | Yes |
| Summariser | 📊 | CSV | 2 (sequential) | Sonnet | Sonnet | 20s | 1000 | Yes |
| PDF Parser | 📄 | PDF | 1 | Haiku | Sonnet | 15s | 1000 | Yes |
| Entity Extractor | 🔍 | PDF | 2 | Haiku | Sonnet | 15s | 1000 | Yes |
| Risk Detector | ⚠️ | PDF | 3 | Sonnet | Sonnet | 15s | 1000 | Yes |
| Action Extractor | ✅ | PDF | 4 | Sonnet | Sonnet | 15s | 1000 | Yes |

**Pipeline totals:** CSV = 6 agents (5 Wave 1 + 1 Wave 2) · PDF = 5 agents (sequential)

---

## CSV Pipeline Agents

### 🧹 Cleaner

**Purpose:** Analyses CSV data and identifies all data quality issues — null handling, date standardisation, inconsistent values, missing fields. Returns structured cleaning recommendations with rows affected and columns cleaned.

**Model Assignment:**

| Mode | Model | Reason |
|------|-------|--------|
| With Router | `claude-haiku-4-5-20251001` | Mechanical formatting — no reasoning needed |
| Without Router | `claude-sonnet-4-6` | Baseline quality |

**System Prompt:**

```
You are a data cleaning agent.
Your job is to analyse CSV data and identify all cleaning issues.
You must respond ONLY with valid JSON. No explanation, no markdown, no code fences.
JSON format:
{
    "issues_fixed": ["list of issues you found and fixed"],
    "rows_affected": 5,
    "cleaned_columns": ["col1", "col2"]
}
```

**Input Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `csv_preview` | `str` | required | First N rows of CSV as a string |
| `total_rows` | `int` | required | Total number of rows in the dataset |
| `model` | `str` | `None` | Model ID — falls back to `MODELS["quality"]` (Sonnet) |
| `span` | `AgentSpan` | `None` | Observability span for tracing |

**Output Schema** (`CleanerResult`):

```python
class CleanerResult(BaseModel):
    issues_fixed: List[str]    # Issues found and fixed
    rows_affected: int         # Number of rows with issues
    cleaned_columns: List[str] # Columns that were cleaned
```

**Configuration:**

| Setting | Value |
|---------|-------|
| Timeout | 12 seconds |
| Max tokens | 400 |
| API call | `client.messages.create()` |

**Fallback Behavior:**

On any exception (API error, JSON parse failure, timeout), returns:

```python
CleanerResult(
    issues_fixed=["Could not parse response"],
    rows_affected=0,
    cleaned_columns=[]
)
```

**Code Example:**

```python
from src.agents.cleaner import run

result = run(
    csv_preview="date,product,price\n2024-01-15,Widget A,29.99\n15/01/2024,widget a,29.99",
    total_rows=100,
    model="claude-haiku-4-5-20251001"
)

print(result.issues_fixed)
# ['Inconsistent date formats', 'Duplicate product names with different casing']
print(result.rows_affected)   # 1
print(result.cleaned_columns) # ['date', 'product']
```

---

### 🔒 PII Anonymiser

**Purpose:** Detects and masks Personally Identifiable Information (PII) using regex patterns. This agent does **NOT** call an LLM — it runs entirely locally with zero cost. Detects emails, phone numbers, postcodes, and credit card numbers, then applies partial masking.

**Model Assignment:**

| Mode | Model | Cost |
|------|-------|------|
| Always | `regex-engine` (local) | **£0.00** |

**System Prompt:**

N/A — no LLM call. Uses regex patterns defined in `PATTERNS` dict.

**Detection Patterns & Anonymisation:**

| PII Type | Regex Pattern | Anonymisation | Example |
|----------|---------------|---------------|---------|
| Email | `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}` | First char + `***@***.com` | `john@acme.com` → `j***@***.com` |
| Phone | `(\+?\d[\d\s\-().]{7,}\d)` | All but last 2 digits → `*` | `+44 7700 900123` → `****\*\*\*\*\*\*\*\*23` |
| Postcode | `\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b` | First 3 chars + `***` | `SW1A 1AA` → `SW1***` |
| Card Number | `\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}` | `**** **** ****` + last 4 | `4111 1111 1111 1234` → `**** **** **** 1234` |

**Input Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `csv_preview` | `str` | required | CSV data as a string |
| `total_rows` | `int` | required | Total row count |
| `model` | `str` | `None` | Ignored — always uses regex |
| `span` | `AgentSpan` | `None` | Observability span |

**Output Schema** (`PIIAnonymiserResult`):

```python
class PIIAnonymiserResult(BaseModel):
    pii_found: List[str]          # e.g. ["Row 4: email", "Row 9: phone"]
    rows_affected: int            # Number of rows containing PII
    pii_types_detected: List[str] # e.g. ["email", "phone", "card_number"]
    anonymised_preview: str       # Full CSV with PII masked
```

**Configuration:**

| Setting | Value |
|---------|-------|
| Timeout | N/A (local computation, <1s) |
| Max tokens | 0 (no LLM) |
| Cost | £0.00 |

**Fallback Behavior:**

No failure path — regex always completes. Returns empty results if no PII found.

**Code Example:**

```python
from src.agents.pii_anonymiser import run

result = run(
    csv_preview="name,email,phone\nJohn,john@example.com,+44 7700 900123\nJane,jane@test.co.uk,020 7946 0000",
    total_rows=2
)

print(result.pii_found)
# ['Row 1: email: 1 found', 'Row 1: phone: 1 found', 'Row 2: email: 1 found', 'Row 2: phone: 1 found']
print(result.rows_affected)       # 2
print(result.pii_types_detected)  # ['email', 'phone']
print(result.anonymised_preview)
# name,email,phone
# John,j***@***.com,****\*\*\*\*\*\*\*\*23
# Jane,j***@***.co.uk,****\*\*\*\*\*\*\*\*00
```

---

### 🛡️ Validator

**Purpose:** Validates CSV data for schema correctness, data types, null values, and constraint violations. Produces a completeness score and distinguishes between passed checks and violations.

**Model Assignment:**

| Mode | Model | Reason |
|------|-------|--------|
| Always | `claude-sonnet-4-6` | Schema judgment requires reasoning |

**System Prompt:**

```
You are a data validation agent.
Your job is to validate CSV data for schema correctness, data types, null values, and constraint violations.
You must respond ONLY with valid JSON. No explanation, no markdown, no code fences.
JSON format:
{
    "schema_ok": true,
    "violations": ["list of validation failures found"],
    "passed_checks": ["list of checks that passed"],
    "completeness_score": 95.5
}
```

**Input Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `csv_preview` | `str` | required | CSV data as a string |
| `total_rows` | `int` | required | Total row count |
| `model` | `str` | `None` | Falls back to `MODELS["quality"]` |
| `span` | `AgentSpan` | `None` | Observability span |

**Output Schema** (`ValidatorResult`):

```python
class ValidatorResult(BaseModel):
    schema_ok: bool              # Overall schema validity
    violations: List[str]        # Validation failures found
    passed_checks: List[str]     # Checks that passed
    completeness_score: float    # 0-100 score
```

**Configuration:**

| Setting | Value |
|---------|-------|
| Timeout | 18 seconds |
| Max tokens | 600 |
| API call | `client.messages.create()` |

**Fallback Behavior:**

```python
ValidatorResult(
    schema_ok=False,
    violations=["Could not parse response"],
    passed_checks=[],
    completeness_score=0.0
)
```

**Code Example:**

```python
from src.agents.validator import run

result = run(
    csv_preview="id,name,amount\n1,Alice,29.99\n2,,-5.00\n3,Bob,abc",
    total_rows=3
)

print(result.schema_ok)          # False
print(result.violations)         # ['Missing name in row 2', 'Negative amount in row 2', 'Invalid amount in row 3']
print(result.passed_checks)      # ['All IDs unique', 'All names present in rows 1,3']
print(result.completeness_score) # 72.2
```

---

### ⚡ Transformer

**Purpose:** Suggests and applies data transformations — column derivation, normalisation, new column creation, and date format standardisation. Identifies opportunities to enrich the dataset with derived fields.

**Model Assignment:**

| Mode | Model | Reason |
|------|-------|--------|
| With Router | `claude-haiku-4-5-20251001` | Column derivation is structured and deterministic |
| Without Router | `claude-sonnet-4-6` | Baseline quality |

**System Prompt:**

```
You are a data transformation agent.
Your job is to suggest and apply transformations to CSV data.
You must respond ONLY with valid JSON. No explanation, no markdown, no code fences.
JSON format:
{
    "transformations_applied": ["list of transformations applied"],
    "new_columns": ["col1", "col2"],
    "rows_transformed": 15
}
```

**Input Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `csv_preview` | `str` | required | CSV data as a string |
| `total_rows` | `int` | required | Total row count |
| `model` | `str` | `None` | Falls back to `MODELS["quality"]` |
| `span` | `AgentSpan` | `None` | Observability span |

**Output Schema** (`TransformerResult`):

```python
class TransformerResult(BaseModel):
    transformations_applied: List[str]  # e.g. ["Dates → ISO 8601", "Product names → title case"]
    new_columns: List[str]              # e.g. ["year", "month", "price_band"]
    rows_transformed: int               # Number of rows affected
```

**Configuration:**

| Setting | Value |
|---------|-------|
| Timeout | 12 seconds |
| Max tokens | 400 |
| API call | `client.messages.create()` |

**Fallback Behavior:**

```python
TransformerResult(
    transformations_applied=["Could not parse response"],
    new_columns=[],
    rows_transformed=0
)
```

**Code Example:**

```python
from src.agents.transformer import run

result = run(
    csv_preview="date,price\n2024-01-15,29.99\n15/01/2024,49.99",
    total_rows=2
)

print(result.transformations_applied)
# ['Dates standardised to ISO 8601', 'Price normalised to float']
print(result.new_columns)      # ['year', 'month', 'day_of_week']
print(result.rows_transformed) # 2
```

---

### 📡 Anomaly Detector

**Purpose:** Finds statistical outliers, duplicate records, suspicious values, price anomalies, and impossible values in CSV data. Assigns an anomaly score (0-10) and flags specific rows for review.

**Model Assignment:**

| Mode | Model | Reason |
|------|-------|--------|
| Always | `claude-sonnet-4-6` | Statistical reasoning needs quality |

**System Prompt:**

```
You are an anomaly detection agent.
Your job is to find statistical outliers, duplicate records, suspicious values, price anomalies, and impossible values in CSV data.
You must respond ONLY with valid JSON. No explanation, no markdown, no code fences.
JSON format:
{
    "anomalies": ["list of anomalies found with row numbers"],
    "anomaly_count": 2,
    "anomaly_score": 4.5,
    "flagged_rows": [7, 11]
}
```

**Input Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `csv_preview` | `str` | required | CSV data as a string |
| `total_rows` | `int` | required | Total row count |
| `model` | `str` | `None` | Falls back to `MODELS["quality"]` |
| `span` | `AgentSpan` | `None` | Observability span |

**Output Schema** (`AnomalyResult`):

```python
class AnomalyResult(BaseModel):
    anomalies: List[str]      # Descriptions with row numbers
    anomaly_count: int        # Total anomalies found
    anomaly_score: float      # 0-10 scale (9.0+ triggers guardrail warning)
    flagged_rows: List[int]   # Row numbers that need review
```

**Configuration:**

| Setting | Value |
|---------|-------|
| Timeout | 18 seconds |
| Max tokens | 550 |
| API call | `client.messages.create()` |

**Fallback Behavior:**

```python
AnomalyResult(
    anomalies=["Could not parse response"],
    anomaly_count=0,
    anomaly_score=0.0,
    flagged_rows=[]
)
```

**Code Example:**

```python
from src.agents.anomaly import run

result = run(
    csv_preview="id,product,price\n7,Widget,999.99\n11,Thing,-5.00\n12,Widget,29.99",
    total_rows=12
)

print(result.anomalies)
# ['TXN007: price £999.99 — expected ~£29.99', 'TXN011: negative price']
print(result.anomaly_count)  # 2
print(result.anomaly_score)  # 6.5
print(result.flagged_rows)    # [7, 11]
```

---

### 📊 Summariser

**Purpose:** Produces a business-readable summary with key statistics and actionable recommendations. This is **Wave 2** — it receives context from all Wave 1 agents (cleaner, PII, validator, transformer, anomaly) to produce a comprehensive summary.

**Model Assignment:**

| Mode | Model | Reason |
|------|-------|--------|
| Always | `claude-sonnet-4-6` | Business insights require full quality |

**System Prompt:**

```
You are a data summarisation agent.
Your job is to produce a business-readable summary of CSV data with key statistics and actionable recommendations.
You must respond ONLY with valid JSON. No explanation, no markdown, no code fences.
JSON format:
{
    "summary": "one paragraph business-readable summary of the dataset",
    "key_stats": {
        "Total Rows": "15",
        "Categories": "4",
        "Date Range": "Jan 2024"
    },
    "recommendations": ["recommendation 1", "recommendation 2"]
}
```

**Input Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `csv_preview` | `str` | required | CSV data as a string |
| `total_rows` | `int` | required | Total row count |
| `context` | `str` | `""` | Findings from Wave 1 agents |
| `model` | `str` | `None` | Falls back to `MODELS["quality"]` |
| `span` | `AgentSpan` | `None` | Observability span |
| `api_key` | `str` | `None` | Override API key |

**Output Schema** (`SummariserResult`):

```python
class SummariserResult(BaseModel):
    summary: str             # Business-readable paragraph
    key_stats: dict          # e.g. {"Total Revenue": "£413.56", "Top Category": "Skincare"}
    recommendations: List[str]  # Actionable next steps
```

**Configuration:**

| Setting | Value |
|---------|-------|
| Timeout | 20 seconds |
| Max tokens | 1000 |
| API call | `client.messages.create()` |

**Fallback Behavior:**

```python
SummariserResult(
    summary="Could not parse response",
    key_stats={},
    recommendations=[]
)
```

**Code Example:**

```python
from src.agents.summariser import run

# context is auto-populated by pipeline with Wave 1 results
result = run(
    csv_preview="product,category,price\nWidget A,Electronics,29.99",
    total_rows=100,
    context="Cleaner: 3 issues fixed. Anomaly: 2 outliers found. Validator: 95% complete."
)

print(result.summary)
# 'Dataset contains 100 retail transactions across 4 categories...'
print(result.key_stats)
# {'Total Rows': '100', 'Categories': '4', 'Date Range': 'Jan 2024'}
print(result.recommendations)
# ['Investigate TXN007 — possible data entry error']
```

---

## PDF Pipeline Agents

All PDF agents use plain Python classes (not Pydantic) and accept `text_preview` + `total_pages` as inputs.

---

### 📄 PDF Parser

**Purpose:** Analyses extracted PDF text and identifies document structure, metadata, and content type. Detects whether the document is an invoice, contract, report, letter, or other type. Identifies sections, tables, numeric content, and key topics.

**Model Assignment:**

| Mode | Model | Reason |
|------|-------|--------|
| With Router | `claude-haiku-4-5-20251001` | Document structure extraction |
| Without Router | `claude-sonnet-4-6` | Baseline quality |

**System Prompt:**

```
You are a document parsing agent.
Your job is to analyse extracted PDF text and identify document structure, metadata and content type.
You must respond ONLY with valid JSON. No explanation, no markdown, no code fences.
JSON format:
{
    "document_type": "invoice/contract/report/letter/other",
    "language": "English",
    "total_sections": 5,
    "has_tables": true,
    "has_numbers": true,
    "key_topics": ["topic1", "topic2", "topic3"],
    "document_quality": "good/fair/poor",
    "parsing_notes": ["note1", "note2"]
}
```

**Input Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `text_preview` | `str` | required | Extracted PDF text |
| `total_pages` | `int` | required | Number of PDF pages |
| `model` | `str` | `"claude-haiku-4-5-20251001"` | Model ID |
| `api_key` | `str` | `None` | Override API key |
| `span` | `AgentSpan` | `None` | Observability span |

**Output Schema** (`PDFParserResult` — plain class):

```python
class PDFParserResult:
    document_type: str       # "invoice", "contract", "report", "letter", "other"
    language: str            # e.g. "English"
    total_sections: int      # Number of sections detected
    has_tables: bool         # Whether tables are present
    has_numbers: bool        # Whether numeric data is present
    key_topics: List[str]    # Main topics
    document_quality: str    # "good", "fair", "poor"
    parsing_notes: List[str] # Notes about parsing
```

**Configuration:**

| Setting | Value |
|---------|-------|
| Timeout | 15 seconds |
| Max tokens | 1000 |
| API call | `client.messages.create()` |

**Fallback Behavior:**

```python
PDFParserResult(
    document_type="unknown",
    parsing_notes=["Could not parse response"]
)
```

**Code Example:**

```python
from src.agents.pdf_parser import run

result = run(
    text_preview="INVOICE #1234\nAcme Corp\nDate: 2024-01-15\nAmount: £1,234.56",
    total_pages=2
)

print(result.document_type)     # "invoice"
print(result.language)          # "English"
print(result.key_topics)        # ['invoice', 'payment', 'Acme Corp']
print(result.document_quality)  # "good"
```

---

### 🔍 Entity Extractor

**Purpose:** Extracts named entities from document text — people, organisations, locations, dates, monetary amounts, and email addresses. Provides a structured inventory of all entities found.

**Model Assignment:**

| Mode | Model | Reason |
|------|-------|--------|
| With Router | `claude-haiku-4-5-20251001` | Pattern-based NER |
| Without Router | `claude-sonnet-4-6` | Baseline quality |

**System Prompt:**

```
You are an entity extraction agent.
Your job is to identify and extract named entities from documents.
You must respond ONLY with valid JSON. No explanation, no markdown, no code fences.
JSON format:
{
    "people": ["person1", "person2"],
    "organisations": ["org1", "org2"],
    "locations": ["location1", "location2"],
    "dates": ["date1", "date2"],
    "amounts": ["£1000", "$500"],
    "emails": ["email1@example.com"],
    "total_entities": 15
}
```

**Input Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `text_preview` | `str` | required | Extracted PDF text |
| `total_pages` | `int` | required | Number of PDF pages |
| `model` | `str` | `"claude-haiku-4-5-20251001"` | Model ID |
| `api_key` | `str` | `None` | Override API key |
| `span` | `AgentSpan` | `None` | Observability span |

**Output Schema** (`EntityExtractorResult` — plain class):

```python
class EntityExtractorResult:
    people: List[str]           # Named individuals
    organisations: List[str]    # Companies, agencies
    locations: List[str]        # Addresses, cities, countries
    dates: List[str]            # Date references
    amounts: List[str]          # Monetary values
    emails: List[str]           # Email addresses
    total_entities: int         # Count of all entities
```

**Configuration:**

| Setting | Value |
|---------|-------|
| Timeout | 15 seconds |
| Max tokens | 1000 |
| API call | `client.messages.create()` |

**Fallback Behavior:**

```python
EntityExtractorResult(
    people=[], organisations=[], locations=[],
    dates=[], amounts=[], emails=[],
    total_entities=0
)
```

**Code Example:**

```python
from src.agents.entity_extractor import run

result = run(
    text_preview="Contract between Acme Corp and John Smith, dated 15 Jan 2024. Amount: £12,000. Contact: john@acme.com",
    total_pages=5
)

print(result.people)         # ['John Smith']
print(result.organisations)  # ['Acme Corp']
print(result.dates)          # ['15 Jan 2024']
print(result.amounts)        # ['£12,000']
print(result.emails)         # ['john@acme.com']
print(result.total_entities) # 5
```

---

### ⚠️ Risk Detector

**Purpose:** Identifies risks, sensitive data, PII, compliance issues, and red flags in documents. Checks for GDPR risks, legal clause issues, financial red flags, and assigns an overall risk score and level.

**Model Assignment:**

| Mode | Model | Reason |
|------|-------|--------|
| Always | `claude-sonnet-4-6` | Compliance reasoning requires quality |

**System Prompt:**

```
You are a document risk detection agent.
Your job is to identify risks, sensitive data, PII, compliance issues and red flags in documents.
You must respond ONLY with valid JSON. No explanation, no markdown, no code fences.
JSON format:
{
    "pii_detected": true,
    "pii_types": ["names", "emails", "phone numbers"],
    "compliance_risks": ["GDPR risk - personal data present", "risk2"],
    "legal_risks": ["unsigned contract clause", "risk2"],
    "financial_risks": ["large payment terms", "risk2"],
    "overall_risk_score": 7.5,
    "risk_level": "high",
    "recommendations": ["recommendation1", "recommendation2"]
}
```

**Input Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `text_preview` | `str` | required | Extracted PDF text |
| `total_pages` | `int` | required | Number of PDF pages |
| `model` | `str` | `"claude-sonnet-4-6"` | Model ID |
| `api_key` | `str` | `None` | Override API key |
| `span` | `AgentSpan` | `None` | Observability span |

**Output Schema** (`RiskDetectorResult` — plain class):

```python
class RiskDetectorResult:
    pii_detected: bool            # Whether PII was found
    pii_types: List[str]          # e.g. ["names", "emails"]
    compliance_risks: List[str]   # GDPR, HIPAA, etc.
    legal_risks: List[str]        # Contract issues
    financial_risks: List[str]    # Payment/red flag issues
    overall_risk_score: float     # 0-10 scale
    risk_level: str               # "low", "medium", "high", "critical"
    recommendations: List[str]    # Mitigation steps
```

**Configuration:**

| Setting | Value |
|---------|-------|
| Timeout | 15 seconds |
| Max tokens | 1000 |
| API call | `client.messages.create()` |

**Fallback Behavior:**

```python
RiskDetectorResult(
    pii_detected=False,
    overall_risk_score=0.0,
    risk_level="unknown",
    recommendations=["Could not parse response"]
)
```

**Code Example:**

```python
from src.agents.risk_detector import run

result = run(
    text_preview="This contract contains personal data for John Smith (john@acme.com, +44 7700 900123)...",
    total_pages=12
)

print(result.pii_detected)      # True
print(result.pii_types)         # ['names', 'emails', 'phone numbers']
print(result.compliance_risks)  # ['GDPR risk - personal data present without consent']
print(result.overall_risk_score) # 7.5
print(result.risk_level)        # "high"
```

---

### ✅ Action Extractor

**Purpose:** Extracts action items, decisions, deadlines, follow-ups, and owners from document text. Identifies priority actions and provides a structured inventory of all tasks and decisions.

**Model Assignment:**

| Mode | Model | Reason |
|------|-------|--------|
| Always | `claude-sonnet-4-6` | Decision extraction requires reasoning |

**System Prompt:**

```
You are an action item extraction agent.
Your job is to extract all action items, decisions, deadlines, and follow-ups from document text.
You must respond ONLY with valid JSON. No explanation, no markdown, no code fences.
JSON format:
{
    "action_items": ["action1", "action2"],
    "decisions_made": ["decision1", "decision2"],
    "deadlines": ["deadline1", "deadline2"],
    "follow_ups": ["followup1", "followup2"],
    "owners": ["owner1", "owner2"],
    "priority_actions": ["urgent1", "urgent2"],
    "total_actions": 10
}
```

**Input Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `text_preview` | `str` | required | Extracted PDF text |
| `total_pages` | `int` | required | Number of PDF pages |
| `model` | `str` | `"claude-sonnet-4-6"` | Model ID |
| `api_key` | `str` | `None` | Override API key |
| `span` | `AgentSpan` | `None` | Observability span |

**Output Schema** (`ActionExtractorResult` — plain class):

```python
class ActionExtractorResult:
    action_items: List[str]      # Tasks to complete
    decisions_made: List[str]    # Decisions documented
    deadlines: List[str]         # Time-bound items
    follow_ups: List[str]        # Items needing follow-up
    owners: List[str]            # Assigned individuals
    priority_actions: List[str]  # Urgent/high-priority items
    total_actions: int           # Count of all actions
```

**Configuration:**

| Setting | Value |
|---------|-------|
| Timeout | 15 seconds |
| Max tokens | 1000 |
| API call | `client.messages.create()` |

**Fallback Behavior:**

```python
ActionExtractorResult(
    action_items=[], decisions_made=[], deadlines=[],
    follow_ups=[], owners=[], priority_actions=[],
    total_actions=0
)
```

**Code Example:**

```python
from src.agents.action_extractor import run

result = run(
    text_preview="ACTION: John to review contract by 31 Jan. DECISION: Budget approved at £50k. FOLLOW-UP: Schedule follow-up meeting.",
    total_pages=8
)

print(result.action_items)     # ['John to review contract']
print(result.decisions_made)   # ['Budget approved at £50k']
print(result.deadlines)        # ['31 Jan']
print(result.owners)           # ['John']
print(result.priority_actions) # ['John to review contract by 31 Jan']
print(result.total_actions)    # 3
```

---

## Agent Pattern

All LLM-based agents follow the same structure:

```python
# 1. System prompt — strict JSON-only output
SYSTEM_PROMPT = """You are a [role] agent.
You must respond ONLY with valid JSON. No explanation, no markdown, no code fences."""

# 2. run() function — same signature pattern
def run(csv_preview: str, total_rows: int,
        model: str = None, span=None) -> ResultModel:
    # a. Default model selection
    if model is None:
        model = MODELS["quality"]

    # b. Anthropic API call
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = client.messages.create(model=model, ...)

    # c. Strip markdown fences, parse JSON
    raw = response.content[0].text.strip()
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    data = json.loads(raw)

    # d. Validate with Pydantic
    result = ResultModel(**data)

    # e. Record telemetry via span
    if span:
        span.finish(input_tokens=..., output_tokens=..., ...)

    return result

# 3. Fallback — never crash the pipeline
    except Exception as e:
        return ResultModel(...)  # degraded but valid result
```

**Key invariant:** Agents never crash the pipeline. Every failure returns a valid fallback result with error messages in the output fields.

---

## Router Engine

The Router Engine in `src/router.py` assigns models based on task complexity:

```python
SIMPLE_AGENTS = ["cleaner", "pii_anonymiser", "transformer"]
COMPLEX_AGENTS = ["validator", "anomaly", "summariser", "pdf_parser", "entity_extractor", "risk_detector", "action_extractor"]
```

- **Simple → Haiku** (`claude-haiku-4-5-20251001`) — mechanical tasks
- **Complex → Sonnet** (`claude-sonnet-4-6`) — reasoning required
- **Disable:** `routing_enabled=False` → all agents use Sonnet

### Cost Comparison

| Mode | CSV Cost (15 rows) | CSV Latency | Saving |
|------|-------------------|-------------|--------|
| No Router (all Sonnet) | ~£0.27 | ~14s | — |
| With Router (routed) | ~£0.08 | ~5s | ~70% cost, ~63% latency |

---

## Adding a New Agent

Follow the existing pattern:

1. **Create** `src/agents/your_agent.py` with `SYSTEM_PROMPT` and `run()` function
2. **Add** result model to `src/models.py` (Pydantic v2 `BaseModel`)
3. **Add** to `AGENT_MAX_TOKENS` and `AGENT_TIMEOUTS` in `src/cost_config.py`
4. **Add** to `SIMPLE_AGENTS` or `COMPLEX_AGENTS` in `src/router.py`
5. **Wire** into `src/pipeline.py` wave1_agents dict (or wave2 if it needs prior context)
6. **Add** telemetry fields to `PipelineResult` in `src/models.py`

```python
# src/agents/your_agent.py
from src.models import YourAgentResult
from src.cost_config import MODELS, AGENT_MAX_TOKENS

SYSTEM_PROMPT = """You are a [role] agent.
You must respond ONLY with valid JSON. No explanation, no markdown, no code fences.
JSON format:
{
    "field1": "value",
    "field2": ["list"]
}"""

def run(csv_preview: str, total_rows: int,
        model: str = None, span=None) -> YourAgentResult:
    if model is None:
        model = MODELS["quality"]
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    user_msg = f"[task] this CSV data ({total_rows} total rows):\n\n{csv_preview}"

    try:
        response = client.messages.create(
            model=model,
            max_tokens=AGENT_MAX_TOKENS["your_agent"],
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}]
        )
        raw = response.content[0].text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(raw)
        result = YourAgentResult(**data)
        if span:
            span.finish(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                model=model, raw_response=raw,
                parsed_output=str(result.model_dump()), parse_ok=True
            )
        return result
    except Exception as e:
        fallback = YourAgentResult(field1="Could not parse response", field2=[])
        if span:
            span.finish(input_tokens=0, output_tokens=0, model=model,
                        raw_response="", parsed_output="", parse_ok=False, error_message=str(e))
        return fallback
```

---

## Configuration Reference

All agent settings are in `src/cost_config.py`:

```python
# Token limits per agent
AGENT_MAX_TOKENS = {
    "cleaner": 400,
    "pii_anonymiser": 350,
    "validator": 600,
    "transformer": 400,
    "anomaly": 550,
    "summariser": 1000,
    "pdf_parser": 600,
    "entity_extractor": 700,
    "risk_detector": 600,
    "action_extractor": 600,
}

# Timeout limits per agent (seconds)
AGENT_TIMEOUTS = {
    "cleaner": 12,
    "pii_anonymiser": 10,
    "validator": 18,
    "transformer": 12,
    "anomaly": 18,
    "summariser": 20,
    "pdf_parser": 15,
    "entity_extractor": 15,
    "risk_detector": 15,
    "action_extractor": 15,
}

# Model pricing (USD per million tokens)
PRICING = {
    "claude-haiku-4-5-20251001": {
        "input_per_m": 0.80,
        "output_per_m": 4.00,
    },
    "claude-sonnet-4-6": {
        "input_per_m": 3.00,
        "output_per_m": 15.00,
    },
}
```
