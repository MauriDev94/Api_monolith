from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    # loguru's type stubs declare Logger at the top-level, but the runtime
    # module (Cython) does not re-export it. Importing here is type-check only.
    from loguru import Logger


def setup_logger() -> Logger:
    """Configure application logging sinks for console, files, and structured JSON logs."""
    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)

    logger.remove()

    # Guarantee request_id exists in extra for all logs (even outside request context)
    logger.configure(patcher=lambda record: record["extra"].setdefault("request_id", "-"))

    # Human-friendly console logs for local development.
    logger.add(
        sys.stdout,
        colorize=True,
        enqueue=True,
        backtrace=False,
        diagnose=False,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{extra[request_id]}</cyan> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan> - "
            "<level>{message}</level>"
        ),
        level="INFO",
    )

    # Rotating plain-text logs.
    logger.add(
        logs_dir / "app_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="30 days",
        compression="zip",
        enqueue=True,
        backtrace=False,
        diagnose=False,
        format=(
            "{time:YYYY-MM-DD HH:mm:ss} | "
            "{level: <8} | "
            "{extra[request_id]} | "
            "{name}:{function}:{line} - {message}"
        ),
        level="DEBUG",
    )

    # Separate error file for incident triage.
    logger.add(
        logs_dir / "errors_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="90 days",
        compression="zip",
        enqueue=True,
        backtrace=False,
        diagnose=False,
        level="ERROR",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss} | "
            "{level: <8} | "
            "{extra[request_id]} | "
            "{name}:{function}:{line} - {message}"
        ),
    )

    # Structured logs for observability platforms.
    logger.add(
        logs_dir / "app_{time:YYYY-MM-DD}.jsonl",
        rotation="00:00",
        retention="30 days",
        compression="zip",
        enqueue=True,
        backtrace=False,
        diagnose=False,
        serialize=True,
        level="INFO",
    )

    return logger.bind(request_id="-")
