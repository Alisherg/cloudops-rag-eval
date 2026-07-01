from pathlib import Path

import pytest

from cloudops_rag_eval.config import Settings
from cloudops_rag_eval.eval_runner import (
    EvaluationQuestion,
    evaluate_questions,
    summarize_results,
)
from cloudops_rag_eval.providers import create_answer_provider
from cloudops_rag_eval.retrieval import ChromaRetriever
from cloudops_rag_eval.service import RagService


@pytest.mark.asyncio
async def test_evaluation_scores_retrieval_and_refusal(tmp_path: Path) -> None:
    settings = Settings(chroma_path=tmp_path / "chroma", min_relevance_score=0.0)
    service = RagService(ChromaRetriever(settings), create_answer_provider(settings))
    questions = [
        EvaluationQuestion(
            id="cost",
            question="How should I keep a Cloud Run demo cheap?",
            expected_sources=("billing-quotas",),
            expect_refusal=False,
        ),
        EvaluationQuestion(
            id="kubernetes",
            question="Can Acme CloudOps deploy to customer-managed Kubernetes clusters?",
            expected_sources=("faq",),
            expect_refusal=True,
        ),
    ]

    results = await evaluate_questions(service, questions)
    summary = summarize_results(results)

    assert summary["questions"] == 2.0
    assert summary["pass_rate"] == 1.0
