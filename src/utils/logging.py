"""Structured JSON logging for the newsletter agent system."""

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


class JsonFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured JSON logs.

    Includes: timestamp, agent_name, phase, status, error details, and custom fields.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON object."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add agent-specific fields if present
        if hasattr(record, "agent_name"):
            log_entry["agent_name"] = record.agent_name
        if hasattr(record, "phase"):
            log_entry["phase"] = record.phase
        if hasattr(record, "status"):
            log_entry["status"] = record.status
        if hasattr(record, "iteration"):
            log_entry["iteration"] = record.iteration
        if hasattr(record, "quality_score"):
            log_entry["quality_score"] = record.quality_score
        if hasattr(record, "duration_ms"):
            log_entry["duration_ms"] = record.duration_ms

        # Add error details if present
        if record.exc_info:
            log_entry["error"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
            }
        if hasattr(record, "error_details"):
            log_entry["error_details"] = record.error_details

        # Add any extra fields
        if hasattr(record, "extra_fields"):
            log_entry.update(record.extra_fields)

        return json.dumps(log_entry, default=str)


class AgentLogger:
    """
    Logger adapter for agent-specific logging with structured context.

    Usage:
        logger = AgentLogger("ResearchAgent", phase="research")
        logger.info("Starting research", status="running", iteration=1)
        logger.error("Research failed", error_details={"reason": "timeout"})
    """

    def __init__(
        self,
        agent_name: str,
        phase: Optional[str] = None,
        base_logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize agent logger.

        Args:
            agent_name: Name of the agent (e.g., "ResearchAgent")
            phase: Current workflow phase (e.g., "research", "writing")
            base_logger: Base logger to use (default: creates new one)
        """
        self.agent_name = agent_name
        self.phase = phase
        self._logger = base_logger or logging.getLogger(f"agent.{agent_name}")

    def _log(self, level: int, message: str, **kwargs: Any) -> None:
        """Internal log method with structured fields."""
        extra = {
            "agent_name": self.agent_name,
            "extra_fields": {},
        }

        if self.phase:
            extra["phase"] = self.phase

        # Extract known fields
        known_fields = ["status", "iteration", "quality_score", "duration_ms", "error_details"]
        for field in known_fields:
            if field in kwargs:
                extra[field] = kwargs.pop(field)

        # Remaining kwargs go to extra_fields
        if kwargs:
            extra["extra_fields"] = kwargs

        self._logger.log(level, message, extra=extra)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        self._log(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message."""
        self._log(logging.CRITICAL, message, **kwargs)

    def set_phase(self, phase: str) -> None:
        """Update the current phase."""
        self.phase = phase


def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[Path] = None,
    console_output: bool = True,
) -> logging.Logger:
    """
    Setup structured JSON logging for the newsletter system.

    Args:
        log_level: Logging level (default: INFO)
        log_file: Optional path to log file
        console_output: Whether to output to console (default: True)

    Returns:
        Configured root logger
    """
    root_logger = logging.getLogger("agent")
    root_logger.setLevel(log_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    json_formatter = JsonFormatter()

    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(json_formatter)
        root_logger.addHandler(console_handler)

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(json_formatter)
        root_logger.addHandler(file_handler)

    return root_logger


def get_agent_logger(agent_name: str, phase: Optional[str] = None) -> AgentLogger:
    """
    Get an agent-specific logger.

    Args:
        agent_name: Name of the agent
        phase: Current workflow phase

    Returns:
        Configured AgentLogger instance
    """
    return AgentLogger(agent_name=agent_name, phase=phase)
