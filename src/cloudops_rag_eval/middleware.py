import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from cloudops_rag_eval.logging import reset_request_context, set_request_context

logger = logging.getLogger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        correlation_id = request.headers.get("x-correlation-id") or request_id
        request.state.request_id = request_id
        request.state.correlation_id = correlation_id

        request_token, correlation_token = set_request_context(request_id, correlation_id)
        started_at = time.perf_counter()

        try:
            try:
                response = await call_next(request)
            except Exception:
                duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
                logger.exception(
                    "request_failed",
                    extra={
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": 500,
                        "duration_ms": duration_ms,
                        "client_host": request.client.host if request.client else None,
                    },
                )
                raise

            duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
            response.headers["x-request-id"] = request_id
            response.headers["x-correlation-id"] = correlation_id
            logger.info(
                "request_completed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                    "client_host": request.client.host if request.client else None,
                },
            )
            return response
        finally:
            reset_request_context(request_token, correlation_token)
