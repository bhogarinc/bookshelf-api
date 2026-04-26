"""Structured logging configuration."""

import json
import logging
import sys
import uuid
from contextvars import ContextVar
from typing import Any, Dict, Optional

correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id.get() or str(uuid.uuid4()),
            "source": {
                "file": record.filename,
                "line": record.lineno,
                "function": record.funcName
            }
        }
        
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, default=str)


def setup_logging(log_level: str = "INFO", log_format: str = "json") -> None:
    """Configure application logging."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers = []
    
    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    
    if log_format == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get logger with correlation ID support."""
    return logging.getLogger(name)


class LogContext:
    """Context manager for correlation IDs."""
    
    def __init__(self, cid: Optional[str] = None) -> None:
        self.cid = cid or str(uuid.uuid4())
        self.token = None
    
    def __enter__(self) -> "LogContext":
        self.token = correlation_id.set(self.cid)
        return self
    
    def __exit__(self, *args) -> None:
        if self.token:
            correlation_id.reset(self.token)
