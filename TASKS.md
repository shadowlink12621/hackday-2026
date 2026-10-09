# Task Assignments & Build Flow

## Person A (Backend & Core)
- [ ] Connect Gemma 4 API (via Gemini proxy).
- [ ] Implement `backend/gemma_client.py` and strict Pydantic schemas.
- [ ] Implement `backend/engine.py` (Deterministic Rules).
- [ ] Set up tests for fallback/mock mode.
- [ ] Package the logic into `skills/hackday-core/SKILL.md` (Agent Skill Standard).

## Person B (Frontend & Demo)
- [ ] Implement Vite + React upload dashboard (`frontend/`).
- [ ] Connect `api.js` to `POST /api/process`.
- [ ] Render telemetry (metadata, latency, confidence, verification passes/fails).
- [ ] Setup fallback demo flow.
- [ ] Take screenshots and polish `README.md`.

## Execution Plan
1. **Freeze MVP** (15 mins after drop)
2. **Core Build** (E2E Pipeline)
3. **Expansion** (Add one differentiator)
4. **Freeze & Polish** (Final testing & demo rehearsal)
