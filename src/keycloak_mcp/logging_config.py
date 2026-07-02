"""Structured JSON logging (FR-8). Never logs body, tokens, passwords, or other PII."""

import json
import logging
from typing import Any


class JsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        """Render `record` as a JSON string."""
        payload: dict[str, Any] = {
            "level": record.levelname,
            "message": record.getMessage(),
        }
        payload.update(getattr(record, "structured_fields", {}))
        return json.dumps(payload)


def configure_logging(level: int = logging.INFO) -> None:
    """Install a JSON stream handler on the root logger."""
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)


def log_http_call(
    logger: logging.Logger, method: str, path: str, status_code: int
) -> None:
    """Log a single HTTP call with method, path, and status code."""
    logger.info(
        "keycloak http call",
        extra={
            "structured_fields": {"method": method, "path": path, "status": status_code}
        },
    )
