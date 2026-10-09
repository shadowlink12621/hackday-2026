import sqlite3
import pytest
from fastapi.testclient import TestClient

from backend import engine
from backend.engine import (
    RuleResult,
    ValidationResult,
    get_all_claims,
    run_deterministic_checks,
    save_claim,
    update_claim_decision,
    with_db_retry,
)
from backend.gemma_client import ClaimExtraction, LineItem
from backend.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolate_test_db(tmp_path, monkeypatch):
    test_db = str(tmp_path / "test_claimguard.db")
    monkeypatch.setenv("CLAIMGUARD_DB_FILE", test_db)
    monkeypatch.setattr(engine, "DB_FILE", test_db)
    engine.init_db()



def test_valid_expense():
    mock_data = ClaimExtraction(
        provider_name="Test Vendor",
        patient_or_employee_name="John Doe",
        date_extracted="2026-10-09",
        currency="INR",
        items=[LineItem(description="Lunch", amount=500.0)],
        total_extracted=500.0,
        confidence_score=0.9,
    )
    result = run_deterministic_checks(mock_data, b"fake_image_bytes_1", "{}", "expense")
    assert result.is_valid is True
    assert result.final_amount_inr == 500.0


def test_over_limit_expense():
    mock_data = ClaimExtraction(
        provider_name="Test Vendor",
        patient_or_employee_name="John Doe",
        date_extracted="2026-10-09",
        currency="USD",
        items=[LineItem(description="Expensive Dinner", amount=100.0)],
        total_extracted=100.0,
        confidence_score=0.9,
    )
    # USD 100 * 83.5 = 8350 INR (over the default 4000 limit)
    result = run_deterministic_checks(mock_data, b"fake_image_bytes_2", "{}", "expense")
    assert result.is_valid is False
    assert any("EXCEEDS policy limit" in r.message for r in result.results)


def test_duplicate_fraud():
    mock_data = ClaimExtraction(
        provider_name="Test Vendor",
        patient_or_employee_name="John",
        date_extracted="2026-10-09",
        currency="INR",
        items=[LineItem(description="Lunch", amount=500.0)],
        total_extracted=500.0,
        confidence_score=0.9,
    )
    result1 = run_deterministic_checks(mock_data, b"duplicate_bytes", "{}", "expense")
    result2 = run_deterministic_checks(mock_data, b"duplicate_bytes", "{}", "expense")

    assert any("unique" in r.message for r in result1.results if "Duplicate" in r.rule_name)
    assert result2.is_valid is False
    assert any("DUPLICATE DETECTED" in r.message for r in result2.results if "Duplicate" in r.rule_name)


def test_health_insurance_consumables():
    mock_data = ClaimExtraction(
        provider_name="Test Hospital",
        patient_or_employee_name="Jane Doe",
        date_extracted="2026-10-09",
        currency="INR",
        items=[
            LineItem(description="Room Rent", amount=2000.0, category="room_rent"),
            LineItem(description="Gloves", amount=500.0, category="consumables"),
        ],
        total_extracted=2500.0,
        confidence_score=0.9,
    )
    result = run_deterministic_checks(mock_data, b"fake_image_bytes_4", "{}", "health_insurance")
    assert result.is_valid is False
    assert any("Consumables" in r.rule_name for r in result.results)



def test_save_and_retrieve_claims():
    mock_data = ClaimExtraction(
        provider_name="Starbucks Audit",
        patient_or_employee_name="Alice",
        date_extracted="2026-10-09",
        currency="INR",
        items=[LineItem(description="Coffee", amount=250.0, category="meals")],
        total_extracted=2500.0,
        confidence_score=0.95,
    )
    val_result = ValidationResult(
        is_valid=True,
        final_amount_inr=250.0,
        results=[RuleResult(rule_name="Policy Limit", passed=True, message="OK")],
    )

    claim_id = save_claim("expense", mock_data, val_result)
    assert isinstance(claim_id, int)
    assert claim_id > 0

    all_claims = get_all_claims()
    assert len(all_claims) > 0
    saved = next((c for c in all_claims if c["id"] == claim_id), None)
    assert saved is not None
    assert saved["domain"] == "expense"
    assert saved["total_inr"] == 250.0
    assert saved["status"] == "Pending"
    assert saved["validation_data"]["is_valid"] is True
    assert saved["extracted_data"]["provider_name"] == "Starbucks Audit"


def test_update_claim_decision():
    mock_data = ClaimExtraction(
        provider_name="Apollo Clinic",
        patient_or_employee_name="Bob",
        date_extracted="2026-10-09",
        currency="INR",
        items=[LineItem(description="Consultation", amount=1200.0, category="doctor_fee")],
        total_extracted=1200.0,
        confidence_score=0.98,
    )
    val_result = ValidationResult(
        is_valid=True,
        final_amount_inr=1200.0,
        results=[],
    )
    claim_id = save_claim("health_insurance", mock_data, val_result)

    # Approve claim
    success = update_claim_decision(claim_id, "Approved")
    assert success is True

    claims = get_all_claims()
    matched = next((c for c in claims if c["id"] == claim_id), None)
    assert matched is not None
    assert matched["status"] == "Approved"

    # Reject non-existent claim
    fail = update_claim_decision(9999999, "Approved")
    assert fail is False


