# ClaimGuard Case Workflow Handoff

This is a local-first demo, not an insurer decision system. Keep the user's case documents and profile attached to one selected case. Do not prefill a patient, policy, claim, date, result, citation, or scam message with sample values.

## Workflow

1. Create a case with the patient's name. Age, weight, blood group, and medical conditions are optional user-entered fields; explain why a field is needed before making it required. Ask lifestyle/disclosure questions only when the uploaded policy or user-selected workflow makes them relevant. Never infer a diagnosis from a blood report.
2. Require the case to be saved before enabling document upload. A separate case must have separate documents and policy links.
3. Upload the policy schedule/full wording as `category=policy`. Upload lab reports as `lab_report`; discharge summaries, bills, prescriptions, and other records have their own categories. A blood report is optional. A discharge summary is useful for a hospitalization claim but is not needed to understand policy wording.
4. Render the returned policy profile only after upload. Each card uses the returned `topic`, `pages`, `evidence`, and `status`; show no card as a confirmed benefit unless the cited wording supports it. Missing evidence should say “Not found in indexed text.” `conflict_review` means a human must inspect the source.
5. Ask policy questions through `/api/policies/{policy_id}/chat`. Display the returned `model_used`, answer, and citations. If the API reports `retrieval_only`, render the source passages and say no generated answer was made. Do not use canned responses when the backend is unavailable.
6. Use user-confirmed policy dates or deadlines. Do not label a generic date a statutory filing limit. Offer an `.ics` download only after the user confirms the date and case.

## API Surface

- `POST /api/cases`: JSON `{ "patient_name": "...", "age": 42, "weight_kg": 70, "blood_group": "O+", "medical_conditions": [] }`; optional fields may be omitted.
- `GET /api/cases`: list separate local cases.
- `GET /api/cases/{case_id}`: get profile and linked document metadata.
- `POST /api/cases/{case_id}/documents`: multipart `file` and `category` (`policy`, `lab_report`, `discharge_summary`, `bill`, `prescription`, `other`). Supports PDF, JPEG, PNG, max 20 MB. Files are saved under ignored local `data/cases/`; policy PDFs are also indexed for page citations.
- `GET /api/cases/{case_id}/documents/{document_id}/download`: retrieve a file for that case.
- Existing `GET /api/policies/{policy_id}`: upload-derived policy profile; `POST /api/policies/{policy_id}/chat`: evidence-backed question answering.
- Existing `GET /api/model/status`: show the configured cloud/local/offline state. Never label output as Gemma unless the response says a configured model generated it.

## Backend / Demo Limits

- The uploaded policy controls policy-specific facts. The insurer markdown files in `backend/knowledge/` are broad reference notes and must not be displayed as terms of the user's contract.
- Policy PDF text extraction works for text PDFs; scanned PDFs need OCR, which is not currently implemented. JPEG/PNG documents are saved locally but are not yet summarized as a medical record.
- The policy profile surfaces retrieved source snippets; it does not yet provide a verified, exhaustive extraction of every schedule field or every covered hospital in India.
- Cloud inference needs `GEMINI_API_KEY` in the local ignored `.env`. Policy and health documents contain sensitive data: get explicit user consent before sending any content to a cloud provider. Never put the key in chat, source files, browser code, or Git.
- Without a reachable model, show empty extraction with confidence `0` or retrieved source text. Never substitute invented sample patient/bill content.
