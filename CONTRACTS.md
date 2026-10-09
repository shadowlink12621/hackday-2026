# API Contracts

## `POST /api/process`

**Request (FormData):**
- `prompt` (string): Context or user request.
- `file` (File, optional): Image or document upload.
- `domain_mode` (string, default: "general"): The archetype domain (e.g., "forms", "code").
- `rule_settings` (JSON string): Specific deterministic rules to apply.

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
    "structured_data": {},
    "confidence": 0.95
  },
  "verification": {
    "is_valid": true,
    "results": [
      {
        "rule_name": "Signature Check",
        "passed": true,
        "message": "Signature verified."
      }
    ]
  }
}
```
