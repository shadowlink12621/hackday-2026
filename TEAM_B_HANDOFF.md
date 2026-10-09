# Hack Day Master Plan: ClaimGuard (Universal Claims Validator)
**Track:** Best Open-Source AI Project & Best Use of Gemma 4

## The Architecture
ClaimGuard supports **Corporate Expenses** AND **Health Insurance Claims (Indian Medical Bills)**!
1. **Frontend (Person B)**: User selects "Domain" (Expense or Health Insurance), uploads receipt/bill image, views extraction & rules, manages claim history approvals, and exports audit reports.
2. **Perception (Gemma 4)**: Extracts Vendor/Hospital, Date, Currency, Line Items (auto-categorized as 'meals', 'room_rent', 'consumables', etc.), and Total.
3. **Logic (Python)**:
   - **Fraud Check**: SHA-256 SQLite lookup for duplicate images with concurrency lock handling.
   - **Expense Math**: Converts USD/EUR to INR, checks ₹4000 limit.
   - **Health Math**: Checks if Room Rent > ₹10,000 and denies non-medical consumables.
   - **Storage & Workflow**: Stores claims in SQLite, supports manager review decisions and CSV audit export.
4. **Dashboard**: Person B displays the results, live audit history table, approve/reject action buttons, and an Export to CSV button.

---

## 👨‍💻 PERSON A STATUS (Backend - Python/FastAPI)
* **Stage 1 (Core AI & Rules)**: ✅ Complete
* **Stage 2 (Storage & Workflow APIs)**: ✅ Complete (`POST /api/validate`, `GET /api/claims`, `POST /api/claims/{id}/decision`, `GET /api/export.csv`)
* **Stage 3 (Hardening & Edge Cases)**: ✅ Complete (5MB / MIME validation, WAL mode, SQLite lock retry decorator, 100% pytest coverage)
* **Latest Checkpoint**: `b7a7d79` on `feat/core-ai`

---

## 👨‍💻 PERSON B DIVISION (Frontend - Vite/React & Deployment)
**@Teammate: Copy the block below and paste it directly into Codex to execute Stage 2!**

```text
SENIOR DEVELOPER PROMPT FOR CODEX (STAGE 2 - FRONTEND WORKFLOW & AUDIT DASHBOARD):

Role: Senior Frontend Engineer on ClaimGuard.
Repository: React / Vite application located in `frontend/`.
Branch: `feat/frontend`

OBJECTIVE:
Connect the ClaimGuard frontend to the full Stage 2 backend audit workflow:
1. Render line items table for the current analyzed document.
2. Connect to `GET /api/claims` to display real-time claim history.
3. Wire Manager "Approve" and "Reject" buttons to `POST /api/claims/{id}/decision`.
4. Wire "Export CSV" to `GET /api/export.csv`.

BACKEND API CONTRACTS (Base URL: `http://localhost:8000/api` or `VITE_API_BASE_URL`):

1. `POST /api/validate` (Already wired in Stage 1)
   - Payload: FormData with `file`, `domain_mode` ('expense' | 'health_insurance'), `prompt`
   - Returns:
     {
       "claim_id": 1,
       "metadata": { "model_used": "...", "domain": "...", "latency_ms": 120 },
       "perception": {
         "structured_data": {
           "provider_name": "Apollo Hospitals",
           "patient_or_employee_name": "Rahul Sharma",
           "currency": "INR",
           "items": [
             { "description": "Room Rent", "amount": 8000, "category": "room_rent" }
           ],
           "total_extracted": 8000,
           "confidence_score": 0.95
         },
         "confidence": 0.95
       },
       "validation": {
         "is_valid": true,
         "final_amount_inr": 8000,
         "results": [
           { "rule_name": "Fraud Detection", "passed": true, "message": "Document hash is unique." }
         ]
       }
     }

2. `GET /api/claims`
   - Returns JSON Array of all claims (newest first):
     [
       {
         "id": 1,
         "domain": "expense",
         "total_inr": 417.5,
         "is_valid": true,
         "status": "Pending", // "Pending" | "Approved" | "Rejected"
         "extracted_data": { "provider_name": "...", "items": [...], ... },
         "validation_data": { "is_valid": true, "results": [...] },
         "timestamp": "2026-10-09 10:00:00"
       }
     ]

3. `POST /api/claims/{claim_id}/decision`
   - Request Body: JSON `{"decision": "Approved"}` or `{"decision": "Rejected"}`
   - Response: `{"status": "success", "claim_id": 1, "decision": "Approved"}`

4. `GET /api/export.csv`
   - Downloads `claimguard_audit.csv` with columns: ID, Timestamp, Domain, Total_INR, System_Valid, Manager_Status, Vendor/Hospital.

IMPLEMENTATION STEPS:

1. Update `frontend/src/api.js`:
   - Keep `validateDocument(file, domainMode)`.
   - Add `fetchClaims()`: Calls `GET ${API_URL}/claims`, returns array of claims.
   - Add `recordClaimDecision(claimId, decision)`: Calls `POST ${API_URL}/claims/${claimId}/decision` with JSON `{"decision": decision}`.
   - Add `exportClaimsCsv()`: Initiates file download of `${API_URL}/export.csv` or fetches blob and triggers link click.

2. Update `frontend/src/App.jsx`:
   - State additions:
     * `claimsHistory`: Array of past claims.
     * `historyLoading`: Boolean for history fetch spinner.
     * `actionLoadingId`: Tracks which claim ID currently has an approve/reject request in-flight.
   - Auto-fetch history on mount using `useEffect`.
   - Auto-refresh history after:
     * A successful document validation (`handleAnalyze`).
     * A manager decision (`handleDecision`).
   - Line Items Table for Current Scan:
     * Under "Telemetry & Validation", add an "Extracted Line Items" table displaying `item.description`, `item.category`, and `item.amount`.
   - Claims History / Audit Section:
     * Place below or beside the main scanner panels (or in a clean tabbed view).
     * Header with "Claim History & Review Workflow" + "Export Audit CSV" button.
     * Table with columns: ID, Timestamp, Domain, Amount (INR), AI Validation (Valid/Invalid badge), Manager Status (Pending: yellow, Approved: green, Rejected: red), and Actions.
     * If status === 'Pending': Render "Approve" (green button) and "Reject" (red button).
     * If status !== 'Pending': Display settled badge with no action buttons.

3. Styling Polish (`frontend/src/index.css` or `frontend/src/App.css`):
   - Maintain the premium dark theme (deep slate background, crisp typography, subtle borders, glass cards).
   - Add styles for:
     * `.items-table`: Clean table styling with rounded corners, alternating row tints.
     * `.badge-pending`: Amber/yellow badge.
     * `.badge-approved`: Emerald green badge.
     * `.badge-rejected`: Crimson red badge.
     * Action button group with hover states and disabled states during loading.

4. Verification & Git Commit:
   - Run `npm --prefix frontend run build` to verify clean build without JSX/lint errors.
   - Run `git diff --check` to verify no whitespace or merge issues.
   - Commit with message:
     `git commit -m "feat(frontend): connect claim history, manager decisions, and CSV export"`
   - Push to `origin/feat/frontend`.
```
