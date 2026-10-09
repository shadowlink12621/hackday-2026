# ClaimGuard Master Project Tracker

This is the shared progress board. Check `origin/master`, `git status -sb`, and this file before each iteration. Each owner updates only their own lane after a pushed checkpoint.

## Person A: Vansh - Backend, AI, Contracts, Integration

### A1: Antigravity Lane - Core Agent and Workflow

- [x] Build FastAPI application and Gemini extraction client.
- [x] Support `expense` and `health_insurance` claim domains.
- [x] Build deterministic math, policy, currency, and duplicate-image checks.
- [x] Persist claims in SQLite and expose claims, decision, and CSV APIs.
- [x] Create the Agent Skill and baseline engine tests.
- [x] Align the backend contract on `POST /api/validate` with `perception` and `validation`.
- [ ] Keep model configuration and fallback behavior working during final integration.

### A2: Codex Lane - Backend Hardening and Verification

- [x] Add a 5 MB request limit and JPEG/PNG MIME validation to `POST /api/validate`.
- [ ] Add recovery for temporary SQLite locking during concurrent requests.
- [ ] Add endpoint smoke tests for health, claims list, CSV export, and manager decisions.
- [ ] Run the complete backend verification flow with fallback mode.
- [ ] Integrate Person B's completed frontend only after it is merged to `master`.

## Person B: Frontend, Browser Testing, Deployment

### B1: Frontend Integration - `feat/frontend` Only

- [ ] Update `frontend/src/api.js` to send `file`, `domain_mode`, and `prompt` to `POST /api/validate`.
- [ ] Add Expense / Health Insurance domain selection to the upload flow.
- [ ] Render `perception.structured_data`, `validation.results`, and validation status.
- [ ] Add the current-document line-item table.

### B2: Claims Workflow and Demo Polish - `feat/frontend` Only

- [ ] Fetch and display `GET /api/claims` history.
- [ ] Add Approve / Reject manager actions using `POST /api/claims/{id}/decision`.
- [ ] Add the `GET /api/export.csv` download action.
- [ ] Run browser and responsive checks, then update the demo/README visuals.
- [ ] Deploy the frontend and backend to DigitalOcean and verify the live URL.

## Shared Contract Rules

- `POST /api/validate` is the stable upload endpoint.
- Responses use `perception` and `validation`; frontend code reads extracted fields from `perception.structured_data`.
- Person A changes `backend/`, API contracts, tests, and skills. Person B changes `frontend/` and deployment work.
- Contract changes require a documented update to `CONTRACTS.md` and confirmation from both people.
