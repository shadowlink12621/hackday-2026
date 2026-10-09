import csv
from datetime import datetime, timezone
import hmac
from io import StringIO
import json
import os
from pathlib import Path
import sqlite3
import time
from typing import Any, Optional
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool


def _load_local_environment() -> None:
    """Load ignored local settings without overriding variables set by the host."""
    repo_root = Path(__file__).resolve().parent.parent
    env_path = next(
        (path for path in (repo_root / ".env", repo_root / "hackday.env") if path.is_file()),
        None,
    )
    if env_path is None:
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        key, separator, value = line.partition("=")
        key = key.strip()
        if not separator or not key or key in os.environ:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '\"'):
            value = value[1:-1]
        os.environ[key] = value


_load_local_environment()
from .engine import (
    RuleResult,
    analyze_insurance_message,
    generate_claim_calendar_ics,
    get_all_claims,
    get_claim_by_id,
    run_deterministic_checks,
    save_claim,
    update_claim_decision,
)
from .gemma_client import CloudModelError, extract_form_data, get_model_status, chat_with_claim, verify_cloud_connection
from .knowledge_loader import get_insurer_knowledge, list_known_insurers
from .policy_store import (
    MAX_POLICY_PDF_BYTES,
    get_policy,
    get_policy_pages,
    ingest_policy_pdf,
    retrieve_policy_pages,
)
from .policy.chat import answer as answer_with_policy
from .gemma_client import summarize_policy_pages
from .case_store import (
    ALLOWED_DOCUMENT_TYPES,
    DOCUMENT_CATEGORIES,
    MAX_DOCUMENT_BYTES,
    create_case,
    get_case,
    get_case_document_path,
    list_cases,
    save_case_document,
    save_case_reminder,
)

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png"}
ALLOWED_VALIDATION_TYPES = ALLOWED_IMAGE_TYPES | {"application/pdf"}
ALLOWED_DOMAINS = {"expense", "health_insurance"}

app = FastAPI(title="ClaimGuard Enterprise API")

cors_origins_env = os.environ.get("CORS_ORIGINS", "*")
origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()] if cors_origins_env != "*" else ["*"]

