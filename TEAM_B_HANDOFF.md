# Hack Day Master Plan: ClaimGuard (Personal Claims Companion & Benefit Navigator)
**Track:** Best Open-Source AI Project & Best Use of Gemma 4

---

## 1. The Big Picture
ClaimGuard has expanded from a simple receipt checker into a full **Personal Claim Companion & Benefit Navigator**:
1. **Document Workspace & Audit Engine**: Multimodal extraction + deterministic policy engine (reconciles line items, room rent caps, non-payable consumables, duplicate receipts).
2. **Local Insurer Knowledge Base**: Real-world claim repudiation traps (HDFC ERGO, Star Health, Niva Bupa, Care Health, ICICI Lombard, SBI General). Catches lifestyle/smoking non-disclosures, room rent proportional deductions, 15-bed registered hospital requirements, and non-medical consumables.
3. **Benefit & Deadline Calendar**: Generates RFC 5545 `.ics` reminder files. Dates are provisional until confirmed from the user's policy or entered by the user; do not label generic intervals as statutory deadlines.
4. **ScamCheck**: Analyzes suspicious SMS/email/WhatsApp messages for fee-to-release claim scams referencing official IRDAI Bima Bharosa alerts.
5. **3-Tier AI Engine**: Cloud Gemma 4 -> Local Offline Ollama (`http://localhost:11434`) -> Deterministic Fallback Mock.

---

## 2. 👨‍💻 PERSON A STATUS (Backend - Python/FastAPI)
* **Stage 1 (Core AI & Multimodal Engine)**: ✅ Complete
* **Stage 2 (Storage & Workflow APIs)**: ✅ Complete (`POST /api/validate`, `GET /api/claims`, `POST /api/claims/{id}/decision`, `GET /api/export.csv`)
* **Stage 3 (Hardening & Edge Cases)**: ✅ Complete (5MB limit, WAL mode, SQLite busy retry, 21/21 pytest tests passing)
* **Stage 4 (Companion Features & Local Knowledge)**: ✅ Complete
  - `backend/knowledge/*.md` (6 top Indian insurers)
  - `GET /api/claims/{id}/calendar.ics`
  - `POST /api/scamcheck`
  - `GET /api/insurers` & `GET /api/insurers/{key}`
  - `GET /api/model/status`
* **Stage 5 (Policy PDF Retrieval & Evidence Chat)**: Backend implemented on this branch; frontend APIs and acceptance checks are described below.
* **Current Backend Branch**: `feat/core-ai`

---

## 3. 👨‍💻 PERSON B DIVISION (Frontend - Vite/React & UI Polish)
**Branch:** `feat/frontend`
**Base URL:** `http://localhost:8000/api` or `import.meta.env.VITE_API_BASE_URL`

> The policy companion work below supersedes the earlier generic policy-guide screen. The local source policy and redacted UI fixture are documented in `CLAIMGUARD_SAMPLE_POLICY_UI_PROFILE.md`; shared sequencing and ownership are in `CLAIMGUARD_UPDATED_TEAM_PLAN.md`.

### Person B - Policy Profile, Evidence Chat, and Reminder UI (Frontend Only)

Use branch `feat/frontend`. Do not edit backend files. The API is implemented by Person A on `feat/core-ai`; sync that branch through the agreed master integration before connecting it.

1. Add a separate policy PDF upload action calling `POST /api/policies` with multipart field `file`. Keep the existing claim-image control restricted to JPG/PNG; policy PDFs must not be sent to `POST /api/validate`. Show indexing progress and errors for invalid, encrypted, oversized, or scanned PDFs.
2. After upload, call `GET /api/policies/{policy_id}` and render insurer, filename, page count, and `profile` facts. Each fact has `topic`, `pages`, `evidence`, and `status`; show citations as 1-based PDF page numbers and flag `conflict_review` for human review.
3. Add a policy question panel calling `POST /api/policies/{policy_id}/chat` with `{"question":"..."}`. Render `answer`, `model_used`, and every `citations[].page` plus excerpt. No source result means no confident policy answer.
4. Read `GET /api/model/status`; distinguish cloud Gemma, reachable local Ollama, and offline retrieval-only mode. Do not describe retrieval-only output as a model response.
5. Keep claim reminders as importable `.ics` links. Label dates provisional and ask the user to confirm a policy deadline; the generic reminder is not a universal legal deadline.
6. Use only fictional profile details from `CLAIMGUARD_SAMPLE_POLICY_UI_PROFILE.md`. Never add the original PDF or its identifiers to screenshots, fixtures, or Git.
7. Replace the current hard-coded “Gemma 2.5 Flash” hero label with runtime status. Show Gemma 4 only when the model status and configured model support that claim.

#### Acceptance Checks

- Cataract card cites page 9; refractive-error card cites pages 4 and 35; OPD/optical card cites pages 3 and 25.
- Room-rent card shows a conflict warning and does not choose a cap.
- Chat answers show page citations, and a no-evidence question says the policy text was not found.
- Offline state is honest and useful; cloud state is visibly identified.
- Frontend build and browser tests pass on `feat/frontend`.

### Copy & Paste Prompt for Codex (Person B Implementation):

