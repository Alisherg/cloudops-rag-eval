import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from cloudops_rag_eval import __version__
from cloudops_rag_eval.api import router as api_router
from cloudops_rag_eval.config import Settings, get_settings
from cloudops_rag_eval.logging import configure_logging
from cloudops_rag_eval.middleware import RequestContextMiddleware
from cloudops_rag_eval.providers import create_answer_provider
from cloudops_rag_eval.retrieval import ChromaRetriever
from cloudops_rag_eval.schemas import ErrorResponse, HealthResponse, ReadyResponse
from cloudops_rag_eval.service import RagService

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()
    configure_logging(app_settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        retriever = ChromaRetriever(app_settings)
        answer_provider = create_answer_provider(app_settings)
        app.state.rag_service = RagService(retriever, answer_provider)
        logger.info(
            "service_started",
            extra={
                "app_env": app_settings.app_env,
                "documents": len(retriever.documents),
                "chunks": len(retriever.chunks),
                "llm_provider": app_settings.llm_provider.value,
            },
        )
        yield

    app = FastAPI(
        title="cloudops-rag-eval",
        version=__version__,
        lifespan=lifespan,
    )
    app.add_middleware(RequestContextMiddleware)
    app.include_router(api_router)

    @app.get("/health", response_model=HealthResponse)
    @app.get("/healthz", response_model=HealthResponse)
    async def health() -> HealthResponse:
        return HealthResponse(status="ok")

    @app.get("/readyz", response_model=ReadyResponse)
    async def readyz(request: Request) -> ReadyResponse:
        service = getattr(request.app.state, "rag_service", None)
        if not isinstance(service, RagService) or not service.is_ready():
            raise HTTPException(status_code=503, detail="Service is not ready")
        return ReadyResponse(status="ready", documents=len(service.list_documents()))

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
        return _error_response(request, str(exc.detail), exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        logger.info("validation_failed", extra={"errors": exc.errors()})
        return _error_response(request, "Request validation failed", 422)

    @app.exception_handler(Exception)
    async def unhandled_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_error", extra={"error_type": type(exc).__name__})
        return _error_response(request, "Internal server error", 500)

    return app


def _error_response(request: Request, message: str, status_code: int) -> JSONResponse:
    response = ErrorResponse(
        error=message,
        request_id=str(getattr(request.state, "request_id", "unknown")),
    )
    return JSONResponse(status_code=status_code, content=response.model_dump())


app = create_app()
