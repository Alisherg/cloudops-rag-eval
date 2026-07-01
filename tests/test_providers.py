import httpx
import pytest
from pydantic import SecretStr

from cloudops_rag_eval.config import Settings
from cloudops_rag_eval.providers import GeminiAnswerProvider
from cloudops_rag_eval.retrieval import RetrievedChunk


@pytest.mark.asyncio
async def test_gemini_provider_calls_generate_content() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert "models/gemini-2.5-flash:generateContent" in str(request.url)
        assert request.headers["x-goog-api-key"] == "test-key"
        payload = request.read().decode()
        assert "Cloud Run" in payload
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": (
                                        "Use min instances of 0 and clean up old images. "
                                        "[billing-quotas]"
                                    )
                                }
                            ]
                        }
                    }
                ]
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = GeminiAnswerProvider(
        Settings(gemini_api_key=SecretStr("test-key")),
        client=client,
    )

    answer = await provider.answer(
        "How do I keep Cloud Run cheap?",
        [
            RetrievedChunk(
                chunk_id="billing-quotas:5",
                document_id="billing-quotas",
                document_title="Billing and quotas",
                section_title="Cost controls for Cloud Run demos",
                text="For a low-cost demo, set Cloud Run minimum instances to 0.",
                score=0.9,
            )
        ],
    )
    await client.aclose()

    assert answer.refusal is False
    assert "[billing-quotas]" in answer.answer
