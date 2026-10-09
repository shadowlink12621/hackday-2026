from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from backend import engine, policy_store
from backend.gemma_client import answer_with_policy
from backend.main import app


client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_database(tmp_path, monkeypatch):
    db_path = str(tmp_path / "policy-test.db")
    monkeypatch.setattr(engine, "DB_FILE", db_path)
    engine.init_db()
    policy_store.init_policy_db()


def test_ingest_policy_and_page_retrieval(monkeypatch):
    class FakePage:
        def __init__(self, text):
            self.text = text

        def extract_text(self):
            return self.text

    monkeypatch.setattr(policy_store, "extract_pdf_pages", lambda _: [
        {"page": 1, "text": "Policy schedule. OPD cover is INR 3000 per family.", "images": []},
        {"page": 2, "text": "Specific waiting period: cataract is 12 months.", "images": []},
        {"page": 3, "text": "", "images": []},
    ])
    saved = policy_store.ingest_policy_pdf(b"%PDF demo bytes", "demo-policy.pdf")
    assert saved["page_count"] == 3
    assert saved["unreadable_pages"] == [3]
    assert saved["insurer"] is None
    assert policy_store.ingest_policy_pdf(b"%PDF demo bytes", "renamed.pdf")["duplicate_upload"] is True

    matches = policy_store.retrieve_policy_pages(saved["policy_id"], "cataract waiting period")
    assert matches[0]["page"] == 2
    profile = policy_store.get_policy(saved["policy_id"])
    assert profile["profile"]
    assert profile["unreadable_pages"] == [3]
    assert "summary" not in profile
    assert "sections" not in profile


def test_policy_upload_rejects_non_pdf():
    response = client.post(
        "/api/policies",
        files={"file": ("policy.txt", b"not a PDF", "text/plain")},
    )
    assert response.status_code == 400


