# ClaimGuard API & Integration Style Guide

This guide ensures Person A (Backend & AI) and Person B (Frontend & Deployment) stay 100% aligned, avoid merge conflicts, and connect seamlessly.

---

## 1. Running the Backend Locally

```bash
# In the repository root
python -m uvicorn backend.main:app --reload --port 8000
```

Verify backend is healthy:
- URL: `GET http://localhost:8000/api/health`
- Response: `{"status": "ok", "service": "ClaimGuard Validation Engine"}`

CORS is configured to allow `*` (all origins, methods, and headers).

---

## 2. API Endpoints & Contract Definitions

### Base URL
- Local Dev: `http://localhost:8000/api`
- Environment Variable: `import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'`

---

### Endpoint 1: `POST /api/validate`
Uploads a receipt/invoice/medical bill image for multimodal extraction and deterministic policy validation.

* **Request Type:** `multipart/form-data`
* **Fields:**
  * `file`: (Binary / File) `.jpg`, `.jpeg`, `.png` (Max 5 MB).
  * `domain_mode`: (string) `"expense"` or `"health_insurance"`.
  * `prompt`: (string, optional) User instructions or notes.
  * `rule_settings`: (JSON string, optional) e.g., `'{"policy_limit_inr": 4000.0, "room_rent_cap_inr": 10000.0, "allow_consumables": false}'`.

* **Response Shape (JSON):**
```json
{
  "claim_id": 1,
  "metadata": {
    "model_used": "gemma-4-26b-a4b-it",
    "is_fallback_mock": false,
    "latency_ms": 350,
    "timestamp": "2026-10-09T07:00:00Z",
    "domain": "expense"
  },
  "perception": {
    "structured_data": {
      "provider_name": "Starbucks Coffee",
      "patient_or_employee_name": "John Doe",
      "date_extracted": "2026-10-09",
      "currency": "INR",
      "items": [
        {
          "description": "Latte",
          "amount": 250.0,
          "category": "meals"
        }
      ],
      "total_extracted": 250.0,
      "confidence_score": 0.95
    },
    "confidence": 0.95
  },
  "validation": {
    "is_valid": true,
    "final_amount_inr": 250.0,
    "results": [
      {
        "rule_name": "Exact Duplicate Submission (SHA-256)",
        "passed": true,
        "message": "Document hash is unique in ledger."
      },
      {
        "rule_name": "Math Verification",
        "passed": true,
        "message": "Line items sum perfectly to 250.0."
      },
      {
        "rule_name": "Policy Limit",
        "passed": true,
        "message": "Converted 250.0 INR to 250.0 INR. Within policy limit of ₹4000.0."
      }
    ]
  }
}
```

---

### Endpoint 2: `GET /api/claims`
Retrieves all historical claims stored in SQLite (newest first).

* **Request Type:** `GET`
* **Response Shape (JSON Array):**
```json
[
  {
    "id": 1,
    "domain": "expense",
    "total_inr": 250.0,
    "is_valid": true,
    "status": "Pending",
    "extracted_data": {
      "provider_name": "Starbucks Coffee",
      "patient_or_employee_name": "John Doe",
      "date_extracted": "2026-10-09",
      "currency": "INR",
      "items": [
        { "description": "Latte", "amount": 250.0, "category": "meals" }
      ],
      "total_extracted": 250.0,
      "confidence_score": 0.95
    },
    "validation_data": {
      "is_valid": true,
      "final_amount_inr": 250.0,
      "results": [...]
    },
    "timestamp": "2026-10-09 12:30:00"
  }
]
```

---

### Endpoint 3: `POST /api/claims/{claim_id}/decision`
Allows a manager to officially Approve or Reject a claim.

* **Request Type:** `POST`
* **Headers:** `Content-Type: application/json`
* **Body:**
```json
{
  "decision": "Approved"
}
```
*(Valid values for `decision`: `"Approved"` or `"Rejected"`)*

* **Response Shape (JSON):**
```json
{
  "status": "success",
  "claim_id": 1,
  "decision": "Approved"
}
```

* **Error Codes:**
  * `400 Bad Request`: When `decision` is not `"Approved"` or `"Rejected"`.
  * `404 Not Found`: When `claim_id` does not exist in SQLite.

---

### Endpoint 4: `GET /api/export.csv`
Downloads an audit report CSV of all claims.

* **Request Type:** `GET`
* **Headers returned:** `Content-Type: text/csv`, `Content-Disposition: attachment; filename=claimguard_audit.csv`
* **CSV Columns:** `ID, Timestamp, Domain, Total_INR, System_Valid, Manager_Status, Vendor/Hospital`

---

## 3. Standard Frontend Client (`frontend/src/api.js`)

Person B should implement `frontend/src/api.js` using these exact function signatures:

```javascript
const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

export const validateDocument = async (file, domainMode = 'expense', prompt = '') => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('domain_mode', domainMode);
  formData.append('prompt', prompt);

  const res = await fetch(`${API_URL}/validate`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail = data.detail || detail;
    } catch {}
    throw new Error(detail);
  }
  return await res.json();
};

export const fetchClaims = async () => {
  const res = await fetch(`${API_URL}/claims`);
  if (!res.ok) throw new Error('Failed to fetch claims');
  return await res.json();
};

export const recordClaimDecision = async (claimId, decision) => {
  const res = await fetch(`${API_URL}/claims/${claimId}/decision`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ decision }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || 'Failed to update decision');
  }
  return await res.json();
};

export const getExportCsvUrl = () => `${API_URL}/export.csv`;
```

---

## 4. Branch & Collaboration Guidelines

- **Person A (Backend/AI):** Commits to `feat/core-ai`.
- **Person B (Frontend/Demo):** Commits to `feat/frontend`.
- **Merge Strategy:** After both feature branches pass verification (`pytest`, `npm run build`), merge each branch into `master` via pull request or fast-forward merge.
