import argparse
import asyncio
import json
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cloudops_rag_eval.config import Settings
from cloudops_rag_eval.providers import create_answer_provider
from cloudops_rag_eval.retrieval import ChromaRetriever
from cloudops_rag_eval.service import RagAnswer, RagService


@dataclass(frozen=True, slots=True)
class EvaluationQuestion:
    id: str
    question: str
    expected_sources: tuple[str, ...]
    expect_refusal: bool


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    id: str
    question: str
    expected_sources: tuple[str, ...]
    actual_sources: tuple[str, ...]
    expected_refusal: bool
    actual_refusal: bool
    retrieval_hit: bool
    refusal_hit: bool
    answer: str

    @property
    def passed(self) -> bool:
        return self.retrieval_hit and self.refusal_hit


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the Acme CloudOps RAG evaluation set.")
    parser.add_argument("--questions", default="eval/questions.json")
    parser.add_argument("--fail-under", type=float, default=0.0)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    raise SystemExit(asyncio.run(_run(args)))


async def _run(args: argparse.Namespace) -> int:
    questions = load_questions(Path(args.questions))
    service = RagService(ChromaRetriever(Settings()), create_answer_provider(Settings()))
    results = await evaluate_questions(service, questions)
    summary = summarize_results(results)

    if args.as_json:
        print(json.dumps({"summary": summary, "results": [_result_dict(item) for item in results]}))
    else:
        print(f"questions={summary['questions']} pass_rate={summary['pass_rate']:.2f}")
        for result in results:
            status = "pass" if result.passed else "fail"
            sources = ",".join(result.actual_sources) or "-"
            print(f"{status} {result.id} sources={sources} refusal={result.actual_refusal}")

    return 1 if summary["pass_rate"] < args.fail_under else 0


def load_questions(path: Path) -> list[EvaluationQuestion]:
    raw_items = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw_items, list):
        raise ValueError("Evaluation questions file must contain a list")

    return [_parse_question(item) for item in raw_items]


async def evaluate_questions(
    service: RagService, questions: list[EvaluationQuestion]
) -> list[EvaluationResult]:
    results: list[EvaluationResult] = []
    for question in questions:
        answer = await service.ask(question.question)
        results.append(_evaluate_answer(question, answer))
    return results


def summarize_results(results: list[EvaluationResult]) -> dict[str, float]:
    total = len(results)
    if total == 0:
        return {
            "questions": 0.0,
            "pass_rate": 0.0,
            "source_recall": 0.0,
            "refusal_accuracy": 0.0,
        }

    return {
        "questions": float(total),
        "pass_rate": _mean(result.passed for result in results),
        "source_recall": _mean(result.retrieval_hit for result in results),
        "refusal_accuracy": _mean(result.refusal_hit for result in results),
    }


def _parse_question(item: object) -> EvaluationQuestion:
    if not isinstance(item, dict):
        raise ValueError("Evaluation question entries must be objects")

    expected_sources = item.get("expected_sources", [])
    if not isinstance(expected_sources, list):
        raise ValueError("expected_sources must be a list")

    return EvaluationQuestion(
        id=str(item["id"]),
        question=str(item["question"]),
        expected_sources=tuple(str(source) for source in expected_sources),
        expect_refusal=bool(item.get("expect_refusal", False)),
    )


def _evaluate_answer(question: EvaluationQuestion, answer: RagAnswer) -> EvaluationResult:
    actual_sources = tuple(dict.fromkeys(chunk.document_id for chunk in answer.contexts))
    retrieval_hit = all(source in actual_sources for source in question.expected_sources)
    return EvaluationResult(
        id=question.id,
        question=question.question,
        expected_sources=question.expected_sources,
        actual_sources=actual_sources,
        expected_refusal=question.expect_refusal,
        actual_refusal=answer.refusal,
        retrieval_hit=retrieval_hit,
        refusal_hit=answer.refusal == question.expect_refusal,
        answer=answer.answer,
    )


def _mean(values: Iterable[bool]) -> float:
    items = list(values)
    if not items:
        return 0.0
    return sum(1 for value in items if value) / len(items)


def _result_dict(result: EvaluationResult) -> dict[str, Any]:
    return {
        "id": result.id,
        "question": result.question,
        "expected_sources": result.expected_sources,
        "actual_sources": result.actual_sources,
        "expected_refusal": result.expected_refusal,
        "actual_refusal": result.actual_refusal,
        "retrieval_hit": result.retrieval_hit,
        "refusal_hit": result.refusal_hit,
        "passed": result.passed,
        "answer": result.answer,
    }
