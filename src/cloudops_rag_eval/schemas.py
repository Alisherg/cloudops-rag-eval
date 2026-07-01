from pydantic import BaseModel, Field


class Citation(BaseModel):
    document_id: str
    document_title: str
    section_title: str
    chunk_id: str
    score: float
    excerpt: str


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    top_k: int | None = Field(default=None, ge=1, le=8)


class AskResponse(BaseModel):
    answer: str
    citations: list[Citation]
    grounded: bool
    refusal: bool
    request_id: str


class SectionSummary(BaseModel):
    title: str


class DocumentSummary(BaseModel):
    document_id: str
    title: str
    path: str
    sections: list[SectionSummary]


class DocumentListResponse(BaseModel):
    documents: list[DocumentSummary]


class HealthResponse(BaseModel):
    status: str


class ReadyResponse(BaseModel):
    status: str
    documents: int


class ErrorResponse(BaseModel):
    error: str
    request_id: str
