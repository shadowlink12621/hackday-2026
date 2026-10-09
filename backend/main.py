import csv
from datetime import datetime, timezone
from io import StringIO
import os
import sqlite3
import time
from typing import Optional
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel
from .engine import get_all_claims, run_deterministic_checks, save_claim, update_claim_decision
from .gemma_client import extract_form_data

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png"}

app = FastAPI(title="ClaimGuard Enterprise API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    rule_settings: str = Form("{}")
):
    start_time = time.time()
    
    contents = await file.read() if file else b""
    mime_type = file.content_type if file else "text/plain"

    if file:
        if mime_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(status_code=400, detail="Only JPEG and PNG images are supported.")
        if len(contents) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(status_code=400, detail="File size must be 5 MB or less.")
    
    extracted_data, is_mock = extract_form_data(contents, mime_type, prompt, domain_mode)
    validation_result = run_deterministic_checks(extracted_data, contents, rule_settings, domain_mode)
    
    # NEW: Save the claim to SQLite and get an ID
    claim_id = save_claim(domain_mode, extracted_data, validation_result)
    
    latency_ms = int((time.time() - start_time) * 1000)
    
    return {
        "claim_id": claim_id,
        "metadata": {
            "model_used": os.environ.get("GEMMA_MODEL", "gemma-4-26b-a4b-it"),
            "is_fallback_mock": is_mock,
            "latency_ms": latency_ms,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "domain": domain_mode
        },
        "perception": {
            "structured_data": extracted_data.model_dump(),
            "confidence": extracted_data.confidence_score
        },
        "validation": validation_result.model_dump()
    }

@app.get("/api/claims")
def list_claims():
    """Returns all claims stored in the database."""
    return get_all_claims()

class DecisionRequest(BaseModel):
    decision: str # "Approved" or "Rejected"

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
        vendor = c["extracted_data"].get("provider_name", "")
        writer.writerow([
            c["id"], c["timestamp"], c["domain"], c["total_inr"], 
            c["is_valid"], c["status"], vendor
        ])
        
    response = output.getvalue()
    return PlainTextResponse(response, media_type="text/csv", headers={
        "Content-Disposition": "attachment; filename=claimguard_audit.csv"
    })
