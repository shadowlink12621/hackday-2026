# ClaimGuard Master Project Tracker

This is the unified project tracking board for the ClaimGuard team.

---

## Strategic Product Architecture: ClaimGuard — Your Claims Companion & Benefit Navigator
- **Core Promise**: Know what your policy says, what your documents prove, what may be missing, and what to do next — with evidence for every important result.
- **Differentiator**: Structured verification pipeline (Multimodal Gemma 4 extraction + Local Insurer Knowledge + Deterministic Python rules + Calendar Reminders + ScamCheck + Interactive Gemma 4 Claim Chat).

---

## Person A — Backend, AI, Engine & Integration (Branch: `feat/core-ai`)

### Stage 1: Core Perception and Validation Engine
- [x] Build the FastAPI application and Gemini/Gemma extraction client.
- [x] Support corporate expense and health insurance domains.
- [x] Implement deterministic math, currency, policy, and duplicate-image SHA-256 checks.
- [x] Add Pydantic extraction and validation schemas with a working fallback mode.
- [x] Write baseline engine tests and the Agent Skill.

### Stage 2: Storage and Workflow APIs
- [x] Persist claims in SQLite and expose the claims history API (`GET /api/claims`).
- [x] Add manager approve/reject decisions (`POST /api/claims/{id}/decision`).
- [x] Add the CSV audit export endpoint with formula-injection sanitization (`GET /api/export.csv`).
- [x] Standardize upload contract on `POST /api/validate` returning `perception` and `validation`.

### Stage 3: Hardening and Edge Cases
- [x] Enforce bounded PDF (20 MB), JPEG/PNG (5 MB), and MIME/signature checks at validation.
- [x] Handle transient SQLite lock errors with WAL mode and retry decorator.
- [x] Test health, validation, claims, decisions, CSV export, and lock retry behavior (21/21 tests passing).
- [x] Clean up backend code and verify fallback behavior.

### Stage 4: Companion Features & Local Knowledge
- [x] **Local Insurer Knowledge Base**: Build markdown knowledge base (`backend/knowledge/`) for HDFC ERGO, Star Health, Niva Bupa, Care Health, ICICI Lombard, and SBI General with real-world claim repudiation traps (lifestyle/smoking disclosures, room rent proportional deductions, 15-bed minimums, consumables exclusions).
- [x] **Benefit & Deadline Calendar Engine**: Generate RFC 5545 `.ics` reminders (`GET /api/claims/{id}/calendar.ics`); generic intervals are now labeled provisional, not statutory or policy deadlines.
- [x] **ScamCheck Engine**: Analyze SMS, email, and WhatsApp messages for insurance refund fee extortion (`POST /api/scamcheck`) referencing IRDAI Bima Bharosa warnings.
- [x] **Hybrid Gemma Architecture**: Support Cloud Gemma 4, Local Ollama open-source Gemma (`http://localhost:11434`), and a non-fabricating offline unavailable state with `GET /api/model/status`.
- [x] **Interactive Claim Chat**: Add `POST /api/chat` to allow conversational Q&A with Gemma about specific audited claims.
- [x] **Developer Scripts**:
  - `backend/scripts/validate_insurer_knowledge.py`: Validates all 6 insurer trap files.
  - `backend/scripts/benchmark_gemma.py`: Multi-tier benchmark utility for Gemma.
  - `backend/scripts/validate_cli.py`: Standalone CLI claim validator.

