import contextvars
import json
import logging
import re
import sys
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)
correlation_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "correlation_id", default=None
)

SENSITIVE_KEYS = {
    "authorization",
    "api_key",
    "apikey",
    "access_token",
    "refresh_token",
    "token",
    "password",
    "secret",
    "openai_api_key",
}
EMAIL_RE = re.compile(r"(?i)\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b")
STANDARD_RECORD_ATTRS = set(logging.makeLogRecord({}).__dict__)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_var.get(),
            "correlation_id": correlation_id_var.get(),
        }

        for key, value in record.__dict__.items():
            if key not in STANDARD_RECORD_ATTRS and key not in payload:
                payload[key] = mask_sensitive(value, key)

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str, separators=(",", ":"))


def configure_logging(level: str) -> None:
    root = logging.getLogger()
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
    root.setLevel(level.upper())

    logging.getLogger("uvicorn.access").disabled = True


def set_request_context(
    request_id: str, correlation_id: str
) -> tuple[contextvars.Token[str | None], contextvars.Token[str | None]]:
    request_token = request_id_var.set(request_id)
    correlation_token = correlation_id_var.set(correlation_id)
    return request_token, correlation_token


def reset_request_context(
    request_token: contextvars.Token[str | None],
    correlation_token: contextvars.Token[str | None],
) -> None:
    request_id_var.reset(request_token)
    correlation_id_var.reset(correlation_token)


def mask_mapping(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {key: mask_sensitive(value, key) for key, value in payload.items()}


def mask_sensitive(value: Any, key: str | None = None) -> Any:
    if key and _is_sensitive_key(key):
        return "[masked]"

    if isinstance(value, str):
        return EMAIL_RE.sub("[masked-email]", value)

    if isinstance(value, Mapping):
        return mask_mapping(value)

    if isinstance(value, list):
        return [mask_sensitive(item) for item in value]

    return value


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return normalized in SENSITIVE_KEYS or normalized.endswith("_token")