```text
SENIOR DEVELOPER PROMPT FOR CODEX (CLAIMGUARD COMPANION FRONTEND & WORKFLOW):

Role: Senior Frontend Engineer on ClaimGuard.
Repository: React / Vite application located in `frontend/`.
Branch: `feat/frontend`
Model Recommendation: 5.6 Luna (balanced speed, UI design quality, and low credit cost)

OBJECTIVE:
Transform the ClaimGuard frontend into a full Personal Claims Companion & Benefit Navigator:
1. Connect to all backend workflow and companion endpoints in `frontend/src/api.js`.
2. Add a clean, responsive navigation / tab layout:
   - Tab 1: Claims Workspace & Validator (File upload, live extraction, rule breakdown, and claim history)
   - Tab 2: Benefit & Deadline Calendar (.ics download reminders)
   - Tab 3: ScamCheck (Suspicious message analyzer with IRDAI Bima Bharosa warnings)
   - Tab 4: Insurer Policy Knowledge Base (Guides & claim traps for HDFC, Star, Niva Bupa, etc.)
3. Add a live AI Model Status indicator in the top navbar (Cloud Gemma / Local Ollama / Offline Mock).

BACKEND CONTRACTS (Base URL: http://localhost:8000/api):
- POST /api/validate: FormData with file, domain_mode ('expense' | 'health_insurance'), prompt, rule_settings
- GET /api/claims: Array of claims
- POST /api/claims/{id}/decision: JSON {"decision": "Approved" | "Rejected"}
- GET /api/claims/{id}/calendar.ics: RFC 5545 .ics download attachment
- POST /api/scamcheck: JSON {"message_text": "..."} -> returns {is_suspicious, risk_score, risk_level, detected_red_flags, guidance, official_portal_link}
- GET /api/insurers: Returns {"insurers": ["hdfc_ergo", "star_health", ...]}
- GET /api/insurers/{key}: Returns {insurer_key, title, key_traps, official_portal, raw_content}
- GET /api/model/status: Returns {cloud_gemma_available, local_ollama_online, active_backend, offline_ready}
- GET /api/export.csv: Direct CSV download

IMPLEMENTATION SPECIFICATION:

1. Update `frontend/src/api.js`:
   Implement and export:
   - validateDocument(file, domainMode, prompt)
   - fetchClaims()
   - recordClaimDecision(claimId, decision)
   - checkScamMessage(messageText)
   - fetchInsurers()
   - fetchInsurerKnowledge(insurerKey)
   - fetchModelStatus()
   - getCalendarIcsUrl(claimId)
   - getExportCsvUrl()

2. Top Navbar / Header:
   - Brand: ClaimGuard (Shield icon + tagline: "Insurance Claim Readiness & Benefit Navigator")
   - Model Status Pill: Fetches `GET /api/model/status`. Shows green dot for "Cloud Gemma 4" or "Local Gemma (Ollama)", blue for "Offline Ready".
   - Navigation Tabs: [Claims Workspace, Benefits Calendar, ScamCheck, Insurer Knowledge Base].

3. Claims Workspace (Tab 1):
   - Domain Mode Selector: Toggle between "Corporate Expense Check" and "Health Insurance Claim".
   - Drag-and-drop or click-to-upload card (JPEG/PNG up to 5MB).
   - Validation Results Card:
     * Structured data fields (Provider, Patient/Employee, Date, Currency, Total).
     * Extracted Line Items table (Description, Category, Amount).
     * Deterministic Rules Checklist with color-coded badges (Green check for passed, Amber warning for review flags like room rent cap or consumables).
     * "Add to Calendar (.ics)" button next to validated claim to download reminder.
   - Claims History & Audit Table:
     * Lists past claims from `GET /api/claims`.
     * Shows ID, Date, Provider, Total, AI Status, Manager Decision.
     * Approve / Reject buttons for "Pending" claims.
     * "Export Audit CSV" button triggering download.

4. Benefits Calendar View (Tab 2):
   - Displays timeline cards for active claims:
     * 30-Day Document Filing Cutoff (Statutory deadline).
     * 7-Day Insurer/TPA Follow-up Checkpoint.
     * 90-Day Post-Hospitalization Bills Window.
   - One-click "Download Calendar Event (.ics)" for each milestone to sync with Google Calendar or Outlook.

5. ScamCheck View (Tab 3):
   - Textarea to paste SMS, email, or WhatsApp message.
   - "Analyze Message" button calling `POST /api/scamcheck`.
   - Result card showing:
     * Risk Level badge: HIGH_RISK (Red), MEDIUM_RISK (Amber), SAFE (Green).
     * Risk score (0 to 100).
     * Detected Red Flags list (e.g. upfront payment demand, OTP request).
     * Official IRDAI Guidance & Direct Link to Bima Bharosa portal.

6. Insurer Knowledge View (Tab 4):
   - Dropdown or card list of top insurers: HDFC ERGO, Star Health, Niva Bupa, Care Health, ICICI Lombard, SBI General.
   - Selecting an insurer displays:
     * Key sub-limits (Room rent cap, waiting periods).
     * Real-World Repudiation Traps (e.g., mid-policy smoking non-disclosure, 15-bed minimum hospital rule).
     * Statutory grievance escalation path.

7. Styling:
   - Deep slate/zinc modern aesthetic with subtle borders and smooth transitions.
   - Accessible contrast, clear badges, and loading spinners.

VERIFICATION:
- Run `npm --prefix frontend run build` to ensure 0 errors.
- Run `git diff --check` to ensure 0 whitespace or formatting issues.
- Commit to `feat/frontend` with descriptive commit message.
```
