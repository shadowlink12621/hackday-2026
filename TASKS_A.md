# Person A (Backend & AI) Master Checklist

This checklist tracks the exact backend steps from scratch to completion, ensuring no git conflicts with Person B (who strictly stays in `frontend/`).

## Stage 1: Core Perception & Validation Engine ✅ (DONE)
- [x] Scaffold FastAPI app (`main.py`).
- [x] Connect `google-genai` SDK and enforce Pydantic schemas (`gemma_client.py`).
- [x] Support multiple domains (Corporate Expense vs Health Insurance).
- [x] Implement deterministic Python rules (Math, Currency).
- [x] Implement SQLite image hashing for duplicate fraud detection (`engine.py`).
- [x] Write baseline `pytest` suite.

## Stage 2: Storage & Workflow APIs ✅ (DONE)
Currently, we only process the image and return JSON. The ChatGPT plan requires us to actually save the claims so managers can review them and export them!
- [x] Upgrade SQLite schema to store full claims (ID, Domain, Extracted JSON, Status: Pending/Approved/Rejected).
- [x] Update `POST /api/process` to save the claim to the DB and return the `claim_id`.
- [x] Implement `GET /api/claims` (Fetch all claims for the dashboard).
- [x] Implement `POST /api/claims/{id}/decision` (Manager clicks Approve or Reject).
- [x] Implement `GET /api/export.csv` (Download audit report).

## Stage 3: Hardening & Edge Cases 🤖 (CODEX WILL DO THIS LATER)
Once Antigravity finishes Stage 2, you will hand these steps to Codex 5.5:
- [ ] Add strict file-size validation (reject files > 5MB) and MIME-type checks (`.jpg`, `.png` only) to the FastAPI endpoints.
- [ ] Add exception handling for database locks.
- [ ] Expand `backend/tests/test_engine.py` to test the new `/api/claims` and `/api/export.csv` endpoints.
- [ ] Final code cleanup and PEP8 formatting.
