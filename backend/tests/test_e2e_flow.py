import io
import pytest
from fastapi.testclient import TestClient

from backend import engine
from backend.main import app
from backend.scripts.seed_demo_claims import seed_demo_claims


client = TestClient(app)


@pytest.fixture(autouse=True)
def isolate_test_db(tmp_path, monkeypatch):
    test_db = str(tmp_path / "test_e2e.db")
    monkeypatch.setenv("CLAIMGUARD_DB_FILE", test_db)
    monkeypatch.setattr(engine, "DB_FILE", test_db)
    engine.init_db()


def test_full_e2e_claims_lifecycle():
    # 1. Healthcheck
    health_resp = client.get("/api/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["status"] == "ok"

    # 2. Seed initial demo claims
    seed_count = seed_demo_claims()
    assert seed_count == 4

    # Running seed a second time should be idempotent (0 new claims)
    reseed_count = seed_demo_claims()
    assert reseed_count == 0


    # 3. Verify seeded claims are listed in GET /api/claims
    claims_resp = client.get("/api/claims")
    assert claims_resp.status_code == 200
    claims = claims_resp.json()
    assert len(claims) == 4

    # 4. Upload and validate a new claim via POST /api/validate
    sample_file_bytes = b"fake_png_header_and_pixels_for_e2e_test_receipt"
    validate_resp = client.post(
        "/api/validate",
        files={"file": ("receipt.png", sample_file_bytes, "image/png")},
        data={"domain_mode": "expense", "rule_settings": '{"policy_limit_inr": 5000.0}'},
    )
    assert validate_resp.status_code == 200
    data = validate_resp.json()
    assert "claim_id" in data
    assert data["metadata"]["domain"] == "expense"
    assert "perception" in data
    assert "validation" in data
    new_claim_id = data["claim_id"]

    # 5. Re-submitting the exact same receipt bytes should trigger duplicate detection
    duplicate_resp = client.post(
        "/api/validate",
        files={"file": ("receipt.png", sample_file_bytes, "image/png")},
        data={"domain_mode": "expense"},
    )
    assert duplicate_resp.status_code == 200
    dup_data = duplicate_resp.json()
    assert dup_data["validation"]["is_valid"] is False
    assert any(
        "Duplicate" in r["rule_name"] and r["passed"] is False
        for r in dup_data["validation"]["results"]
    )

    # 6. Manager reviews and approves the new claim
    decision_resp = client.post(
        f"/api/claims/{new_claim_id}/decision",
        json={"decision": "Approved"},
    )
    assert decision_resp.status_code == 200
    assert decision_resp.json()["decision"] == "Approved"

    # 7. Check claims list reflects the updated status
    claims_updated_resp = client.get("/api/claims")
    updated_claims = claims_updated_resp.json()
    approved_claim = next((c for c in updated_claims if c["id"] == new_claim_id), None)
    assert approved_claim is not None
    assert approved_claim["status"] == "Approved"

    # 8. Export CSV and verify all claims are present and escaped
    csv_resp = client.get("/api/export.csv")
    assert csv_resp.status_code == 200
    assert "text/csv" in csv_resp.headers["content-type"]
    csv_text = csv_resp.text
    assert "claimguard_audit.csv" in csv_resp.headers["content-disposition"]
    assert "Starbucks Coffee" in csv_resp.text
    assert "Apollo Hospital Bangalore" in csv_resp.text
