# Hack Day Master Plan: ClaimGuard (Universal Claims validator)
**Track:** Best Open-Source AI Project & Best Use of Gemma 4

## The Architecture
ClaimGuard now supports **Corporate Expenses** AND **Health Insurance Claims (e.g., Indian Medical Bills)**!
1. **Frontend (Person B)**: User selects "Domain" (Expense or Health Insurance) and uploads an image.
2. **Perception (Gemma 4)**: Extracts Vendor/Hospital, Date, Currency, Line Items (auto-categorized as 'meals', 'room_rent', 'consumables', etc.), and Total.
3. **Logic (Python)**:
   - **Fraud Check**: SHA-256 SQLite lookup for duplicate images.
   - **Expense Math**: Converts USD/EUR to INR, checks ₹4000 limit.
   - **Health Math**: Checks if Room Rent > ₹10,000 and denies non-medical consumables.
4. **Dashboard**: Person B displays the results and an Export to CSV button.

---

## 👨‍💻 PERSON A DIVISION (Backend - Python/FastAPI)
### Part A1: Antigravity AI (Heavy Lifting)
* **Universal Gemma Integration**: Rewrote `gemma_client.py` to accept `domain_mode` and dynamically alter the AI prompt/extraction.
* **Complex Python Engine**: Expanded `engine.py` to handle specialized Indian Health Insurance rules (room rent caps, consumables exclusion) alongside standard corporate expense math.
* **Testing**: Implemented a full `pytest` suite in `backend/tests/` to guarantee open-source track points.

### Part A2: Human (Vansh)
* **Execution**: Ensure `.env` is loaded. Run tests and keep Uvicorn running (`python -m uvicorn backend.main:app --reload`).
* **Git**: Commit and push changes to `master` so Person B can pull.

---

## 👨‍💻 PERSON B DIVISION (Frontend - Next.js/React & Deployment)
**@Teammate: Copy the block below and paste it directly into Codex / your AI assistant to generate your code!**

```text
PROMPT FOR CODEX / FRONTEND AI:

You are building the frontend for a Universal AI Claims Validator called "ClaimGuard". 
We are using React/Vite (or Next.js).

Context: 
The backend (FastAPI) is live at `POST http://localhost:8000/api/validate`.
It expects `FormData` with:
- `file` (image)
- `domain_mode` (string: either "expense" or "health_insurance")
- `prompt` (string: optional, can be empty)

It returns this exact JSON schema:
{
  "metadata": { "model_used": "gemma-4-26b-a4b-it", "domain": "health_insurance" },
  "perception": {
    "structured_data": {
      "provider_name": "Apollo Hospitals", "patient_or_employee_name": "Rahul Sharma",
      "currency": "INR",
      "items": [ {"description": "ICU", "amount": 20000, "category": "room_rent"} ],
      "total_extracted": 20000, "confidence_score": 0.95
    }
  },
  "validation": {
    "is_valid": false, "final_amount_inr": 20000,
    "results": [
      { "rule_name": "Fraud Detection", "passed": true, "message": "Hash unique." },
      { "rule_name": "Room Rent Cap", "passed": false, "message": "Exceeds standard cap." }
    ]
  }
}

Your Tasks (Codex):
1. Build a drag-and-drop upload zone, AND add a dropdown selector for the user to choose "Corporate Expense" or "Health Insurance".
2. Build an `api.js` file that sends the image, domain mode, and prompt to `/api/validate`.
3. Build the Results Dashboard: A clean HTML table mapping over `response.perception.structured_data.items`.
4. UI Badges: If `response.validation.is_valid` is true, render a GREEN "APPROVED" badge. If false, render a RED "FLAGGED/MANUAL REVIEW" badge. Show the exact failure rules.
5. Export Feature: Add an "Export to CSV" button that converts `structured_data.items` to a CSV file.
```

### Part B2: Human (Teammate)
* **Git Workflow**: Run `git pull origin master`.
* **Environment**: Run `npm install` and `npm run dev` in the frontend directory.
* **DigitalOcean Deployment**: Connect the GitHub repo to DigitalOcean App Platform as a static Vite site and Python web service. Set `VITE_API_BASE_URL` to the live backend URL.
