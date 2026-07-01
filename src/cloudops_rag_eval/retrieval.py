from dataclasses import dataclass
from typing import Any, cast

import chromadb
from chromadb.config import Settings as ChromaSettings

from cloudops_rag_eval.config import Settings
from cloudops_rag_eval.documents import (
    DocumentChunk,
    SourceDocument,
    chunk_documents,
    load_documents,
)
from cloudops_rag_eval.embeddings import HashingEmbeddingFunction, expanded_tokens

COLLECTION_NAME = "acme_cloudops_docs"


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    chunk_id: str
    document_id: str
    document_title: str
    section_title: str
    text: str
    score: float

    @property
    def source_label(self) -> str:
        return f"{self.document_title} - {self.section_title}"


class ChromaRetriever:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.documents = load_documents(settings.docs_path)
        self.chunks = chunk_documents(self.documents)
        self.embedding_function = HashingEmbeddingFunction()
        self.client = chromadb.PersistentClient(
            path=str(settings.chroma_path),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self._build_collection(self.chunks)

    def retrieve(self, query: str, top_k: int | None = None) -> list[RetrievedChunk]:
        limit = top_k or self.settings.retrieval_top_k
        candidate_limit = min(len(self.chunks), max(limit * 4, limit))
        result: Any = self.collection.query(
            query_texts=[query],
            n_results=candidate_limit,
            include=["documents", "metadatas", "distances"],
        )

        ids = result.get("ids", [[]])[0]
        texts = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        retrieved: list[RetrievedChunk] = []
        for chunk_id, text, metadata, distance in zip(
            ids, texts, metadatas, distances, strict=False
        ):
            semantic_score = max(0.0, 1.0 - float(distance))
            lexical_text = f"{metadata['document_title']} {metadata['section_title']} {text}"
            lexical_score = _lexical_score(query, lexical_text)
            score = min(1.0, (semantic_score * 0.45) + (lexical_score * 0.55))
            if score < self.settings.min_relevance_score:
                continue
            retrieved.append(
                RetrievedChunk(
                    chunk_id=str(chunk_id),
                    document_id=str(metadata["document_id"]),
                    document_title=str(metadata["document_title"]),
                    section_title=str(metadata["section_title"]),
                    text=str(text),
                    score=round(score, 4),
                )
            )

        return sorted(retrieved, key=lambda chunk: chunk.score, reverse=True)[:limit]

    def list_documents(self) -> list[SourceDocument]:
        return self.documents

    def is_ready(self) -> bool:
        return bool(self.documents and self.chunks and self.collection.count() == len(self.chunks))

    def _build_collection(self, chunks: list[DocumentChunk]) -> Any:
        if not chunks:
            raise ValueError("No document chunks were created")

        try:
            self.client.delete_collection(COLLECTION_NAME)
        except ValueError:
            pass

        collection = self.client.create_collection(
            name=COLLECTION_NAME,
            embedding_function=cast(Any, self.embedding_function),
            metadata={"hnsw:space": "cosine"},
        )
        collection.add(
            ids=[chunk.chunk_id for chunk in chunks],
            documents=[chunk.text for chunk in chunks],
            metadatas=[
                {
                    "document_id": chunk.document_id,
                    "document_title": chunk.document_title,
                    "section_title": chunk.section_title,
                }
                for chunk in chunks
            ],
        )
        return collection


def _lexical_score(query: str, text: str) -> float:
    query_terms = set(expanded_tokens(query))
    if not query_terms:
        return 0.0

    text_terms = set(expanded_tokens(text))
    if not text_terms:
        return 0.0

    matches = query_terms & text_terms
    coverage = len(matches) / len(query_terms)
    precision = len(matches) / len(text_terms)
    return min(1.0, (coverage * 0.8) + (precision * 0.2))
