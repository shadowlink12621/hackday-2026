from fastapi.testclient import TestClient
import pytest

from backend import case_store, engine
from backend.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolate_case_db(tmp_path, monkeypatch):
    db_path = str(tmp_path / "case-flow.db")
    monkeypatch.setenv("CLAIMGUARD_DB_FILE", db_path)
    monkeypatch.setattr(engine, "DB_FILE", db_path)
    engine.init_db()


def test_case_documents_are_separate_and_saved_locally(tmp_path, monkeypatch):
    db_path = str(tmp_path / "cases.db")
    monkeypatch.setenv("CLAIMGUARD_DB_FILE", db_path)
    monkeypatch.setattr(engine, "DB_FILE", db_path)
    monkeypatch.setattr(case_store, "DATA_DIR", tmp_path / "private-data")

    first = client.post("/api/cases", json={
        "patient_name": "Demo Patient One",
        "age": 42,
        "blood_group": "O+",
        "medical_conditions": ["user reported hypertension"],
    })
    second = client.post("/api/cases", json={"patient_name": "Demo Patient Two"})
    assert first.status_code == 201
    assert second.status_code == 201
    case_id = first.json()["case_id"]

    uploaded = client.post(
        f"/api/cases/{case_id}/documents",
        data={"category": "lab_report"},
        files={"file": ("blood-report.pdf", b"%PDF demo report bytes", "application/pdf")},
    )
    assert uploaded.status_code == 201
    assert uploaded.json()["storage"] == "local"

    case = client.get(f"/api/cases/{case_id}").json()
    assert case["patient_name"] == "Demo Patient One"
    assert case["patient_details"]["age"] == 42
    assert case["documents"][0]["category"] == "lab_report"
    assert len(client.get("/api/cases").json()) == 2

    downloaded = client.get(
        f"/api/cases/{case_id}/documents/{uploaded.json()['document_id']}/download"
    )
    assert downloaded.status_code == 200
    assert downloaded.content == b"%PDF demo report bytes"


def test_case_upload_rejects_invalid_mime_and_missing_case():
    created = client.post("/api/cases", json={"patient_name": "Demo Patient"})
    case_id = created.json()["case_id"]
    bad_type = client.post(
        f"/api/cases/{case_id}/documents",
        data={"category": "other"},
        files={"file": ("payload.exe", b"not a document", "application/octet-stream")},
    )
    assert bad_type.status_code == 400

    missing_case = client.post(
        "/api/cases/999/documents",
        data={"category": "other"},
        files={"file": ("report.pdf", b"%PDF demo", "application/pdf")},
    )
    assert missing_case.status_code == 404


def test_offline_claim_extraction_does_not_invent_sample_data(monkeypatch):
    from backend.gemma_client import extract_form_data

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("USE_LOCAL_LLM", raising=False)
    monkeypatch.setenv("FORCE_MOCK", "1")
    data, is_fallback, source = extract_form_data(b"some bytes", "image/jpeg", "", "health_insurance")
    assert is_fallback is True
    assert source == "offline_mock"
    assert data.provider_name.startswith("Not extracted")
    assert data.items == []
    assert data.confidence_score == 0.0


def test_offline_validation_cannot_return_an_approved_claim(monkeypatch):
    monkeypatch.setenv("FORCE_MOCK", "1")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    response = client.post(
        "/api/validate",
        data={"domain_mode": "health_insurance"},
        files={"file": ("bill.png", b"image bytes", "image/png")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["perception"]["structured_data"]["provider_name"].startswith("Not extracted")
    assert payload["perception"]["confidence"] == 0.0
    assert payload["validation"]["is_valid"] is False
    assert any(rule["rule_name"] == "Model extraction unavailable" for rule in payload["validation"]["results"])