def test_api_claims_and_decision_endpoints():
    # Test GET /api/claims
    res = client.get("/api/claims")
    assert res.status_code == 200
    claims = res.json()
    assert isinstance(claims, list)

    # Save a claim and test decision endpoint
    mock_data = ClaimExtraction(
        provider_name="Test Decision Vendor",
        patient_or_employee_name="Carol",
        date_extracted="2026-10-09",
        currency="INR",
        items=[LineItem(description="Taxi", amount=300.0, category="transport")],
        total_extracted=300.0,
        confidence_score=0.9,
    )
    val_result = ValidationResult(is_valid=True, final_amount_inr=300.0, results=[])
    claim_id = save_claim("expense", mock_data, val_result)

    # Test valid approval
    resp_approve = client.post(f"/api/claims/{claim_id}/decision", json={"decision": "Approved"})
    assert resp_approve.status_code == 200
    assert resp_approve.json()["decision"] == "Approved"

    # Test valid rejection
    resp_reject = client.post(f"/api/claims/{claim_id}/decision", json={"decision": "Rejected"})
    assert resp_reject.status_code == 200
    assert resp_reject.json()["decision"] == "Rejected"

    # Test invalid decision value
    resp_invalid = client.post(f"/api/claims/{claim_id}/decision", json={"decision": "PendingReview"})
    assert resp_invalid.status_code == 400

    # Test 404 for missing claim
    resp_missing = client.post("/api/claims/9999999/decision", json={"decision": "Approved"})
    assert resp_missing.status_code == 404


def test_api_export_csv():
    res = client.get("/api/export.csv")
    assert res.status_code == 200
    assert "text/csv" in res.headers.get("content-type", "")
    content = res.text
    assert "ID,Timestamp,Domain,Total_INR,System_Valid,Manager_Status,Vendor/Hospital" in content


def test_api_file_upload_validation_limits():
    # Oversized file (> 5MB)
    large_payload = b"A" * (5 * 1024 * 1024 + 1024)
    res_large = client.post(
        "/api/validate",
        files={"file": ("large.png", large_payload, "image/png")},
        data={"domain_mode": "expense"},
    )
    assert res_large.status_code == 400
    detail = res_large.json().get("detail", "")
    assert "5 MB" in detail or "parsing the body" in detail.lower()

    # Unsupported MIME type
    res_mime = client.post(
        "/api/validate",
        files={"file": ("doc.txt", b"plain text...", "text/plain")},
        data={"domain_mode": "expense"},
    )
    assert res_mime.status_code == 400
    assert "Only JPEG, PNG, and searchable PDF files are supported" in res_mime.json()["detail"]


def test_unsupported_currency_flagged():
    mock_data = ClaimExtraction(
        provider_name="Tokyo Shop",
        patient_or_employee_name="Kenji",
        date_extracted="2026-10-09",
        currency="XYZ",
        items=[LineItem(description="Item", amount=100.0)],
        total_extracted=100.0,
        confidence_score=0.9,
    )
    result = run_deterministic_checks(mock_data, b"test_unsupported_curr", "{}", "expense")
    assert result.is_valid is False
    assert any(
        r.rule_name == "Currency Verification" and r.passed is False
        for r in result.results
    )


def test_api_validate_missing_file_and_invalid_domain():
    # Missing file
    res_no_file = client.post("/api/validate", data={"domain_mode": "expense"})
    assert res_no_file.status_code == 400
    assert "required" in res_no_file.json()["detail"].lower()

    # Invalid domain mode
    dummy_img = (b"fake_valid_png_header", "receipt.png", "image/png")
    res_bad_domain = client.post(
        "/api/validate",
        files={"file": ("receipt.png", b"valid_bytes_test", "image/png")},
        data={"domain_mode": "invalid_domain"},
    )
    assert res_bad_domain.status_code == 400
    assert "domain_mode" in res_bad_domain.json()["detail"].lower()

    # Invalid rule settings JSON
    res_bad_settings = client.post(
        "/api/validate",
        files={"file": ("receipt.png", b"valid_bytes_test", "image/png")},
        data={"domain_mode": "expense", "rule_settings": "{bad_json}"},
    )
    assert res_bad_settings.status_code == 400
    assert "rule_settings" in res_bad_settings.json()["detail"].lower()


def test_csv_export_sanitizes_formula_injection():
    mock_data = ClaimExtraction(
        provider_name="=CMD|' /C calc'!A0",
        patient_or_employee_name="Hacker",
        date_extracted="2026-10-09",
        currency="INR",
        items=[LineItem(description="Hack", amount=100.0)],
        total_extracted=100.0,
        confidence_score=0.9,
    )
    val_result = ValidationResult(is_valid=False, final_amount_inr=100.0, results=[])
    save_claim("expense", mock_data, val_result)

    res = client.get("/api/export.csv")
    assert res.status_code == 200
    # Formula prefix '=' must be sanitized with single quote "'"
    assert "'=CMD|" in res.text


def test_db_operational_error_retry():
    call_count = {"count": 0}

    @with_db_retry
    def transient_locked_operation():
        call_count["count"] += 1
        if call_count["count"] < 3:
            raise sqlite3.OperationalError("database is locked")
        return "success"

    result = transient_locked_operation()
    assert result == "success"
    assert call_count["count"] == 3
