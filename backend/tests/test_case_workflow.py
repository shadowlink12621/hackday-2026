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


def test_offline_validation_fails_clearly_without_saving_empty_claim(monkeypatch):
    monkeypatch.setenv("FORCE_MOCK", "1")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    response = client.post(
        "/api/validate",
        data={"domain_mode": "health_insurance"},
        files={"file": ("bill.png", b"image bytes", "image/png")},
    )
    assert response.status_code == 422
    assert "No claim was saved" in response.json()["detail"]
    assert client.get("/api/claims").json() == []


def test_cloud_upload_without_consent_is_not_saved(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("FORCE_MOCK", "1")
    response = client.post(
        "/api/validate",
        data={"domain_mode": "health_insurance", "allow_cloud_processing": "false"},
        files={"file": ("bill.png", b"image bytes", "image/png")},
    )
    assert response.status_code == 422
    assert "consent is off" in response.json()["detail"]
    assert client.get("/api/claims").json() == []


def test_policy_named_pdf_is_routed_to_policy_navigator(monkeypatch):
    from backend import main

    def should_not_extract(*args, **kwargs):
        raise AssertionError("Policy PDFs must not enter claim extraction")

    monkeypatch.setattr(main, "extract_form_data", should_not_extract)
    response = client.post(
        "/api/validate",
        data={"domain_mode": "health_insurance", "allow_cloud_processing": "true"},
        files={"file": ("Policy_demo.pdf", b"%PDF-1.4 synthetic policy", "application/pdf")},
    )
    assert response.status_code == 422
    assert "Policy Navigator" in response.json()["detail"]
    assert client.get("/api/claims").json() == []


def test_user_confirmed_reminder_persists_on_case():
    created = client.post("/api/cases", json={"patient_name": "Local Test Patient"})
    case_id = created.json()["case_id"]
    saved = client.post(f"/api/cases/{case_id}/reminder", json={"confirmed_date": "2026-11-15"})
    assert saved.status_code == 200
    assert client.get(f"/api/cases/{case_id}").json()["reminder_date"] == "2026-11-15"

    cleared = client.post(f"/api/cases/{case_id}/reminder", json={"confirmed_date": None})
    assert cleared.status_code == 200
    assert client.get(f"/api/cases/{case_id}").json()["reminder_date"] is None


def test_validate_accepts_pdf_and_passes_cloud_consent(monkeypatch):
    from backend import main
    from backend.gemma_client import ClaimExtraction, LineItem

    received = {}

    def fake_extract(content, mime_type, prompt, domain, allow_cloud_processing=False):
        received.update(mime_type=mime_type, consent=allow_cloud_processing)
        return ClaimExtraction(
            provider_name="Example Hospital",
            items=[LineItem(description="Consultation", amount=100, category="doctor_fee")],
            total_extracted=100,
            confidence_score=0.9,
        ), False, "test_backend"

    monkeypatch.setattr(main, "extract_form_data", fake_extract)
    response = client.post(
        "/api/validate",
        data={"domain_mode": "health_insurance", "allow_cloud_processing": "true"},
        files={"file": ("bill.pdf", b"%PDF-1.4 test", "application/pdf")},
    )
    assert response.status_code == 200
    assert received == {"mime_type": "application/pdf", "consent": True}


def test_pdf_rejects_invalid_signature():
    response = client.post(
        "/api/validate",
        files={"file": ("bill.pdf", b"not really a PDF", "application/pdf")},
    )
    assert response.status_code == 400


def test_scanned_pdf_requires_explicit_cloud_ocr_consent(monkeypatch):
    from backend import gemma_client

    monkeypatch.setattr(gemma_client, "_extract_text_from_pdf", lambda _: "")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="appears scanned"):
        gemma_client.extract_form_data(b"%PDF-1.4 scan", "application/pdf", "", "health_insurance")


def test_api_token_protects_personal_data_routes(monkeypatch):
    monkeypatch.setenv("CLAIMGUARD_API_TOKEN", "test-access-token")
    assert client.get("/api/cases").status_code == 401
    authorized = client.get("/api/cases", headers={"Authorization": "Bearer test-access-token"})
    assert authorized.status_code == 200
    assert client.get("/api/health").json()["authentication_required"] is True
