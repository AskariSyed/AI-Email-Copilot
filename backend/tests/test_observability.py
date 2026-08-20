import json
import logging
from io import StringIO

from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.logging import correlation_id_var
from app.main import app


def test_correlation_id_middleware():
    client = TestClient(app)
    response = client.get("/api/v1/openapi.json")  # Use a fast default endpoint
    assert response.status_code == 200
    assert "X-Correlation-ID" in response.headers
    assert len(response.headers["X-Correlation-ID"]) > 10


def test_structured_logger(monkeypatch):
    # Enable verbose diagnostics to trigger JSON output
    monkeypatch.setattr(settings, "VERBOSE_DIAGNOSTICS", True)

    # Capture logs
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)

    from app.core.logging import StructuredFormatter

    handler.setFormatter(StructuredFormatter())

    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    correlation_id_var.set("test-123")

    logger.info("Test message", extra={"some_metric": 42})

    log_output = log_stream.getvalue()
    log_dict = json.loads(log_output)

    assert log_dict["correlation_id"] == "test-123"
    assert log_dict["message"] == "Test message"
    assert log_dict["some_metric"] == 42

    logger.removeHandler(handler)


def test_token_redaction(monkeypatch):
    monkeypatch.setattr(settings, "VERBOSE_DIAGNOSTICS", True)
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)

    from app.core.logging import StructuredFormatter

    handler.setFormatter(StructuredFormatter())

    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    logger.info("Here is the access_token = 12345")

    log_output = log_stream.getvalue()
    log_dict = json.loads(log_output)

    assert log_dict["message"] == "[REDACTED TOKEN]"

    logger.removeHandler(handler)
