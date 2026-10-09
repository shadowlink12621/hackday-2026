# Hack Day Master Plan: ClaimGuard (BillBuddy)
**Track:** Best Open-Source AI Project & Best Use of Gemma 4

## The Architecture (How it works)
We are building a "Real-World Enterprise AI Agent" for processing and validating expense receipts.
1. **Frontend (Person B)** sends a crumpled receipt image (`.jpg`/`.png`) to the backend.
2. **Perception (Gemma 4)** reads the image and extracts the Vendor, Date, Currency, Line Items, and Total into strict JSON.
3. **Logic (Python Deterministic Engine)** checks a local SQLite DB for duplicate images (Fraud Check), validates the math, converts the currency to INR, and ensures it's under the company limit (₹4000).
4. **Frontend (Person B)** displays a beautiful dashboard with the results, BADGES (Green/Red), and a CSV Export button.

---

## 👨‍💻 PERSON A DIVISION (Backend - Python/FastAPI)
*The backend is already scaffolded and pushed to `master`.*

### Part 1: Antigravity AI (Heavy Lifting & Expert Logic)
* **LLM Orchestration**: Wrote `gemma_client.py` using `google-genai` SDK with strict JSON schema parsing and fallback mock mode.
* **Deterministic Engine**: Built `engine.py` with `sqlite3` for SHA-256 image hashing (Fraud Detection) and mathematical policy limits.
* **API Contracts**: Designed the `POST /api/process` endpoint in FastAPI.

### Part 2: Human (Vansh)
* **Environment Control**: Manage the `GEMINI_API_KEY` in `.env`.
* **Testing & Servers**: Run `python -m uvicorn backend.main:app --reload`.
* **Git Orchestration**: Merge Antigravity's heavy logic to `master` and ensure Person B gets the updates.

---

## 👨‍💻 PERSON B DIVISION (Frontend - Next.js/React & Deployment)
**@Teammate: Copy the block below and paste it directly into Codex / your AI assistant to generate your code!**

```text
PROMPT FOR CODEX / FRONTEND AI:

You are building the frontend for an Enterprise AI Agent called "ClaimGuard". 
We are using React/Vite (or Next.js) with Tailwind or Vanilla CSS glassmorphism.

Context: 
The backend (FastAPI) is already built. It exposes an endpoint: `POST http://localhost:8000/api/process`.
It expects `FormData` with a `file` (image).
It returns this exact JSON schema:
{
  "metadata": { "model_used": "gemini-2.5-flash", "is_fallback_mock": false },
  "perception": {
    "structured_data": {
      "vendor_name": "Starbucks", "date_extracted": "2026-10-09", "currency": "USD",
      "items": [ {"description": "Coffee", "amount": 5.0} ],
      "total_extracted": 5.0, "confidence_score": 0.95
    }
  },
  "verification": {
    "is_valid": true, "final_amount_inr": 417.5,
    "results": [
      { "rule_name": "Fraud Detection", "passed": true, "message": "Receipt hash is unique." },
      { "rule_name": "Math Verification", "passed": true, "message": "Line items sum perfectly to 5.0." }
    ]
  }
}

Your Tasks (Codex):
1. Create a modern drag-and-drop file upload zone.
2. Build an `api.js` file that sends the image to `http://localhost:8000/api/process`.
3. Build the Results Dashboard: Create a clean HTML table that maps over `response.perception.structured_data.items` and displays the receipt line items.
4. UI Badges: Look at `response.verification.is_valid`. If true, render a massive, glowing GREEN "APPROVED" badge. If false, render a RED "FLAGGED" badge.
5. Export Feature: Write a JavaScript function that takes the `structured_data.items`, converts it to CSV format, and triggers a browser file download when the user clicks "Export to CSV". Make the UI look like a premium SaaS dashboard.
```

### Part 2: Human (Teammate)
* **Git Workflow**: Run `git pull origin master` to grab the latest backend files, then switch to `feat/frontend`.
* **Environment**: Run `npm install` and `npm run dev` in the frontend directory.
* **DigitalOcean Deployment**: At 2:30 PM, take the GitHub repo, connect it to DigitalOcean App Platform, configure the build settings (Node for frontend, Python for backend, or just static site for frontend), and secure the live `https://` URL for the judges.
