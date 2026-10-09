# API Contracts

## `POST /api/process`
Upload an image and run extraction + validation.
**Request (FormData):**
- `prompt` (string)
- `file` (File, optional): `.jpg` or `.png`
- `domain_mode` (string): `"expense"` or `"health_insurance"`
- `rule_settings` (JSON string)

**Response (JSON):**
Returns `claim_id` along with `metadata`, `perception` (extracted JSON), and `verification` (passed/failed rules).

## `GET /api/claims`
Fetch all processed claims for the dashboard.
**Response (JSON Array):**
```json
[
  {
    "id": 1,
    "domain": "expense",
    "total_inr": 417.5,
    "is_valid": true,
    "status": "Pending",
    "extracted_data": { ... },
    "verification_data": { ... },
    "timestamp": "2026-10-09 10:00:00"
  }
]
```

## `POST /api/claims/{claim_id}/decision`
Record a manager's final approval/rejection.
**Request (JSON):**
```json
{ "decision": "Approved" } // or "Rejected"
```
**Response (JSON):** `{"status": "success", "claim_id": 1, "decision": "Approved"}`

## `GET /api/export.csv`
Downloads a CSV audit report of all claims.
