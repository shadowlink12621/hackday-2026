from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from .gemma_client import extract_form_data
from .engine import run_deterministic_checks
import time
from datetime import datetime, timezone
from typing import Optional

app = FastAPI(title="ClaimGuard Enterprise API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "ClaimGuard Validation Engine"}

@app.post("/api/process")
async def process_request(
    prompt: str = Form(...),
    file: Optional[UploadFile] = File(None),
    domain_mode: str = Form("expense"), # 'expense' or 'health_insurance'
    rule_settings: str = Form("{}")
):
    """
    Main endpoint for ClaimGuard (Universal Claims).
    """
    start_time = time.time()
    
    contents = await file.read() if file else b""
    mime_type = file.content_type if file else "text/plain"
    
    # Phase 1: AI Perception
    extracted_data, is_mock = extract_form_data(contents, mime_type, prompt, domain_mode)
    
    # Phase 2: Code Validation (Math, Fraud, and Domain Rules)
    validation = run_deterministic_checks(extracted_data, contents, rule_settings, domain_mode)
    
    latency_ms = int((time.time() - start_time) * 1000)
    
    return {
        "metadata": {
            "model_used": "gemini-2.5-flash",
            "is_fallback_mock": is_mock,
            "latency_ms": latency_ms,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "domain": domain_mode
        },
        "perception": {
            "structured_data": extracted_data.model_dump(),
            "confidence": extracted_data.confidence_score
        },
        "verification": validation.model_dump()
    }
