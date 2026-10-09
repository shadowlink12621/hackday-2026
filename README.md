# ClaimGuard (Universal Claims AI Validator)
**Hacktoberfest Hack Day Bengaluru × IEEE CIS (October 9, 2026)**

ClaimGuard is an open-source, enterprise-grade AI expense and health insurance claim validator. It takes messy, unstructured evidence (crumpled receipts or medical bills) and strictly validates them against corporate policy.

This project targets two prize categories simultaneously:
1. **Best Use of Gemma 4:** Uses Gemma 4 Multimodal reasoning to intelligently read faded or handwritten receipts/bills and extract structured JSON (far superior to legacy OCR).
2. **Best Open-Source AI Project:** Built as a compliant **Agent Skill** following the [Agent Skills open standard](https://agentskills.io/specification). It heavily relies on AI but uses strict Python deterministic software to make the final verification.

## Architecture & The Split
- **Perception (Gemma 4):** Extracts fields, line items (categorized as meals, room rent, etc.), and currency from raw images.
- **Verification (Deterministic Python):** 
  - **Fraud Detection:** Computes a SHA-256 hash of the image and checks a local SQLite DB (`claimguard.db`) for duplicates.
  - **Multi-Currency:** Converts foreign currency to INR.
  - **Math & Policy Limits:** Validates line item sums and flags exceptions based on domain (e.g., standard ₹4000 expense limit, or ₹10,000 Health Insurance Room Rent cap).

## Running the Application
### Backend (Python)
1. `cd backend`
2. `pip install -r requirements.txt`
3. Configure your API key: `export GEMINI_API_KEY="your_key"`
4. Run the API: `python -m uvicorn backend.main:app --reload`
5. *Run tests:* `pytest backend/tests/test_engine.py`

### Frontend (React/Vite)
1. `cd frontend`
2. `npm install`
3. `npm run dev`

## License
Apache 2.0 (See `LICENSE` file)