### Stage 5: User Policy Ingestion & Evidence Chat
- [x] Add bounded PDF ingestion and page-by-page text extraction in `backend/policy_store.py`.
- [x] Store extracted policy text locally; deduplicate repeat uploads and do not retain source PDF bytes.
- [x] Add retrieval-backed profile and policy chat APIs with page citations.
- [x] Keep offline replies extractive and explicit when no language model is available.
- [x] Add source-backed policy UI and detailed Person B handoff.
- [x] Replace the four-topic sample profile with an upload-derived 15-topic evidence profile.
- [x] Add local patient cases with isolated case metadata, document uploads/downloads, and case-linked policy indexing.
- [x] Make offline extraction report “Not extracted” with zero confidence instead of fake sample patients/bills.
- [x] Add explicit-consent, redacted whole-policy outline generation with schema validation and page citations.
- [x] Load model credentials from ignored `.env`; do not commit keys.
- [x] Verify case/document APIs and the local 59-page SBI policy using temporary DB/storage; profile returns indexed evidence and chat citations.
- [x] Verify no-model claim uploads cannot be marked approved; backend suite currently 33 passing.
- [ ] Verify a live Gemma model request with the local API key.
- [x] Replace in-progress sample policy/patient/chat UI with empty states, case selection, API-backed policy/documents, source citations, runtime status, and cloud-consent controls.
- [x] Remove canned scam/policy fallback answers; support PDF/JPEG/PNG claim documents with per-format limits and explicit cloud consent.
- [x] Add opt-in cloud OCR for scanned claim PDFs; searchable claim PDFs use local extraction with mandatory human-review flag.
- [x] Persist a user-confirmed reminder date on its patient case; never calculate an unverified deadline.
- [x] Add optional shared-token API auth and a browser token gate; production mode fails closed if the token is missing.
- [ ] Add cited, consent-based medical-record interpretation and robust insured-member identity extraction; not included in this merge because extracted health identity must be handled locally or under clear consent.
- [ ] Verify a live Gemma response after restarting the backend with the updated model selection.

---

## Person B — Frontend, Browser Testing, and Deployment (Branch: `feat/frontend`)

### Stage 1: Frontend Scaffold and API-Connected UI
- [x] Build the React/Vite claim upload interface with expense and health insurance modes.
- [x] Render extracted claim details, policy checks, and validation status.
- [x] Organize interface into reusable components (`UploadZone`, `ResultsDashboard`, `HistoryTable`, `Header`, `ErrorBoundary`, `AnalyticsChart`, `ChatInterface`).

### Stage 2: Claims Workflow & Analytics Dashboard
- [x] Load and display claim history in real-time.
- [x] Add manager approve/reject actions with visual status badges.
- [x] Add CSV audit export download button.
- [x] Interactive Recharts analytics breakdown of claims.
- [x] Gemma 4 interactive chat interface for claim inquiries.

### Stage 3: Browser E2E Testing
- [x] Configure Playwright to run the frontend locally in Chromium.
- [x] Test an approved corporate expense and a flagged health insurance claim with mocked API responses.
- [x] Test CSV download and display of backend validation errors.
- [x] Run the focused case/policy/chat browser flow successfully after integration.
- [ ] Rerun all Playwright cases; the constrained Windows runner crashed Chromium workers for memory, though the focused case/policy test passed.

### Stage 4: Local Docker Deployment
- [x] Add multi-stage frontend Dockerfile (Vite build + static server on port 5173).
- [x] Add backend Dockerfile (Python 3.11 on port 8000).
- [x] Add `docker-compose.yml` with persistent volume and health check.
- [x] Add DigitalOcean App Platform deployment configuration (`do-app.yaml`).

### Stage 5: Patient Case & Policy Outline
- [x] Build API-backed patient registration and per-case local document storage.
- [x] Replace placeholder policy facts and chat answers with uploaded-policy evidence, cited chat, and explicit cloud consent.
- [x] Remove static scam examples and canned fallback verdicts.
- [x] Add case-persisted user-confirmed date and `.ics` export without assuming a statutory/policy deadline.
- [ ] Merge these UI changes from `feat/core-ai` into `feat/frontend` so Person B can continue demo polish.

---

## How to Run the Unified Application

### Local Development (Recommended)
1. **Backend**:
   ```bash
   python -m uvicorn backend.main:app --reload --port 8000
   ```
2. **Frontend**:
   ```bash
   npm --prefix frontend run dev
   ```
3. Open `http://localhost:5173` in your browser. Backend healthcheck is at `http://localhost:8000/api/health`.

### Docker Deployment
```bash
docker compose up --build
```
