from fastapi import APIRouter, HTTPException, Request

from cloudops_rag_eval.schemas import (
    AskRequest,
    AskResponse,
    Citation,
    DocumentListResponse,
    DocumentSummary,
    SectionSummary,
)
from cloudops_rag_eval.service import RagService

router = APIRouter(prefix="/v1")


@router.post("/ask", response_model=AskResponse)
async def ask(payload: AskRequest, request: Request) -> AskResponse:
    service = _service(request)
    result = await service.ask(payload.question, payload.top_k)
    return AskResponse(
        answer=result.answer,
        citations=[
            Citation(
                document_id=chunk.document_id,
                document_title=chunk.document_title,
                section_title=chunk.section_title,
                chunk_id=chunk.chunk_id,
                score=chunk.score,
                excerpt=chunk.text[:500],
            )
            for chunk in result.contexts
        ],
        grounded=result.grounded,
        refusal=result.refusal,
        request_id=_request_id(request),
    )


@router.get("/documents", response_model=DocumentListResponse)
async def documents(request: Request) -> DocumentListResponse:
    service = _service(request)
    return DocumentListResponse(
        documents=[
            DocumentSummary(
                document_id=document.document_id,
                title=document.title,
                path=document.path.name,
                sections=[SectionSummary(title=section.title) for section in document.sections],
            )
            for document in service.list_documents()
        ]
    )


def _service(request: Request) -> RagService:
    service = getattr(request.app.state, "rag_service", None)
    if not isinstance(service, RagService):
        raise HTTPException(status_code=503, detail="Service is not ready")
    return service


def _request_id(request: Request) -> str:
    return str(getattr(request.state, "request_id", "unknown"))
