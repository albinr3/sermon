import logging
import sys

from loguru import logger

from src.config import settings


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame = logging.currentframe()
        depth = 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging() -> None:
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(settings.log_level)

    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        logger_instance = logging.getLogger(name)
        logger_instance.handlers = [InterceptHandler()]
        logger_instance.propagate = False

    logger.remove()
    logger.add(
        sys.stdout,
        level=settings.log_level,
        serialize=settings.log_json,
        backtrace=False,
        diagnose=False,
    )
