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

### Core Endpoint: `POST /api/validate`
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
    "model_used": "cloud_gemma (gemma-4-26b-a4b-it)",
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
        "message": "Image SHA-256 is unique."
      },
      {
        "rule_name": "Math Verification",
        "passed": true,
        "message": "Line items sum perfectly to 250.0."
      },
      {
        "rule_name": "Policy Limit",
        "passed": true,
        "message": "Within policy limit."
      }
    ]
  }
}
```

---

### Companion Endpoint: `GET /api/claims/{claim_id}/calendar.ics`
Generates and downloads an RFC 5545 `.ics` calendar reminder file for the claim.
Tracks:
- 30-day statutory claim documents filing cutoff.
- 7-day TPA / Insurer follow-up milestone.
- 90-day post-hospitalization bills submission deadline.

* **Usage in UI:** Directly link with an `<a>` tag or `window.open(`${API_URL}/claims/${id}/calendar.ics`)`.

---

### Companion Endpoint: `POST /api/scamcheck`
Checks an SMS, email, or WhatsApp message for insurance fraud and refund fee extortion.

* **Request Type:** `POST application/json`
* **Body:** `{"message_text": "Pay fee of Rs 1500 to release claim refund..."}`
* **Response:**
```json
{
  "is_suspicious": true,
  "risk_score": 45,
  "risk_level": "HIGH_RISK",
  "detected_red_flags": [
    "🚨 UPFRONT PAYMENT DEMAND: The message asks for money/fee to release an insurance claim. According to IRDAI Bima Bharosa guidelines, insurers NEVER ask policyholders for payment to release an approved claim or bonus."
  ],
  "guidance": "DO NOT pay any money, share OTPs, or click links. Verify directly with your insurer's official helpline or register a grievance on IRDAI's Bima Bharosa portal.",
  "official_portal_link": "https://bimabharosa.irdai.gov.in"
}
```

---

### Companion Endpoint: `GET /api/insurers` & `GET /api/insurers/{insurer_key}`
Fetches local knowledge base and rejection traps for insurers: `hdfc_ergo`, `star_health`, `niva_bupa`, `care_health`, `icici_lombard`, `sbi_general`.

---

### Model Status Endpoint: `GET /api/model/status`
Returns runtime AI model status (Cloud Gemma 4 vs Local Ollama Gemma vs Offline Mock).

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

export const checkScamMessage = async (messageText) => {
  const res = await fetch(`${API_URL}/scamcheck`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message_text: messageText }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || 'Failed to analyze message');
  }
  return await res.json();
};

export const fetchInsurers = async () => {
  const res = await fetch(`${API_URL}/insurers`);
  if (!res.ok) throw new Error('Failed to fetch insurers');
  return await res.json();
};

export const fetchInsurerKnowledge = async (insurerKey) => {
  const res = await fetch(`${API_URL}/insurers/${insurerKey}`);
  if (!res.ok) throw new Error('Failed to fetch insurer details');
  return await res.json();
};

export const fetchModelStatus = async () => {
  const res = await fetch(`${API_URL}/model/status`);
  if (!res.ok) throw new Error('Failed to fetch model status');
  return await res.json();
};

export const getCalendarIcsUrl = (claimId) => `${API_URL}/claims/${claimId}/calendar.ics`;
export const getExportCsvUrl = () => `${API_URL}/export.csv`;
```

---

## 4. Branch & Collaboration Guidelines

- **Person A (Backend/AI):** Commits to `feat/core-ai`.
- **Person B (Frontend/Demo):** Commits to `feat/frontend`.
- **Merge Strategy:** After both feature branches pass verification (`pytest`, `npm run build`), merge each branch into `master` via pull request or fast-forward merge.
