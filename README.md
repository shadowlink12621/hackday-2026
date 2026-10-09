# ClaimGuard — Multimodal Claim Verification Agent

**Hacktoberfest Hack Day Bengaluru × IEEE CIS (October 9, 2026)**
**Tracks:** *Best Use of Gemma 4* & *Best Open-Source AI Project*
**License:** Apache 2.0 (See `LICENSE`)


---

## Overview

ClaimGuard is an open-source multimodal claim verification agent designed to audit corporate expense receipts and health insurance bills.

Instead of relying on fragile legacy OCR or trusting black-box LLM arithmetic, ClaimGuard uses a two-stage hybrid architecture:
1. **Document Perception (Google GenAI):** Uses the configured Gemini API model for consented image/PDF extraction; searchable PDFs can also be parsed locally. Model calls are server-side.
2. **Deterministic Code Verification (Python Engine):** Validates arithmetic sums, cross-references an immutable SQLite ledger for exact duplicate image submissions (SHA-256), applies currency conversions, and enforces configurable policy limits (e.g. corporate expense caps or hospital room-rent limits).

---

## Key Features

- **Model-backed extraction:** Google GenAI integration with prompt-injection defenses; cloud processing requires explicit user consent.
- **Honest Offline Mode:** Without a configured model, policy Q&A returns extractive source passages and claim uploads return zero-confidence “not extracted” evidence rather than fabricated sample claims.
- **Deterministic Math & Policy Engine:** Strict arithmetic validation separating AI perception from mathematical proof.
- **Cryptographic Duplicate Ledger:** Instant duplicate submission detection using SHA-256 image hashes stored in SQLite with WAL mode and concurrency retry handling.
- **Configurable Policies:** Dynamic rule settings for expense caps, health insurance room-rent caps, and exclusions for non-medical consumables.
- **Manager Approval Workflow:** Full lifecycle API supporting `Pending`, `Approved`, and `Rejected` statuses with CSV audit export.
- **Agent Skill Standard:** Packaged following the [Agent Skills open specification](https://agentskills.io/specification) under `skills/expense-claim-audit/SKILL.md`.

---

## Architecture

```
User Document (Receipt / Bill Image)
                 │
                 ▼
       [FastAPI Validation API]
                 │
        ┌────────┴──────────────────┐
        ▼                           ▼
[Google GenAI Model]     [Deterministic Verification]
  - Untrusted data guard   - SHA-256 duplicate ledger
  - Structured extraction  - Line-item sum verification
  - Line-item categorizer  - Configurable policy caps
  - Confidence scoring     - Currency normalization
        │                           │
        └────────┬──────────────────┘
                 ▼
      [SQLite Claim Ledger]
  - Reviewer decision tracking (Approve / Reject)
  - CSV audit export
```

---

## Quickstart

### Prerequisites
- Python 3.11+
- Node.js 20+

### 1. Backend Setup & Run

Run from the **repository root**:

```bash
# Optional: create and activate virtual environment
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Copy .env.example to .env and set GEMINI_API_KEY locally.
# GEMINI_MODEL defaults to gemini-2.5-flash. Never commit .env.

# Start FastAPI server
python -m uvicorn backend.main:app --reload --port 8000
```

Verify backend health: [http://localhost:8000/api/health](http://localhost:8000/api/health)

### 2. Frontend Setup & Run

In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL printed by the dev server (normally [http://localhost:5173](http://localhost:5173)) in your browser.

### Policy and case workflow

Create a patient case, upload a policy PDF (up to 20 MB), then add optional supporting documents. Searchable policy PDFs are indexed locally page by page. Scanned policy PDFs are not indexed yet. The claim auditor accepts searchable PDFs plus JPEG/PNG; cloud AI/OCR is only used when the user opts in and `GEMINI_API_KEY` is configured. Use **Test AI connection** in the policy view to verify the live provider instead of relying on configuration status.

Confirmed reminder dates are stored with the local case and can be downloaded as `.ics`; ClaimGuard does not infer filing deadlines or coverage decisions. Medical-record interpretation is not enabled yet.

### Private deployment

Do not expose this single-machine SQLite/file-storage demo publicly with personal policy or health data. Before an internet-facing deployment, set `APP_ENV=production`, configure a long random `CLAIMGUARD_API_TOKEN`, restrict `CORS_ORIGINS` to the exact frontend origin, use HTTPS, and provide the token in the browser's private-workspace gate. This is a basic shared-token gate, not multi-user identity or production health-data storage.

---

## Running Automated Tests

Run the complete backend test suite from the repository root:

```bash
python -m pytest -v
```

Tests run against isolated temporary SQLite databases to prevent cross-test contamination.

---

## API Summary

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Service health status |
| `POST` | `/api/validate` | Upload PDF/JPEG/PNG (`file`, `domain_mode`, `rule_settings`, `allow_cloud_processing`) for validation |
| `POST` | `/api/model/check` | Make a live, minimal cloud-model connectivity request |
| `POST` | `/api/cases/{id}/reminder` | Persist or clear a user-confirmed case reminder date |
| `GET` | `/api/claims` | List all historical claims from SQLite ledger |
| `POST` | `/api/claims/{id}/decision` | Record manager review (`{"decision": "Approved"}`) |
| `GET` | `/api/export.csv` | Download sanitised CSV audit trail |

Refer to [API_STYLE_GUIDE.md](file:///c:/Users/Vansh/OneDrive/Desktop/New%20folder%20%282%29/API_STYLE_GUIDE.md) and [CONTRACTS.md](file:///c:/Users/Vansh/OneDrive/Desktop/New%20folder%20%282%29/CONTRACTS.md) for full schemas.
