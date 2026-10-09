# Task Assignments & Build Flow

## Person A (Backend & Core)
- [x] Connect the Gemini SDK with server-side model configuration and fallback mode.
- [x] Implement `backend/gemma_client.py` and strict Pydantic schemas.
- [x] Implement `backend/engine.py` with deterministic rules and SQLite claim storage.
- [x] Set up tests for fallback/mock mode.
- [x] Package the logic into `skills/expense-claim-audit/SKILL.md` (Agent Skill Standard).
- [x] Align the validation endpoint and response key with `AGENTS.md`.
- [ ] Add database-lock handling and endpoint smoke tests.

## Person B (Frontend & Demo)
- [x] Initialize Vite + React in `frontend/`.
- [x] Build the upload flow with expense/health-insurance selection.
- [x] Connect `api.js` to `POST /api/validate`.
- [x] Render telemetry, confidence, validation rules, and approval status.
- [ ] Connect claim history, reviewer decisions, and CSV export.
- [ ] Browser-test the responsive flow and polish the demo.

## Execution Plan
1. **Freeze MVP** (15 mins after drop)
2. **Core Build** (E2E Pipeline)
3. **Expansion** (Add one differentiator)
4. **Freeze & Polish** (Final testing & demo rehearsal)
