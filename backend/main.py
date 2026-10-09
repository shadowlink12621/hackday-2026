import csv
from datetime import datetime, timezone
from io import StringIO
import json
import os
import sqlite3
import time
from typing import Any, Optional
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool
from .engine import get_all_claims, run_deterministic_checks, save_claim, update_claim_decision
from .gemma_client import extract_form_data

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png"}
ALLOWED_DOMAINS = {"expense", "health_insurance"}

app = FastAPI(title="ClaimGuard Enterprise API")

cors_origins_env = os.environ.get("CORS_ORIGINS", "*")
origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()] if cors_origins_env != "*" else ["*"]

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
    return {"status": "ok", "service": "ClaimGuard Validation Engine"}


@app.post("/api/validate")
async def process_request(
    prompt: Optional[str] = Form(""),
    file: Optional[UploadFile] = File(None),
    domain_mode: str = Form("expense"),
    rule_settings: str = Form("{}"),
):
    start_time = time.time()

    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="An image file is required for document validation.")

    contents = await file.read()
    if not contents or len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file cannot be empty.")

    mime_type = file.content_type or "application/octet-stream"
    if mime_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG and PNG images are supported.")
    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File size must be 5 MB or less.")

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

    extracted_data, is_mock = await run_in_threadpool(
        extract_form_data, contents, mime_type, prompt or "", domain_mode
    )
    validation_result = run_deterministic_checks(extracted_data, contents, rule_settings, domain_mode)

    claim_id = save_claim(domain_mode, extracted_data, validation_result)
    latency_ms = int((time.time() - start_time) * 1000)

    return {
        "claim_id": claim_id,
        "metadata": {
            "model_used": os.environ.get("GEMMA_MODEL", "gemma-4-26b-a4b-it"),
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
