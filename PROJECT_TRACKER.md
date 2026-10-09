# ClaimGuard Master Project Tracker

This document serves as the single source of truth for tracking progress across the team.

## 👨‍💻 PERSON A (Backend & AI) 
**Owner:** Vansh / Antigravity / Codex

### Stage 1: Core Perception & Validation Engine ✅ (DONE by Antigravity)
- [x] Scaffold FastAPI app (`main.py`).
- [x] Connect `google-genai` SDK and enforce Pydantic schemas (`gemma_client.py`).
- [x] Support multiple domains (Corporate Expense vs Health Insurance).
- [x] Implement deterministic Python rules (Math, Currency).
- [x] Implement SQLite image hashing for duplicate fraud detection (`engine.py`).
- [x] Write baseline `pytest` suite.

### Stage 2: Storage & Workflow APIs ✅ (DONE by Antigravity)
- [x] Upgrade SQLite schema to store full claims (ID, Domain, Extracted JSON, Status: Pending/Approved/Rejected).
- [x] Update `POST /api/validate` to save the claim to the DB and return the `claim_id`.
- [x] Implement `GET /api/claims` (Fetch all claims for the dashboard).
- [x] Implement `POST /api/claims/{id}/decision` (Manager clicks Approve or Reject).
- [x] Implement `GET /api/export.csv` (Download audit report).
- [x] Standardize API endpoints (e.g. `/api/validate`) and JSON payload names (`validation`) across backend and `CONTRACTS.md`.

### Stage 3: Hardening & Edge Cases ⏳ (CODEX - UP NEXT)
- [ ] Add strict file-size validation (reject files > 5MB) and MIME-type checks (`.jpg`, `.png` only) to the FastAPI endpoints.
- [ ] Add exception handling for `sqlite3.OperationalError` (database is locked).
- [ ] Expand `backend/tests/test_engine.py` to test the new `/api/claims` and `/api/export.csv` endpoints.
- [ ] Final code cleanup and PEP8 formatting.

---

## 👨‍💻 PERSON B (Frontend & Deployment)
**Owner:** Teammate / Codex

### Stage 1: Scaffold & Mock UI ⏳ (CODEX - IN PROGRESS)
- [x] Initialize React/Vite in `frontend/`.
- [ ] Build drag-and-drop file upload zone with Domain Selector (Expense vs Health).
- [ ] Build API Client (`api.js`) to send `file`, `domain_mode`, and `prompt` to `/api/validate`.
- [ ] Build Results Dashboard (Render Red/Green badges based on `response.validation.is_valid`).

### Stage 2: API Integration & Workflow
- [ ] Connect dashboard to `GET /api/claims` to fetch history.
- [ ] Add "Approve" and "Reject" buttons that call `POST /api/claims/{id}/decision`.
- [ ] Add "Export CSV" button pointing to `GET /api/export.csv`.

### Stage 3: Deployment
- [ ] Connect repository to DigitalOcean App Platform.
- [ ] Deploy Vite as a Static Site.
- [ ] Deploy FastAPI as a Python Web Service, linking `GEMINI_API_KEY`.
- [ ] End-to-end live testing before 3:30 PM deadline.