def test_policy_chat_offline_returns_source_excerpts(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("USE_LOCAL_LLM", raising=False)
    result = answer_with_policy(
        "What is the cataract waiting period?",
        [{"page": 9, "text": "The specific waiting period for cataract is 12 months."}],
    )
    assert result["model_used"] == "retrieval_only"
    assert "not inferred coverage" in result["answer"]
    assert result["citations"][0]["page"] == 9
    assert "12 months" in result["answer"]


def test_model_connection_check_reports_missing_credentials(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    response = client.post("/api/model/check")
    assert response.status_code == 503
    assert "GEMINI_API_KEY" in response.json()["detail"]


def test_cloud_policy_chat_requires_explicit_consent_and_respects_zero_env(monkeypatch):
    from types import SimpleNamespace
    from backend import gemma_client

    class FakeModels:
        def generate_content(self, **kwargs):
            return SimpleNamespace(text="The policy states a 12-month waiting period [page 9].")

    class FakeClient:
        def __init__(self, **kwargs):
            self.models = FakeModels()

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("USE_LOCAL_LLM", "0")
    monkeypatch.setattr(gemma_client, "HAS_GENAI", True)
    monkeypatch.setattr(gemma_client, "genai", SimpleNamespace(Client=FakeClient))
    evidence = [{"page": 9, "text": "The specific waiting period for cataract is 12 months."}]

    without_consent = gemma_client.answer_with_policy("Cataract waiting period?", evidence)
    assert without_consent["model_used"] == "retrieval_only"
    with_consent = gemma_client.answer_with_policy("Cataract waiting period?", evidence, True)
    assert with_consent["model_used"].startswith("cloud_gemma")


def test_policy_summary_api_forwards_explicit_consent_and_source_pages(monkeypatch):
    class FakePage:
        def __init__(self, text):
            self.text = text

        def extract_text(self):
            return self.text

    monkeypatch.setattr(policy_store, "extract_pdf_pages", lambda _: [
        {"page": 1, "text": "Policy name: Example Plan. Coverage period listed.", "images": []},
    ])
    policy_id = policy_store.ingest_policy_pdf(b"%PDF summary fixture", "fixture.pdf")["policy_id"]
    received = {}

    def fake_summary(pages, consent):
        received["consent"] = consent
        received["pages"] = pages
        return {
            "summary": {"policy_name": {"fact": "Example Plan", "pages": [1]}},
            "model_used": "cloud_gemma (test-model)",
            "detail": None,
        }

    monkeypatch.setattr("backend.main.summarize_policy_pages", fake_summary)
    response = client.post(
        f"/api/policies/{policy_id}/summary",
        json={"allow_cloud_processing": True},
    )
    assert response.status_code == 200
    assert received["consent"] is True
    assert response.json()["sources"][0]["page"] == 1


def test_policy_summary_is_source_only_without_consent(monkeypatch):
    from backend import gemma_client

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    result = gemma_client.summarize_policy_pages(
        [{"page": 1, "text": "Policy wording."}], allow_cloud_processing=False
    )
    assert result["summary"] is None
    assert result["model_used"] == "retrieval_only"


def test_policy_summary_refuses_to_claim_complete_analysis_with_unreadable_pages():
    from backend import gemma_client

    result = gemma_client.summarize_policy_pages(
        [{"page": 1, "text": "Readable wording"}, {"page": 2, "text": ""}],
        allow_cloud_processing=True,
    )
    assert result["summary"] is None
    assert result["model_used"] == "ocr_required"
    assert "pages 2" in result["detail"]


def test_generated_policy_summary_filters_unknown_citation_pages(monkeypatch):
    import json
    from backend import gemma_client

    payload = {
        "insurer": {"fact": "Example insurer", "pages": [1, 99]},
        "policy_name": None,
        "policy_type": None,
        "policy_period": None,
        "sum_insured": None,
        "insured_members": [],
        "benefits": [{"fact": "Hospitalization cover", "pages": [2]}],
        "sub_limits": [],
        "waiting_periods": [],
        "exclusions": [],
        "claim_requirements": [],
        "network_terms": [],
        "uncertainties": [],
    }

    class FakeModels:
        def generate_content(self, **kwargs):
            return SimpleNamespace(text=json.dumps(payload))

    class FakeClient:
        def __init__(self, **kwargs):
            self.models = FakeModels()

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("USE_LOCAL_LLM", "0")
    monkeypatch.setattr(gemma_client, "HAS_GENAI", True)
    monkeypatch.setattr(gemma_client, "genai", SimpleNamespace(Client=FakeClient))
    result = gemma_client.summarize_policy_pages(
        [{"page": 1, "text": "Example insurer"}, {"page": 2, "text": "Hospitalization cover"}],
        allow_cloud_processing=True,
    )
    assert result["model_used"].startswith("cloud_gemma")
    assert result["summary"]["insurer"]["pages"] == [1]
    assert result["summary"]["benefits"][0]["pages"] == [2]


def test_policy_excerpt_redacts_personal_names_and_contacts():
    excerpt = policy_store._redact_text(
        "ANANYA SHARMA\nMobile Number 9876543210\nCataract waiting period is 12 months."
    )
    assert "ANANYA SHARMA" in excerpt
    assert "9876543210" not in excerpt
    assert "Cataract waiting period" in excerpt


def test_policy_excerpt_keeps_policy_terms_and_dates():
    excerpt = policy_store._redact_text(
        "POLICY PERIOD 01/04/2025 to 31/03/2026\n"
        "SUM INSURED FAMILY FLOATER INR 500000\n"
        "Date of Birth: 01/04/1980"
    )
    assert "POLICY PERIOD 01/04/2025 to 31/03/2026" in excerpt
    assert "SUM INSURED FAMILY FLOATER INR 500000" in excerpt
    assert "Date of Birth: 01/04/1980" not in excerpt


def test_gemma4_is_default_and_full_policy_summary_covers_every_page(monkeypatch):
    import json
    import re
    from backend import gemma_client

    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.delenv("GEMMA_MODEL", raising=False)
    assert gemma_client._cloud_model_name() == "gemma-4-26b-a4b-it"

    class FakeModels:
        calls = 0

        def generate_content(self, **kwargs):
            self.calls += 1
            pages_in_prompt = [int(value) for value in re.findall(r"\[PDF page (\d+)", kwargs["contents"])]
            first = pages_in_prompt[0]
            return SimpleNamespace(text=json.dumps({
                "insurer": None,
                "policy_name": {"fact": f"Plan on page {first}", "pages": [first]},
                "policy_type": None,
                "policy_period": None,
                "sum_insured": None,
                "insured_members": [],
                "benefits": [{"fact": f"Benefit from page {first}", "pages": [first]}],
                "sub_limits": [],
                "waiting_periods": [],
                "exclusions": [],
                "claim_requirements": [],
                "network_terms": [],
                "uncertainties": [],
            }))

    models = FakeModels()

    class FakeClient:
        def __init__(self, **kwargs):
            self.models = models

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("USE_LOCAL_LLM", "0")
    monkeypatch.setattr(gemma_client, "HAS_GENAI", True)
    monkeypatch.setattr(gemma_client, "genai", SimpleNamespace(Client=FakeClient))
    pages = [{"page": page, "text": f"Policy clause page {page}"} for page in range(1, 22)]
    result = gemma_client.summarize_policy_pages(pages, allow_cloud_processing=True)

    assert models.calls == 3, result
    assert result["pages_processed"] == 21
    assert result["model_used"] == "cloud_gemma (gemma-4-26b-a4b-it)"
    assert [fact["pages"][0] for fact in result["summary"]["benefits"]] == [1, 11, 21]


def test_scanned_policy_requires_explicit_cloud_consent(monkeypatch):
    monkeypatch.setattr(policy_store, "extract_pdf_pages", lambda _: [
        {"page": 1, "text": "", "images": [{"bytes": b"image", "mime_type": "image/png"}]},
    ])
    with pytest.raises(ValueError, match="Enable cloud-processing consent"):
        policy_store.ingest_policy_pdf(b"%PDF scanned", "scanned.pdf")


def test_policy_chat_uses_gemma_only_after_consent_and_keeps_turn_context(monkeypatch):
    import json
    from backend.policy import llm
    from backend.policy.chat import answer

    class FakeModels:
        calls = []

        def generate_content(self, **kwargs):
            self.calls.append(kwargs)
            return SimpleNamespace(text=json.dumps({
                "answer": "The cited room limit applies [page 4].",
                "citations": [{"page": 4, "quote": "Room charges are limited."}],
            }))

    models = FakeModels()

    class FakeClient:
        def __init__(self, **kwargs):
            self.models = models

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMMA_MODEL", "gemma-4-26b-a4b-it")
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.setenv("USE_LOCAL_LLM", "0")
    monkeypatch.setattr(llm, "HAS_GENAI", True)
    monkeypatch.setattr(llm, "genai", SimpleNamespace(Client=FakeClient))
    evidence = [{"page": 4, "text": "Room charges are limited."}]
    history = [{"role": "user", "text": "What is the room rent cap?"}]

    offline = answer("Does that apply to ICU?", evidence, False, history)
    assert offline["model_used"] == "retrieval_only"
    assert models.calls == []

    cloud = answer("Does that apply to ICU?", evidence, True, history)
    assert cloud["model_used"] == "cloud_gemma (gemma-4-26b-a4b-it)"
    assert "What is the room rent cap?" in models.calls[0]["contents"]
    assert cloud["citations"][0]["quote"] == "Room charges are limited."


def test_policy_chat_api_forwards_consent_and_history(monkeypatch):
    monkeypatch.setattr(policy_store, "extract_pdf_pages", lambda _: [
        {"page": 1, "text": "Room charges are limited to a standard room.", "images": []},
    ])
    policy_id = policy_store.ingest_policy_pdf(b"%PDF chat fixture", "chat-policy.pdf")["policy_id"]
    received = {}

    def fake_answer(question, evidence, consent, history):
        received.update(question=question, evidence=evidence, consent=consent, history=history)
        return {"answer": "Source-backed answer", "citations": [], "model_used": "test"}

    monkeypatch.setattr("backend.main.answer_with_policy", fake_answer)
    response = client.post(f"/api/policies/{policy_id}/chat", json={
        "question": "Does that include ICU?",
        "allow_cloud_processing": True,
        "history": [{"role": "user", "text": "What is the room rent limit?"}],
    })
    assert response.status_code == 200
    assert received["consent"] is True
    assert "room charges" in received["evidence"][0]["text"].lower()
    assert received["history"][0]["text"] == "What is the room rent limit?"
