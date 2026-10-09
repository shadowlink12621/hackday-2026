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


def test_policy_excerpt_redacts_personal_names_and_contacts():
    excerpt = policy_store._redact_text(
        "GEETA GOVIND SAIL\nMobile Number 9876543210\nCataract waiting period is 12 months."
    )
    assert "GEETA GOVIND SAIL" not in excerpt
    assert "9876543210" not in excerpt
    assert "Cataract waiting period" in excerpt
