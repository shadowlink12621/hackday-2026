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

    monkeypatch.setattr(
        policy_store,
        "PdfReader",
        lambda _: SimpleNamespace(pages=[
            FakePage("Policy schedule. OPD cover is INR 3000 per family."),
            FakePage("Specific waiting period: cataract is 12 months."),
        ]),
    )
    saved = policy_store.ingest_policy_pdf(b"%PDF demo bytes", "demo-policy.pdf")
    assert saved["page_count"] == 2
    assert saved["insurer"] is None
    assert policy_store.ingest_policy_pdf(b"%PDF demo bytes", "renamed.pdf")["duplicate_upload"] is True

    matches = policy_store.retrieve_policy_pages(saved["policy_id"], "cataract waiting period")
    assert matches[0]["page"] == 2
    profile = policy_store.get_policy(saved["policy_id"])
    assert profile["profile"]


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

    monkeypatch.setattr(
        policy_store,
        "PdfReader",
        lambda _: SimpleNamespace(pages=[FakePage("Policy name: Example Plan. Coverage period listed.")]),
    )
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
    assert "ANANYA SHARMA" not in excerpt
    assert "9876543210" not in excerpt
    assert "Cataract waiting period" in excerpt
