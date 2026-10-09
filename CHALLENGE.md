# ClaimGuard (Policy & Expense Validator)

## Archetype
We are building **ClaimGuard** (aka BillBuddy), an enterprise-grade AI expense validator. It takes messy, crumpled receipts and strictly validates them against corporate policy using Gemma 4 for perception and Python for deterministic math/fraud detection.

## The Split
1. **Gemma's Exact Job (Perception):**
   * Uses Multimodal reasoning to read crumpled, faded, or handwritten receipts (`.jpg` or `.png`).
   * Extracts vendor name, date, currency, and an array of line items with their amounts into strict JSON.
2. **Deterministic Engine's Exact Job (Validation):**
   * **Fraud Detection**: Computes a SHA-256 hash of the image and checks a local SQLite DB for duplicates.
   * **Currency Orchestration**: Converts foreign currency to INR.
   * **Policy Limit**: Sums the line items and fails the claim if the total exceeds company policy (e.g., ₹4000).
