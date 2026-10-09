# API Contracts (ClaimGuard Companion & Engine)

All endpoints conform to strict enterprise standards. The core contract `POST /api/validate` remains 100% stable with consistent `perception` and `validation` blocks.

---

## 1. `POST /api/validate`
Upload an image and run multimodal extraction + deterministic policy engine validation.

**Request (`multipart/form-data`):**
- `prompt` (`string`, optional): Context hints or claim notes.
- `file` (`File`, required): Supported formats: `.jpg`, `.jpeg`, `.png` (Max size: 5 MB).
- `domain_mode` (`string`, required): `"expense"` or `"health_insurance"`.
- `rule_settings` (`string`, optional JSON): e.g. `{"policy_limit_inr": 50000.0, "require_all_fields": true}`.

**Response (`application/json`):**
```json
{
  "claim_id": 5,
  "metadata": {
    "model_used": "cloud_gemma (gemma-4-26b-a4b-it)",
    "is_fallback_mock": false,
    "latency_ms": 1420,
    "timestamp": "2026-10-09T08:15:00.000000+00:00",
    "domain": "health_insurance"
  },
  "perception": {
    "structured_data": {
      "provider_name": "Apollo Hospitals",
      "patient_or_employee_name": "Rahul Sharma",
      "date_extracted": "2026-10-09",
      "currency": "INR",
      "items": [
        {"description": "ICU Room Rent (2 days)", "amount": 20000.0, "category": "room_rent"},
        {"description": "Surgical Consumables", "amount": 3500.0, "category": "consumables"},
        {"description": "Surgeon Fee", "amount": 45000.0, "category": "doctor_fee"}
      ],
      "total_extracted": 68500.0,
      "confidence_score": 0.94
    },
    "confidence": 0.94
  },
  "validation": {
    "is_valid": false,
    "final_amount_inr": 68500.0,
    "results": [
      {
        "rule_name": "Mandatory Fields",
        "passed": true,
        "message": "All required fields (vendor, date, total) are present."
      },
      {
        "rule_name": "Currency Verification",
        "passed": true,
        "message": "Currency 'INR' verified."
      },
      {
        "rule_name": "Non-Medical Consumables Audit",
        "passed": false,
        "message": "⚠️ 1 non-payable item(s) found (total: ₹3500.00). Consumables are excluded under standard IRDAI guidelines unless Consumables Rider is active."
      },
      {
        "rule_name": "Exact Duplicate Submission (SHA-256)",
        "passed": true,
        "message": "Image SHA-256 is unique."
      }
    ]
  }
}
```

---

## 2. `GET /api/claims`
Fetch all processed claims for the dashboard workspace.

**Response (`application/json`):**
```json
[
  {
    "id": 1,
    "domain": "expense",
    "total_inr": 450.0,
    "is_valid": true,
    "status": "Approved",
    "extracted_data": { ... },
    "validation_data": { ... },
    "timestamp": "2026-10-09 10:00:00"
  }
]
```

---

## 3. `POST /api/claims/{claim_id}/decision`
Record a manager or user decision for an audited claim.

**Request (`application/json`):**
```json
{ "decision": "Approved" } // or "Rejected"
```
**Response (`application/json`):**
```json
{ "status": "success", "claim_id": 1, "decision": "Approved" }
```

---

## 4. `GET /api/claims/{claim_id}/calendar.ics`
Generates and downloads an RFC 5545 `.ics` calendar reminder file for the claim.
Tracks:
- 30-day statutory claim documents filing cutoff.
- 7-day TPA / Insurer follow-up milestone.
- 90-day post-hospitalization bills submission deadline.

**Response:**
- `Content-Type: text/calendar`
- `Content-Disposition: attachment; filename=claimguard_claim_{id}.ics`

---

## 5. `POST /api/scamcheck`
Analyzes SMS, email, or WhatsApp messages for insurance fraud and refund fee extortion.
Cross-references official IRDAI Bima Bharosa warnings.

**Request (`application/json`):**
```json
{
  "message_text": "Your claim refund of Rs 50,000 is ready. Pay processing fee of Rs 1,500 to release funds via UPI."
}
```

**Response (`application/json`):**
```json
{
  "is_suspicious": true,
  "risk_score": 45,
  "risk_level": "HIGH_RISK",
  "detected_red_flags": [
    "🚨 UPFRONT PAYMENT DEMAND: The message asks for money/fee to release an insurance claim. According to IRDAI Bima Bharosa guidelines, insurers NEVER ask policyholders for payment to release an approved claim or bonus."
  ],
  "guidance": "DO NOT pay any money, share OTPs, or click links. Verify directly with your insurer's official helpline or register a grievance on IRDAI's Bima Bharosa portal.",
  "official_portal_link": "https://bimabharosa.irdai.gov.in",
  "regulatory_reference": "IRDAI Consumer Protection Notice (No fee required for claim settlement)"
}
```

---

## 6. `GET /api/insurers` & `GET /api/insurers/{insurer_key}`
Retrieve local insurer knowledge base entries (sub-limits, waiting periods, rejection traps).

- `GET /api/insurers` returns `{"insurers": ["care_health", "hdfc_ergo", "icici_lombard", "niva_bupa", "sbi_general", "star_health"]}`
- `GET /api/insurers/hdfc_ergo` returns:
```json
{
  "insurer_key": "hdfc_ergo",
  "title": "HDFC ERGO Health Insurance Policy Rules & Rejection Gotchas",
  "key_traps": [
    "1. Lifestyle Disclosure Trap: If the insured took up smoking...",
    "2. Missing Hospital Registration Certificate...",
    "3. Non-Medical Consumables: Gloves, PPE kits...",
    "4. Claim Submission Deadline: Reimbursement claim documents must be submitted within 30 days..."
  ],
  "official_portal": "https://bimabharosa.irdai.gov.in",
  "raw_content": "# HDFC ERGO Health Insurance..."
}
```

---

## 7. `GET /api/model/status`
Returns runtime AI model status (Cloud Gemma 4 vs Local Ollama Gemma vs Offline Mock).

**Response (`application/json`):**
```json
{
  "cloud_gemma_available": true,
  "cloud_model": "gemma-4-26b-a4b-it",
  "local_ollama_online": false,
  "local_ollama_host": "http://localhost:11434",
  "local_models": [],
  "active_backend": "cloud_gemma",
  "offline_ready": true
}
```

---

## 8. `GET /api/export.csv`
Downloads an audit-compliant CSV report with formula-injection sanitization.
