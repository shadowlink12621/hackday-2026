# ClaimGuard (Policy & Expense Validator)

## Archetype
We are building **ClaimGuard** (aka BillBuddy), a universal enterprise AI claim validator for both **Corporate Expenses** and **Health Insurance**. It takes messy, unstructured receipts or medical bills and strictly validates them against corporate/insurance policy using Gemma 4 for perception and Python for deterministic math/fraud detection.

## The Split
1. **Gemma's Exact Job (Perception):**
   * Uses Multimodal reasoning to read crumpled, faded, or handwritten documents (`.jpg` or `.png`).
   * Extracts vendor/hospital name, patient/employee name, date, currency, and an array of categorized line items (meals, room_rent, consumables, etc.) into strict JSON.
2. **Deterministic Engine's Exact Job (Validation):**
   * **Fraud Detection**: Computes a SHA-256 hash of the image and checks a local SQLite DB for duplicates.
   * **Domain Rules**: Enforces specific industry rules (e.g. Health Insurance Room Rent capped at ₹10,000, or Corporate Expenses converted to INR and capped at ₹4000).
