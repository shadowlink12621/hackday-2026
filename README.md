# ClaimGuard — Multimodal Claim Verification Agent

**Hacktoberfest Hack Day Bengaluru × IEEE CIS (October 9, 2026)**
**Tracks:** *Best Use of Gemma 4* & *Best Open-Source AI Project*
**License:** Apache 2.0 (See `LICENSE`)


---

## Overview

ClaimGuard is an open-source multimodal claim verification agent designed to audit corporate expense receipts and health insurance bills.

Instead of relying on fragile legacy OCR or trusting black-box LLM arithmetic, ClaimGuard uses a two-stage hybrid architecture:
1. **Multimodal Perception (Gemma 4 / Gemini):** Reads messy, faded, or handwritten receipts and extracts structured JSON evidence (`provider_name`, `date`, `currency`, `items`, `total_extracted`).
2. **Deterministic Code Verification (Python Engine):** Validates arithmetic sums, cross-references an immutable SQLite ledger for exact duplicate image submissions (SHA-256), applies currency conversions, and enforces configurable policy limits (e.g. corporate expense caps or hospital room-rent limits).

---

## Key Features

- **Multimodal Perception:** Prompt-engineered Gemma 4 extraction with prompt-injection defenses (untrusted document sandboxing).
- **Graceful Server-Side Fallback:** Automatically switches to structured offline mock mode when offline or without an API key, ensuring reliable demo and review execution.
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
[Gemma 4 Multimodal]     [Deterministic Verification]
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

# Configure environment (optional - runs in mock fallback mode if omitted)
$env:GEMINI_API_KEY = "your-gemini-api-key"
$env:GEMMA_MODEL = "gemma-4-26b-a4b-it"

# Start FastAPI server
python -m uvicorn backend.main:app --reload --port 8000
```

Verify backend health: [http://localhost:8000/api/health](http://localhost:8000/api/health)

### 2. Seed Demo Claims (Optional)

To populate the local ledger with 4 representative demo claims (corporate expenses and hospital bills):

```bash
python -m backend.scripts.seed_demo_claims
```

### 3. Frontend Setup & Run

In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## Running Automated Tests

Run the complete backend test suite from the repository root:

```bash
python -m pytest -v
```

All 13+ tests run against isolated temporary SQLite databases to prevent cross-test contamination.

---

## API Summary

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Service health status |
| `POST` | `/api/validate` | Upload image (`file`, `domain_mode`, `rule_settings`) for validation |
| `GET` | `/api/claims` | List all historical claims from SQLite ledger |
| `POST` | `/api/claims/{id}/decision` | Record manager review (`{"decision": "Approved"}`) |
| `GET` | `/api/export.csv` | Download sanitised CSV audit trail |

Refer to [API_STYLE_GUIDE.md](file:///c:/Users/Vansh/OneDrive/Desktop/New%20folder%20%282%29/API_STYLE_GUIDE.md) and [CONTRACTS.md](file:///c:/Users/Vansh/OneDrive/Desktop/New%20folder%20%282%29/CONTRACTS.md) for full schemas.
