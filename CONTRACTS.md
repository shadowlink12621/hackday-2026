# API Contracts

## `POST /api/process`

**Request (FormData):**
- `prompt` (string): Context or user request.
- `file` (File, optional): Image or document upload (`.jpg`, `.png`).
- `domain_mode` (string, default: "receipts"): The archetype domain.
- `rule_settings` (JSON string): e.g. `{"policy_limit_inr": 4000.0}`.

**Response (JSON):**
```json
{
  "metadata": {
    "model_used": "gemini-2.5-flash",
    "is_fallback_mock": false,
    "latency_ms": 1250,
    "timestamp": "2026-10-09T10:00:00Z"
  },
  "perception": {
    "structured_data": {
      "vendor_name": "Starbucks",
      "date_extracted": "2026-10-09",
      "currency": "USD",
      "items": [
        {"description": "Coffee", "amount": 5.0}
      ],
      "total_extracted": 5.0,
      "confidence_score": 0.95
    },
    "confidence": 0.95
  },
  "verification": {
    "is_valid": true,
    "final_amount_inr": 417.5,
    "results": [
      {
        "rule_name": "Fraud Detection",
        "passed": true,
        "message": "Receipt hash is unique."
      },
      {
        "rule_name": "Math Verification",
        "passed": true,
        "message": "Line items sum perfectly to 5.0."
      },
      {
        "rule_name": "Policy Limit",
        "passed": true,
        "message": "Converted 5.0 USD to 417.5 INR. Within policy limit of ₹4000.0."
      }
    ]
  }
}
```
