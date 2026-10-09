---
name: expense-claim-audit
description: Multimodal AI agent skill for verifying corporate expenses and health insurance claims against deterministic rules.
version: 1.0.0
---

# Expense & Health Claim Audit (Agent Skill)

## Intent
This skill allows agentic systems to pass raw images (receipts or medical bills) along with domain metadata to a multimodal validation engine. Gemma 4 handles the perception (extraction), while strict Python deterministic logic enforces mathematical rules, duplicate image fraud detection (SHA-256), and industry-specific policies (like Indian Health Insurance room rent caps).

## Architecture
- **Perception:** Uses Gemma 4 to parse structured JSON from images.
- **Verification:** Runs offline Python logic (SQLite DB, Math matching, Currency exchange).

## Usage (API Contract)
Make a `POST` request to `/api/process` with a multipart form:
- `file`: The image payload (`.jpg`, `.png`).
- `domain_mode`: `"expense"` or `"health_insurance"`.
- `prompt`: Context.

Returns a detailed JSON structure containing `metadata`, AI `perception` extraction, and deterministic `verification` passes/fails.
