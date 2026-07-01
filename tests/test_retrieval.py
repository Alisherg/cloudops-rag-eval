from pathlib import Path

from cloudops_rag_eval.config import Settings
from cloudops_rag_eval.retrieval import ChromaRetriever


def test_retrieves_cloud_run_cost_sources(tmp_path: Path) -> None:
    retriever = ChromaRetriever(Settings(chroma_path=tmp_path / "chroma", min_relevance_score=0.0))

    chunks = retriever.retrieve("How do I keep Cloud Run demo costs low?", top_k=4)
    sources = {chunk.document_id for chunk in chunks}

    assert "billing-quotas" in sources
    assert chunks[0].document_id == "billing-quotas"
    assert chunks[0].score >= 0


def test_retrieves_unsupported_kubernetes_source(tmp_path: Path) -> None:
    retriever = ChromaRetriever(Settings(chroma_path=tmp_path / "chroma", min_relevance_score=0.0))

    chunks = retriever.retrieve("Can Acme deploy to Kubernetes clusters?", top_k=4)
    sources = {chunk.document_id for chunk in chunks}

    assert "faq" in sources
