import pytest
from fastapi.testclient import TestClient
from backend import engine
from backend.main import app
from backend.gemma_client import ClaimExtraction

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolate_test_db(tmp_path, monkeypatch):
    test_db = str(tmp_path / "test_companion.db")
    monkeypatch.setenv("CLAIMGUARD_DB_FILE", test_db)
    monkeypatch.setattr(engine, "DB_FILE", test_db)
    engine.init_db()


def test_model_status_endpoint():
    res = client.get("/api/model/status")
    assert res.status_code == 200
    data = res.json()
    assert "active_backend" in data
    assert "cloud_gemma_available" in data
    assert "local_ollama_online" in data
    assert data["offline_ready"] is True


def test_calendar_ics_download():
    extracted = ClaimExtraction(
        provider_name="Calendar test provider",
        currency="INR",
        total_extracted=100.0,
    )
    validation = engine.run_deterministic_checks(extracted, b"calendar fixture", "{}", "expense")
    engine.save_claim("expense", extracted, validation)
    claims_resp = client.get("/api/claims")
    claims = claims_resp.json()
    assert len(claims) > 0
    claim_id = claims[0]["id"]

    res = client.get(f"/api/claims/{claim_id}/calendar.ics")
    assert res.status_code == 200
    assert "text/calendar" in res.headers.get("content-type", "")
    assert f"claimguard_claim_{claim_id}.ics" in res.headers.get("content-disposition", "")
    ics_text = res.text
    assert "BEGIN:VCALENDAR" in ics_text
    assert "END:VCALENDAR" in ics_text
    assert "verify document deadline" in ics_text
    assert "not a universal or statutory cutoff" in ics_text
    assert "Provisional 7-day follow-up reminder" in ics_text


def test_calendar_ics_not_found():
    res = client.get("/api/claims/9999999/calendar.ics")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_scamcheck_fraud_detection():
    # Fee demand scam message
    scam_msg = (
        "Dear customer, your health claim of Rs 45,000 is approved. "
        "Pay fee of Rs 1,500 processing charges to clear tax and release funds immediately to bit.ly/claim-fund"
    )
    res = client.post("/api/scamcheck", json={"message_text": scam_msg})
    assert res.status_code == 200
    data = res.json()
    assert data["is_suspicious"] is True
    assert data["risk_level"] == "HIGH_RISK"
    assert data["risk_score"] >= 40
    assert any("UPFRONT PAYMENT DEMAND" in flag for flag in data["detected_red_flags"])
    assert "bimabharosa.irdai.gov.in" in data["official_portal_link"]


def test_scamcheck_safe_message():
    safe_msg = "Your policy renewal is due on 24th October. Please visit our branch or official portal to renew."
    res = client.post("/api/scamcheck", json={"message_text": safe_msg})
    assert res.status_code == 200
    data = res.json()
    assert data["is_suspicious"] is False
    assert data["risk_level"] == "SAFE"
    assert data["risk_score"] == 0


def test_scamcheck_empty_message_rejected():
    res = client.post("/api/scamcheck", json={"message_text": ""})
    assert res.status_code == 400


def test_insurers_knowledge_endpoints():
    res_list = client.get("/api/insurers")
    assert res_list.status_code == 200
    insurers = res_list.json()["insurers"]
    assert "hdfc_ergo" in insurers
    assert "star_health" in insurers
    assert "care_health" in insurers

    # Detail endpoint for HDFC ERGO
    res_detail = client.get("/api/insurers/hdfc_ergo")
    assert res_detail.status_code == 200
    hdfc_data = res_detail.json()
    assert hdfc_data["insurer_key"] == "hdfc_ergo"
    assert len(hdfc_data["key_traps"]) >= 3
    assert any("smoking" in trap.lower() or "lifestyle" in trap.lower() for trap in hdfc_data["key_traps"])

    # Non-existent insurer 404
    res_missing = client.get("/api/insurers/unknown_insurer_xyz")
    assert res_missing.status_code == 404
