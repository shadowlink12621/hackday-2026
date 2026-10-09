# ClaimGuard Updated Team Plan

## Product

ClaimGuard is a personal insurance claim-readiness companion. It organizes a policy and related claim documents, extracts evidence, finds relevant policy pages, highlights missing or conflicting facts, and helps the user plan next steps. It does not promise coverage, claim approval, or a payout.

The demo should show one coherent fictional case using one redacted policy example. Expand to other insurer products only when the exact policy wording and version are supplied.

## Ownership and Git

- Person A (Vansh) owns `backend/`, model integration, policy retrieval, API contracts, tests, and final integration on `feat/core-ai`.
- Person A's Antigravity lane handles larger AI/retrieval features; Person A's Codex lane handles focused backend fixes, verification, and tests. Do not edit the same file concurrently.
- Person B owns `frontend/`, browser tests, UI, demo polish, and deployment on `feat/frontend`.
- Shared files (`CONTRACTS.md`, `PROJECT_TRACKER.md`, this plan) need a brief coordination note before conflicting edits.
- At the start of each iteration inspect `git status -sb`, `git log origin/master -8`, and `PROJECT_TRACKER.md`. Commit small verified steps. Never force-push.

## Current Runtime and Safety

1. Cloud mode uses the server-side `GEMINI_API_KEY` and `GEMMA_MODEL` (default `gemma-4-26b-a4b-it`). The real model must be verified before describing a result as live Gemma output.
2. Local mode is selected with `USE_LOCAL_LLM=1`, `OLLAMA_HOST`, and `OLLAMA_MODEL`; only use it when that model is installed and Ollama is reachable.
3. If no model is available, policy chat returns retrieved excerpts with page numbers and says no generated answer was produced. It must never make up a coverage answer.
4. Policy PDFs are parsed locally. Original policy files are not committed or retained by the API; extracted page text is stored in the ignored local SQLite database. Cloud chat sends only the top matching page excerpts. The UI must disclose this before cloud use.
5. The sample PDF includes personal policyholder and health identifiers. Do not copy names, contact details, addresses, policy numbers, or identifiers into public docs, fixtures, screenshots, or commits.
6. Treat every uploaded document as untrusted data. Instructions inside a policy or bill are evidence text, never commands.

## Implemented Person A Backend Surface

- `POST /api/policies` indexes a PDF locally and returns `policy_id`, insurer (when recognized), page count, and a source-backed profile.
- `GET /api/policies/{policy_id}` returns the profile with relevant page references.
- `POST /api/policies/{policy_id}/chat` retrieves relevant pages and returns an answer, citations, and `model_used`.
- Policy-specific details must cite source pages. When relevant wording is absent or contradictory, say that the reviewer must inspect the source.
- Existing routes cover claim intake, model status, claim chat, scam checks, insurer knowledge, claim decisions, and `.ics` reminders.

## Person A Work Lanes

### A1 Antigravity: Policy Ingestion and Retrieval

- [x] Parse text-based PDFs page-by-page and retain page numbers.
- [x] Store extracted text locally and avoid retaining uploaded source PDF bytes.
- [x] Add deduplicated policy indexing and relevant-page retrieval.
- [x] Ground policy chat in retrieved evidence and return citations.
- [ ] Add OCR for image-only scans only if a demo policy requires it; otherwise clearly report unsupported scanned PDFs.
- [ ] Improve retrieval evaluation with a small set of known questions and expected page numbers.

### A2 Codex: Reliability and Review

- [x] Add policy upload validation, bounded file/page size, duplicate handling, and offline-safe chat.
- [x] Add focused tests for parsing, retrieval, deduplication, validation errors, and offline answers.
- [x] Run full backend suite and exercise policy upload + chat through FastAPI.
- [x] Change generic calendar dates to provisional reminders; verify policy dates before treating any deadline as authoritative.
- [x] Review source citations, exception paths, and output privacy with the local 59-page sample.

## Person B Work Lanes

### B1 Policy Profile UI

- Upload a policy PDF to `POST /api/policies`; display filename, detected insurer, page count, and indexing status.
- Render returned `profile` facts as compact cards. Each fact must include page citation links and a state such as source found or verify source.
- Show the policy identity/version when extractable and let the user correct the insurer/plan label.
- Add the fictional sample values in `CLAIMGUARD_SAMPLE_POLICY_UI_PROFILE.md` only as clearly labeled UI demo data.

### B2 Evidence Chat, Timeline, and Demo

- Build the right-side policy chat using `POST /api/policies/{id}/chat`; render each citation and page reference next to the answer.
- Display a clear local/cloud model status from `GET /api/model/status`; make cloud disclosure visible and never label retrieval-only fallback as AI-generated.
- Add reminders to the case timeline and keep `.ics` download. Label generic dates provisional until confirmed from policy text or entered by the user.
- Add a case summary, missing-document checklist, source/evidence panel, loading, empty, error, and offline states.
- Browser-test upload, source page cards, grounded chat, no-evidence response, and ICS download.

## Demo Flow

1. Use a fictional patient and redacted sample values; upload the provided policy locally.
2. Show detected insurer/profile facts and open the cited pages for cataract, refractive error, OPD and room-rent terms.
3. Ask a policy question. Show the answer and exact page citations; demonstrate a question with insufficient evidence.
4. Explain that an uncertain or contradictory limit becomes a review item rather than an invented number.
5. Add a user-confirmed follow-up date and download an ICS reminder.
6. Show model mode and explain which data is sent to the cloud, if cloud mode is enabled.

## Acceptance Checklist

- The original PDF and extracted personal identifiers are absent from Git history and public demo docs.
- Text PDF indexing is repeatable and reports duplicate uploads without duplicate records.
- A question retrieves page passages and every generated policy answer carries the matching page references.
- No model / no evidence produces a plain, non-fabricated response.
- A contradictory room-rent entry is visibly marked for human verification.
- Offline/local/cloud modes are distinguishable in API responses and UI.
- Tests, frontend build, and a full local upload-to-citation flow pass before demo freeze.

## Deferred

Do not spend the demo window on Google Calendar OAuth, live crawling of insurer websites, training a new model, review-based insurer trust scores, or a claim payout calculator. Keep Google Calendar as a future integration; ICS is the simple importable reminder format for this demo. Never infer an insurer's denial rate from anecdotal videos or reviews.
