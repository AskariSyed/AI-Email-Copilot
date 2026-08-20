import contextvars
import json
import logging
from datetime import datetime, timezone

from app.core.config import settings

# Context variable to hold the correlation ID for the current request
correlation_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "correlation_id", default="system"
)

class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that injects correlation_id and formats as JSON if
    VERBOSE_DIAGNOSTICS is enabled, otherwise standard text.
    """
    def format(self, record: logging.LogRecord) -> str:
        # Inject correlation ID
        record.correlation_id = correlation_id_var.get()
        
        # Privacy filters: Redact sensitive fields if they accidentally get passed
        if hasattr(record, "msg") and isinstance(record.msg, str):
            if "access_token" in record.msg.lower() or "refresh_token" in record.msg.lower():
                record.msg = "[REDACTED TOKEN]"
                
        if settings.VERBOSE_DIAGNOSTICS:
            log_data = {
                "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
                "level": record.levelname,
                "correlation_id": record.correlation_id,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "funcName": record.funcName,
                "line": record.lineno
            }
            if record.exc_info:
                log_data["exception"] = self.formatException(record.exc_info)
                
            # Allow injecting arbitrary extra fields from the logger
            for key, value in record.__dict__.items():
                if key not in ["args", "asctime", "created", "exc_info", "exc_text", "filename", "funcName", "levelname", "levelno", "lineno", "module", "msecs", "message", "msg", "name", "pathname", "process", "processName", "relativeCreated", "stack_info", "thread", "threadName", "correlation_id", "color_message"]:
                    log_data[key] = value
                    
            return json.dumps(log_data)
        else:
            # Standard human-readable format
            formatter = logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] [%(correlation_id)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            return formatter.format(record)

def setup_logging():
    """Configure the root logger."""
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredFormatter())
    logger.addHandler(handler)
    
    # Suppress overly verbose third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("googleapiclient").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

def get_logger(name: str):
    """Get a configured logger instance."""
    return logging.getLogger(name)
