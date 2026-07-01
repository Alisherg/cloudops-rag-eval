import json
import re
from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from cloudops_rag_eval.config import LlmProvider, Settings
from cloudops_rag_eval.retrieval import RetrievedChunk

SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
UNSUPPORTED_TERMS = (
    "kubernetes",
    "desktop agent",
    "desktop agents",
    "on-prem",
    "legal compliance",
    "certification",
    "certifications",
)


@dataclass(frozen=True, slots=True)
class GeneratedAnswer:
    answer: str
    refusal: bool


class AnswerProvider(Protocol):
    async def answer(self, question: str, contexts: list[RetrievedChunk]) -> GeneratedAnswer: ...


class MockAnswerProvider:
    async def answer(self, question: str, contexts: list[RetrievedChunk]) -> GeneratedAnswer:
        if not contexts:
            return GeneratedAnswer(
                answer=(
                    "I do not have enough information in the Acme CloudOps docs to answer "
                    "that question."
                ),
                refusal=True,
            )

        if _is_unsupported_request(question, contexts):
            first = _first_sentence(contexts[0].text)
            return GeneratedAnswer(
                answer=(
                    "The Acme CloudOps docs do not support that request. "
                    f"{first} [{contexts[0].document_id}]"
                ),
                refusal=True,
            )

        sentences = [
            f"{_first_sentence(chunk.text)} [{chunk.document_id}]" for chunk in contexts[:2]
        ]
        return GeneratedAnswer(answer=" ".join(sentences), refusal=False)


class OpenAIAnswerProvider:
    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        self.api_key = settings.openai_api_key.get_secret_value()
        self.base_url = settings.openai_base_url.rstrip("/")
        self.model = settings.openai_model

    async def answer(self, question: str, contexts: list[RetrievedChunk]) -> GeneratedAnswer:
        if not contexts:
            return GeneratedAnswer(
                answer=(
                    "I do not have enough information in the Acme CloudOps docs to answer "
                    "that question."
                ),
                refusal=True,
            )

        prompt_context = "\n\n".join(
            f"[{chunk.document_id} / {chunk.section_title}]\n{chunk.text}" for chunk in contexts
        )
        payload = {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Answer only from the provided Acme CloudOps documentation. "
                        "If the docs do not answer the question, say so clearly. "
                        "Cite source IDs in square brackets."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Question: {question}\n\nSources:\n{prompt_context}",
                },
            ],
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                content=json.dumps(payload),
            )
            response.raise_for_status()

        data = response.json()
        content = str(data["choices"][0]["message"]["content"]).strip()
        return GeneratedAnswer(
            answer=content,
            refusal=_is_unsupported_request(question, contexts) or "do not have enough" in content,
        )


class GeminiAnswerProvider:
    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required when LLM_PROVIDER=gemini")
        self.api_key = settings.gemini_api_key.get_secret_value()
        self.model = settings.gemini_model
        self.max_output_tokens = settings.gemini_max_output_tokens
        self._client = client
        self._timeout = settings.gemini_timeout_seconds

    async def answer(self, question: str, contexts: list[RetrievedChunk]) -> GeneratedAnswer:
        if not contexts:
            return GeneratedAnswer(
                answer=(
                    "I do not have enough information in the Acme CloudOps docs to answer "
                    "that question."
                ),
                refusal=True,
            )

        payload = self._build_payload(question, contexts)
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        )
        client = self._client or httpx.AsyncClient(timeout=self._timeout)
        close_client = self._client is None

        try:
            response = await client.post(
                url,
                headers={"x-goog-api-key": self.api_key},
                json=payload,
            )
            response.raise_for_status()
        finally:
            if close_client:
                await client.aclose()

        text = self._extract_text(response.json())
        if not text:
            return GeneratedAnswer(
                answer=(
                    "I do not have enough information in the Acme CloudOps docs to answer "
                    "that question."
                ),
                refusal=True,
            )

        return GeneratedAnswer(
            answer=text,
            refusal=_is_unsupported_request(question, contexts) or "do not have enough" in text,
        )

    def _build_payload(self, question: str, contexts: list[RetrievedChunk]) -> dict[str, Any]:
        prompt_context = "\n\n".join(
            f"[{chunk.document_id} / {chunk.section_title}]\n{chunk.text}" for chunk in contexts
        )
        return {
            "system_instruction": {
                "parts": [
                    {
                        "text": (
                            "Answer only from the provided Acme CloudOps documentation. "
                            "If the docs do not answer the question, say so clearly. "
                            "Cite source IDs in square brackets."
                        )
                    }
                ]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"Question: {question}\n\nSources:\n{prompt_context}"}],
                }
            ],
            "generationConfig": {
                "temperature": 0,
                "candidateCount": 1,
                "maxOutputTokens": self.max_output_tokens,
            },
        }

    def _extract_text(self, payload: dict[str, Any]) -> str:
        prompt_feedback = payload.get("promptFeedback") or {}
        if isinstance(prompt_feedback, dict) and prompt_feedback.get("blockReason"):
            return ""

        candidate = (payload.get("candidates") or [None])[0]
        if not isinstance(candidate, dict) or candidate.get("finishReason") == "SAFETY":
            return ""

        content = candidate.get("content") or {}
        parts = content.get("parts") or []
        text_parts = [
            part.get("text", "").strip()
            for part in parts
            if isinstance(part, dict) and isinstance(part.get("text"), str)
        ]
        return "\n".join(part for part in text_parts if part).strip()


def create_answer_provider(settings: Settings) -> AnswerProvider:
    if settings.llm_provider == LlmProvider.OPENAI:
        return OpenAIAnswerProvider(settings)
    if settings.llm_provider == LlmProvider.GEMINI:
        return GeminiAnswerProvider(settings)
    return MockAnswerProvider()


def _first_sentence(text: str) -> str:
    sentence = SENTENCE_RE.split(text.strip(), maxsplit=1)[0]
    return sentence[:360].strip()


def _is_unsupported_request(question: str, contexts: list[RetrievedChunk]) -> bool:
    normalized_question = question.lower()
    if not any(term in normalized_question for term in UNSUPPORTED_TERMS):
        return False

    context_text = " ".join(chunk.text for chunk in contexts).lower()
    return any(
        phrase in context_text
        for phrase in ("unsupported", "does not", "not deploy", "not supported")
    )
