# ClaimGuard Master Project Tracker

This is the shared checklist for the Hack Day team. Check the current branch and working tree before each iteration.

## Person A — Backend, AI, and Integration

### Stage 1: Core Perception and Validation Engine

- [x] Build the FastAPI application and Gemini extraction client.
- [x] Support corporate expense and health insurance domains.
- [x] Implement deterministic math, currency, policy, and duplicate-image checks.
- [x] Add Pydantic extraction and validation schemas with a working fallback mode.
- [x] Write baseline engine tests and the Agent Skill.

### Stage 2: Storage and Workflow APIs

- [x] Persist claims and expose the claims history API.
- [x] Add manager approve/reject decisions.
- [x] Add the CSV audit export endpoint.
- [x] Standardize the upload contract on `POST /api/validate` with `perception` and `validation` response fields.

### Stage 3: Hardening and Edge Cases

- [x] Reject files over 5 MB and unsupported MIME types at the validation endpoint.
- [x] Handle transient SQLite lock errors with retry and a clear API error response.
- [x] Test health, validation, claims, decisions, CSV export, and lock retry behavior.
- [x] Clean up backend code and verify fallback behavior.

### Stage 4: Local Docker Deployment

- [x] Add a Python 3.11 backend image that serves the API on port 8000.
- [x] Load `GEMINI_API_KEY` from the local Compose environment without committing secrets.
- [x] Persist the SQLite database through the Compose data volume.
- [x] Add a backend health check for Compose startup ordering.

## Person B — Frontend, Browser Testing, and Deployment

### Stage 1: Frontend Scaffold and API-Connected UI

- [x] Build the React/Vite claim upload interface with expense and health insurance modes.
- [x] Render extracted claim details, policy checks, and validation status.
- [x] Organize the interface into reusable upload, results, history, and header components.

### Stage 2: Claims Workflow

- [x] Load and display claim history.
- [x] Add manager approve/reject actions.
- [x] Add CSV audit export.
- [x] Align the frontend request and response handling with the backend contract.

### Stage 3: Browser E2E Testing

- [x] Configure Playwright to run the frontend locally in Chromium.
- [x] Test an approved corporate expense and a flagged health insurance claim with mocked API responses.
- [x] Test CSV download and display of backend validation errors.
- [x] Run the four Playwright flows successfully.

### Stage 4: Local Docker Deployment

- [x] Add a multi-stage frontend image that builds Vite and serves the static app on port 5173.
- [x] Add Docker Compose services for the frontend and backend, including the API base URL and persistent claim data.
- [x] Add `.dockerignore` rules to exclude local secrets, dependency folders, generated assets, and databases.
- [x] Document the local launch command and `.env` setup below.

## Companion Features

- [x] Add the Benefit Calendar UI with claim-specific `.ics` downloads.
- [x] Add ScamCheck with a risk score, red flags, and IRDAI guidance.
- [x] Add insurer knowledge cards with claim gotchas and official portal links.
- [x] Add a live Cloud Gemma / Local Ollama / Offline model status badge.
- [x] Add Gemma extraction benchmarking, CLI validation, and insurer knowledge validation utilities.

## Run the Local Demo

1. Copy `.env.example` to `.env` and add `GEMINI_API_KEY` if live Gemini extraction is desired. Leave it blank to use the backend fallback.
2. Run `docker compose up --build` from the repository root.
3. Open the frontend at `http://localhost:5173`; the backend health endpoint is at `http://localhost:8000/api/health`.

The Docker configuration is prepared. The Docker engine was unavailable in the Codex environment, so the containers still need to be launched locally to verify the runtime.
