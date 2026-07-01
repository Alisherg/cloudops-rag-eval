from pathlib import Path

from fastapi.testclient import TestClient

from cloudops_rag_eval.config import Settings
from cloudops_rag_eval.main import create_app


def test_health_and_readiness(tmp_path: Path) -> None:
    app = create_app(Settings(chroma_path=tmp_path / "chroma", min_relevance_score=0.0))

    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}
        assert client.get("/healthz").json() == {"status": "ok"}
        ready = client.get("/readyz")

    assert ready.status_code == 200
    assert ready.json()["documents"] >= 8


def test_ask_returns_citations_and_request_id(tmp_path: Path) -> None:
    app = create_app(Settings(chroma_path=tmp_path / "chroma", min_relevance_score=0.0))

    with TestClient(app) as client:
        response = client.post(
            "/v1/ask",
            json={"question": "How should I keep a Cloud Run demo cheap?"},
            headers={"x-request-id": "req-test-123"},
        )

    body = response.json()
    assert response.status_code == 200
    assert response.headers["x-request-id"] == "req-test-123"
    assert body["request_id"] == "req-test-123"
    assert body["grounded"] is True
    assert body["citations"]


def test_ask_refuses_unsupported_topic(tmp_path: Path) -> None:
    app = create_app(Settings(chroma_path=tmp_path / "chroma", min_relevance_score=0.0))

    with TestClient(app) as client:
        response = client.post(
            "/v1/ask",
            json={"question": "Can Acme CloudOps deploy to customer-managed Kubernetes clusters?"},
        )

    body = response.json()
    assert response.status_code == 200
    assert body["refusal"] is True
    assert {citation["document_id"] for citation in body["citations"]} & {"faq", "onboarding"}


def test_validation_error_has_clean_shape(tmp_path: Path) -> None:
    app = create_app(Settings(chroma_path=tmp_path / "chroma", min_relevance_score=0.0))

    with TestClient(app) as client:
        response = client.post("/v1/ask", json={"question": ""})

    assert response.status_code == 422
    assert response.json()["error"] == "Request validation failed"
    assert "request_id" in response.json()