@app.middleware("http")
async def require_configured_api_token(request: Request, call_next):
    if request.method == "OPTIONS" or request.url.path == "/api/health":
        return await call_next(request)
    token = os.environ.get("CLAIMGUARD_API_TOKEN")
    if not token and os.environ.get("APP_ENV", "development").lower() in {"production", "prod"}:
        return JSONResponse(status_code=503, content={"detail": "Set CLAIMGUARD_API_TOKEN before running in production."})
    if token:
        supplied = request.headers.get("authorization", "")
        expected = f"Bearer {token}"
        if not hmac.compare_digest(supplied, expected):
            return JSONResponse(status_code=401, content={"detail": "Authentication required. Enter the workspace access token."})
    return await call_next(request)


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True if cors_origins_env != "*" else False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def sanitize_csv_cell(value: Any) -> str:
    """Escapes leading formula characters to prevent CSV spreadsheet injection."""
    text = str(value) if value is not None else ""
    if text and text[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + text
    return text


@app.exception_handler(sqlite3.OperationalError)
async def handle_sqlite_operational_error(request: Request, exc: sqlite3.OperationalError):
    return JSONResponse(
        status_code=503,
        content={"detail": "Database is temporarily busy or locked. Please retry shortly."},
    )


@app.get("/api/health")
def health_check():
    production = os.environ.get("APP_ENV", "development").lower() in {"production", "prod"}
    return {
        "status": "ok",
        "service": "ClaimGuard Validation Engine",
        "authentication_required": bool(os.environ.get("CLAIMGUARD_API_TOKEN")) or production,
    }


@app.get("/api/model/status")
def model_status():
    """Returns runtime AI model connectivity (Cloud Gemma vs Local Ollama vs Offline Mock)."""
    return get_model_status()


@app.post("/api/model/check")
async def check_model_connection():
    result = await run_in_threadpool(verify_cloud_connection)
    if not result["ok"]:
        raise HTTPException(status_code=503, detail=result["detail"])
    return result


@app.post("/api/validate")
async def process_request(
    prompt: Optional[str] = Form(""),
    file: Optional[UploadFile] = File(None),
    domain_mode: str = Form("expense"),
    rule_settings: str = Form("{}"),
    allow_cloud_processing: bool = Form(False),
):
    start_time = time.time()

    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="A receipt, bill, or invoice file is required.")

    mime_type = file.content_type or "application/octet-stream"
    if mime_type not in ALLOWED_VALIDATION_TYPES:
        raise HTTPException(status_code=400, detail="Upload a PDF, JPEG, or PNG document.")
    is_pdf = mime_type == "application/pdf"
    size_limit = MAX_POLICY_PDF_BYTES if is_pdf else MAX_FILE_SIZE_BYTES
    contents = await file.read(size_limit + 1)
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file cannot be empty.")
    if len(contents) > size_limit:
        raise HTTPException(status_code=400, detail=f"File size must be {size_limit // (1024 * 1024)} MB or less.")
    if is_pdf and not contents.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="The uploaded file is not a valid PDF.")

    if domain_mode not in ALLOWED_DOMAINS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid domain_mode '{domain_mode}'. Supported values: 'expense', 'health_insurance'.",
        )

    if rule_settings:
        try:
            parsed = json.loads(rule_settings)
            if not isinstance(parsed, dict):
                raise ValueError()
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Invalid rule_settings: must be a valid JSON object string.",
            )

    try:
        extracted_data, is_mock, model_source = await run_in_threadpool(
            extract_form_data, contents, mime_type, prompt or "", domain_mode,
            allow_cloud_processing,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except CloudModelError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    validation_result = run_deterministic_checks(extracted_data, contents, rule_settings, domain_mode)
    if model_source == "local_pdf_document_extractor":
        validation_result.results.append(RuleResult(
            rule_name="Manual evidence review required",
            passed=False,
            message="PDF text was parsed with deterministic heuristics. Verify every extracted amount and provider against the source before approval.",
        ))
        validation_result.is_valid = False
    if is_mock and extracted_data.confidence_score == 0:
        validation_result.results.append(RuleResult(
            rule_name="Model extraction unavailable",
            passed=False,
            message="No AI model produced evidence. Configure Cloud Gemma or local Ollama before treating this upload as analyzed.",
        ))
        validation_result.is_valid = False

    claim_id = save_claim(domain_mode, extracted_data, validation_result)
    latency_ms = int((time.time() - start_time) * 1000)

    return {
        "claim_id": claim_id,
        "metadata": {
            "model_used": model_source,
            "is_fallback_mock": is_mock,
            "latency_ms": latency_ms,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "domain": domain_mode,
        },
        "perception": {
            "structured_data": extracted_data.model_dump(),
            "confidence": extracted_data.confidence_score,
        },
        "validation": validation_result.model_dump(),
    }


@app.get("/api/claims")
def list_claims():
    """Returns all claims stored in the database."""
    return get_all_claims()


@app.get("/api/claims/{claim_id}/calendar.ics", response_class=PlainTextResponse)
def download_claim_calendar(claim_id: int):
    """Generates an RFC 5545 .ics calendar reminder for claim submission & follow-up."""
    claims = get_all_claims()
    claim = next((c for c in claims if c["id"] == claim_id), None)
    if not claim:
        raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found.")

    ics_content = generate_claim_calendar_ics(claim)
    return PlainTextResponse(
        ics_content,
        media_type="text/calendar",
        headers={"Content-Disposition": f"attachment; filename=claimguard_claim_{claim_id}.ics"},
    )


class DecisionRequest(BaseModel):
    decision: str  # "Approved" or "Rejected"


@app.post("/api/claims/{claim_id}/decision")
def record_decision(claim_id: int, payload: DecisionRequest):
    """Records a manager's final decision for a claim."""
    if payload.decision not in ["Approved", "Rejected"]:
        raise HTTPException(status_code=400, detail="Invalid decision. Use 'Approved' or 'Rejected'.")

    success = update_claim_decision(claim_id, payload.decision)
    if not success:
        raise HTTPException(status_code=404, detail=f"Claim with id {claim_id} not found.")
    return {"status": "success", "claim_id": claim_id, "decision": payload.decision}

class ChatRequest(BaseModel):
    claim_id: int
    question: str

@app.post("/api/chat")
async def chat_endpoint(payload: ChatRequest):
    """Allows user to chat with the Gemma model about a specific claim."""
    claim = get_claim_by_id(payload.claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail=f"Claim {payload.claim_id} not found.")
    
    answer = await run_in_threadpool(chat_with_claim, json.dumps(claim), payload.question)
    return {"answer": answer}


@app.post("/api/policies")
async def upload_policy(file: UploadFile = File(...)):
    """Extract and index a policy PDF locally without retaining the original file."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Upload a PDF policy document.")
    contents = await file.read(MAX_POLICY_PDF_BYTES + 1)
    if len(contents) > MAX_POLICY_PDF_BYTES:
        raise HTTPException(status_code=413, detail="Policy PDF must be 20 MB or smaller.")
    try:
        # Legacy endpoint remains local-only; image OCR requires explicit consent.
        return ingest_policy_pdf(contents, file.filename, allow_cloud_processing=False)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/policies/{policy_id}")
def read_policy(policy_id: int):
    policy = get_policy(policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found.")
    return policy


class PolicyQuestion(BaseModel):
    question: str
    allow_cloud_processing: bool = False
    history: list[dict[str, str]] = Field(default_factory=list, max_length=8)


class PolicySummaryRequest(BaseModel):
    allow_cloud_processing: bool = False


class ReminderRequest(BaseModel):
    confirmed_date: Optional[str] = None


@app.post("/api/cases/{case_id}/reminder")
def save_reminder(case_id: int, payload: ReminderRequest):
    if payload.confirmed_date:
        try:
            datetime.strptime(payload.confirmed_date, "%Y-%m-%d")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Reminder date must use YYYY-MM-DD format.") from exc
    if not save_case_reminder(case_id, payload.confirmed_date):
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found.")
    return {"case_id": case_id, "confirmed_date": payload.confirmed_date}


@app.post("/api/policies/{policy_id}/chat")
async def ask_policy(policy_id: int, payload: PolicyQuestion):
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question is required.")
    policy = get_policy(policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found.")
    history = [
        {"role": turn["role"], "text": turn["text"][:1200]}
        for turn in payload.history[-8:]
        if turn.get("role") in {"user", "assistant"} and turn.get("text", "").strip()
    ]
    context_query = " ".join(
        [turn["text"] for turn in history if turn["role"] == "user"] + [payload.question]
    )
    evidence = retrieve_policy_pages(policy_id, context_query)
    result = await run_in_threadpool(
        answer_with_policy, payload.question, evidence, payload.allow_cloud_processing, history
    )
    return {"policy": policy, **result}


@app.post("/api/policies/{policy_id}/summary")
async def summarize_policy(policy_id: int, payload: PolicySummaryRequest):
    """Generate a whole-policy outline only after explicit cloud consent."""
    if not get_policy(policy_id):
        raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found.")
    pages = get_policy_pages(policy_id)
    result = await run_in_threadpool(
        summarize_policy_pages, pages, payload.allow_cloud_processing
    )
    summary = result.get("summary")
    cited_pages = set()
    if summary:
        for key, value in summary.items():
            if isinstance(value, list):
                for fact in value:
                    cited_pages.update(fact.get("pages", []))
            elif isinstance(value, dict):
                cited_pages.update(value.get("pages", []))
    sources = [page for page in pages if page["page"] in cited_pages]
    return {**result, "sources": sources}


class CaseCreateRequest(BaseModel):
    patient_name: str = Field(min_length=1, max_length=120)
    age: int | None = Field(default=None, ge=0, le=120)
    weight_kg: float | None = Field(default=None, gt=0, le=500)
    blood_group: str | None = Field(default=None, max_length=8)
    medical_conditions: list[str] = Field(default_factory=list, max_length=40)
    additional_details: dict[str, str] = Field(default_factory=dict)


@app.post("/api/cases", status_code=201)
def create_case_endpoint(payload: CaseCreateRequest):
    """Create a local patient case; optional health details are user-provided, never inferred."""
    details = payload.model_dump(exclude={"patient_name"})
    case_id = create_case(payload.patient_name, details)
    return get_case(case_id)


@app.get("/api/cases")
def list_cases_endpoint():
    return list_cases()


@app.get("/api/cases/{case_id}")
def read_case_endpoint(case_id: int):
    result = get_case(case_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found.")
    return result


@app.post("/api/cases/{case_id}/documents", status_code=201)
async def upload_case_document(
    case_id: int,
    file: UploadFile = File(...),
    category: str = Form("other"),
    allow_cloud_processing: bool = Form(False),
):
    """Store a case file locally and index policy PDFs for citation-backed questions."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="A document filename is required.")
    if category not in DOCUMENT_CATEGORIES:
        raise HTTPException(status_code=400, detail="Unsupported document category.")
    if not get_case(case_id):
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found.")
    content_type = file.content_type or "application/octet-stream"
    if content_type not in ALLOWED_DOCUMENT_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF, JPEG, and PNG files are supported.")
    contents = await file.read(MAX_DOCUMENT_BYTES + 1)
    if len(contents) > MAX_DOCUMENT_BYTES:
        raise HTTPException(status_code=413, detail="Documents must be 20 MB or smaller.")

    policy_id = None
    policy_index = None
    if category == "policy":
        if content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Policy documents must be PDF files.")
        try:
            policy_index = ingest_policy_pdf(contents, file.filename, allow_cloud_processing)
            policy_id = policy_index["policy_id"]
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
    try:
        saved = save_case_document(case_id, category, file.filename, content_type, contents, policy_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if not saved:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found.")
    return {
        **saved,
        "policy": get_policy(policy_id) if policy_id else None,
        "indexing": policy_index,
        "storage": "local",
    }


@app.get("/api/cases/{case_id}/documents/{document_id}/download")
def download_case_document(case_id: int, document_id: int):
    result = get_case_document_path(case_id, document_id)
    if not result:
        raise HTTPException(status_code=404, detail="Document not found.")
    path, filename = result
    return FileResponse(path, filename=filename)

class ScamCheckRequest(BaseModel):
    message_text: str


@app.post("/api/scamcheck")
def check_scam_message(payload: ScamCheckRequest):
    """
    Checks an SMS, email, or WhatsApp message for insurance fraud and fee-to-release scams.
    Cross-references IRDAI Bima Bharosa warnings.
    """
    if not payload.message_text or not payload.message_text.strip():
        raise HTTPException(status_code=400, detail="Message text is required.")
    return analyze_insurance_message(payload.message_text)


@app.get("/api/insurers")
def list_insurers():
    """Returns list of supported insurers with local knowledge base entries."""
    return {"insurers": list_known_insurers()}


@app.get("/api/insurers/{insurer_key}")
def get_insurer_details(insurer_key: str):
    """Returns policy gotchas, sub-limits, and rejection traps for an insurer."""
    data = get_insurer_knowledge(insurer_key)
    if not data:
        raise HTTPException(status_code=404, detail=f"No knowledge found for insurer '{insurer_key}'.")
    return data


@app.get("/api/export.csv", response_class=PlainTextResponse)
def export_claims_csv():
    """Generates a CSV export of all claims for auditing."""
    claims = get_all_claims()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Timestamp", "Domain", "Total_INR", "System_Valid", "Manager_Status", "Vendor/Hospital"])

    for c in claims:
        vendor = sanitize_csv_cell(c["extracted_data"].get("provider_name", ""))
        domain = sanitize_csv_cell(c.get("domain", ""))
        status = sanitize_csv_cell(c.get("status", ""))
        writer.writerow([
            c["id"],
            c["timestamp"],
            domain,
            c["total_inr"],
            c["is_valid"],
            status,
            vendor,
        ])

    response = output.getvalue()
    return PlainTextResponse(
        response,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=claimguard_audit.csv"},
    )
