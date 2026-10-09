# ClaimGuard Master Project Tracker

This is the shared progress board. Check `origin/master`, `git status -sb`, and this file before each iteration. Each owner updates only their own lane after a pushed checkpoint.

---

## Strategic Product Architecture: ClaimGuard — Your Claims Companion & Benefit Navigator
- **Core Promise**: Know what your policy says, what your documents prove, what may be missing, and what to do next — with evidence for every important result.
- **Differentiator**: Structured verification pipeline (Multimodal Gemma 4 extraction + Local Insurer Knowledge + Deterministic Python rules + Calendar Reminders + ScamCheck).

---

## Person A: Vansh — Backend, AI, Engine, Contracts, Integration (Branch: `feat/core-ai`)

### A1: Antigravity Lane — Core Agent, Hybrid Engine & Knowledge Base
- [x] Build FastAPI application with SQLite (WAL mode, connection timeouts, retries).
- [x] Support `expense` and `health_insurance` claim domains.
- [x] Build deterministic math, policy, currency, and duplicate-image SHA-256 checks.
- [x] Persist claims in SQLite and expose claims, decision, and CSV APIs.
- [x] Create Agent Skill and test suite (21/21 passing tests).
- [x] Align stable backend contract on `POST /api/validate` returning `perception` and `validation`.
- [x] **Local Insurer Knowledge Base**: Build markdown knowledge base (`backend/knowledge/`) for HDFC ERGO, Star Health, Niva Bupa, Care Health, ICICI Lombard, and SBI General with real-world claim repudiation traps (lifestyle/smoking disclosures, room rent proportional deductions, 15-bed minimums, consumables exclusions).
- [x] **Benefit & Deadline Calendar Engine**: Generate RFC 5545 `.ics` calendar files (`GET /api/claims/{id}/calendar.ics`) for 30-day document submission cutoff, 7-day TPA follow-up, and 90-day post-hospitalization bills.
- [x] **ScamCheck Engine**: Analyze SMS, email, and WhatsApp messages for insurance refund fee extortion (`POST /api/scamcheck`) referencing IRDAI Bima Bharosa warnings.
- [x] **Hybrid Gemma Architecture**: Support Cloud Gemma 4, Local Ollama open-source Gemma (`http://localhost:11434`), and offline structured mock fallback with `GET /api/model/status`.

### A2: Codex Lane — Parallel Scripting & Hardening
- [x] Seed realistic demo claims idempotently (`backend/scripts/seed_demo_claims.py`).
- [x] Sanitize CSV export against spreadsheet formula injection (`'=...`).
- [x] Expose insurer knowledge endpoints (`GET /api/insurers`, `GET /api/insurers/{key}`).
- [ ] Codex Task 1: Insurer policy checklist validator script (`backend/scripts/validate_insurer_knowledge.py`).
- [ ] Codex Task 2: Local Ollama vs Cloud Gemma benchmark utility (`backend/scripts/benchmark_gemma.py`).

---

## Person B: Teammate — Frontend UI, Browser Testing, Polish (Branch: `feat/frontend`)

### B1: Core Upload Flow & Claim Verification Workspace
- [ ] Update `frontend/src/api.js` to implement standard API functions (`validateDocument`, `fetchClaims`, `checkScamMessage`, etc.).
- [ ] Build dual domain mode selector: **Corporate Expense Check** vs **Health Insurance Claim Readiness**.
- [ ] Render `perception.structured_data` (provider, patient, line items, amounts) and `validation.results` with visual status badges (Green = Verified, Amber = Review Flag, Red = Rejected).
- [ ] Display deterministic calculations with "How was this calculated?" breakdown (e.g. room rent cap, non-payable consumables).

### B2: Personal Claims Companion Features & Polish
- [ ] **Benefit & Deadline Calendar UI**: Add "Download Calendar Reminder (.ics)" button on claim cards to export RFC 5545 reminders for Google Calendar/Outlook.
- [ ] **ScamCheck Tab**: Simple interface to paste suspicious SMS/email/WhatsApp messages and display real-time risk score, red flags, and IRDAI Bima Bharosa guidance.
- [ ] **Policy Gotcha & Insurer Guide**: Interactive drawer or panel showing insurer-specific claim traps (e.g., HDFC ERGO smoking disclosure, Star Health room rent caps).
- [ ] **AI Model Status Badge**: Live status indicator (Cloud Gemma 4 / Local Ollama Gemma / Offline Ready).
- [ ] Run browser testing (`npm run build`, responsive viewports) and verify no console errors.

---

## Shared Contract Rules
- `POST /api/validate` is the stable upload endpoint.
- Responses use `perception` and `validation`; frontend code reads extracted fields from `perception.structured_data`.
- Person A changes `backend/`, API contracts, tests, and skills on `feat/core-ai`.
- Person B changes `frontend/` and UI polish on `feat/frontend`.
- Contract changes require a documented update to `CONTRACTS.md` and confirmation from both teammates.
