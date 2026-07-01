from dataclasses import dataclass

from cloudops_rag_eval.documents import SourceDocument
from cloudops_rag_eval.providers import AnswerProvider
from cloudops_rag_eval.retrieval import ChromaRetriever, RetrievedChunk


@dataclass(frozen=True, slots=True)
class RagAnswer:
    answer: str
    contexts: list[RetrievedChunk]
    grounded: bool
    refusal: bool


class RagService:
    def __init__(self, retriever: ChromaRetriever, answer_provider: AnswerProvider) -> None:
        self.retriever = retriever
        self.answer_provider = answer_provider

    async def ask(self, question: str, top_k: int | None = None) -> RagAnswer:
        contexts = self.retriever.retrieve(question, top_k=top_k)
        generated = await self.answer_provider.answer(question, contexts)
        return RagAnswer(
            answer=generated.answer,
            contexts=contexts,
            grounded=bool(contexts),
            refusal=generated.refusal,
        )

    def list_documents(self) -> list[SourceDocument]:
        return self.retriever.list_documents()

    def is_ready(self) -> bool:
        return self.retriever.is_ready()
