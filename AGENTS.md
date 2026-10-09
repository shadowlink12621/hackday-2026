# Hack Day Engineering Rules

## Team Ownership

- Person A owns backend and AI work: `backend/`, schemas, tests, skills, API contracts, dependency decisions, and final integration.
- Person B owns frontend work: `frontend/`, UI styling, upload flow, result display, browser testing, and demo polish.
- Shared files such as `README.md`, `CONTRACTS.md`, `TASKS.md`, and `AGENTS.md` should only change after both people understand the impact.

## Branches

- Keep `master` stable and runnable.
- Person A works on `feat/core-ai`.
- Person B works on `feat/frontend`.
- Do not force push or rewrite shared history.
- Commit in small, descriptive checkpoints.

## Contracts

- Keep the MVP API contract stable: `POST /api/validate`.
- The frontend should call `frontend/src/api.js` instead of creating a separate API path.
- Do not change request or response shapes without confirming with both people.
- Backend responses must consistently return `perception` and `validation`.

## Safety

- Never commit API keys, passwords, tokens, `.env` files, or private data.
- Keep model calls server-side.
- Preserve fallback/mock mode when `GEMINI_API_KEY` is missing or Gemma fails.
- Do not run destructive commands or overwrite unrelated files.

## Verification

- Run relevant checks before pushing.
- Person A verifies backend health and validation flow.
- Person B verifies the browser flow and responsive UI.
- Do not claim a test passed unless it was actually run.

