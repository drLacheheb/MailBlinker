import json
import logging
import os
import sys
from datetime import UTC, datetime
from typing import Any, cast

SUCCESS_LEVEL_NUM = 25
logging.addLevelName(SUCCESS_LEVEL_NUM, "SUCCESS")


class TrackerLogger(logging.Logger):
    def success(self, msg: str, *args: Any, **kwargs: Any) -> None:
        if self.isEnabledFor(SUCCESS_LEVEL_NUM):
            self._log(SUCCESS_LEVEL_NUM, msg, args, **kwargs)


logging.setLoggerClass(TrackerLogger)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "ts": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "service": getattr(record, "service", record.name),
            "msg": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0]:
            log_entry["error"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


def get_logger(service_name: str) -> TrackerLogger:
    logger = logging.getLogger(service_name)
    if not isinstance(logger, TrackerLogger):
        logger.__class__ = TrackerLogger

    if not logger.handlers:
        from logging.handlers import RotatingFileHandler

        try:
            from .config import settings

            log_file = settings.LOG_FILE or os.getenv("LOG_FILE", "logs/app.log")
        except Exception:
            log_file = os.getenv("LOG_FILE", "logs/app.log")

        log_dir = os.path.dirname(os.path.abspath(log_file))
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        try:
            handler = RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,
                backupCount=5,
                encoding="utf-8",
            )
            handler.setFormatter(JsonFormatter())
            logger.addHandler(handler)
        except Exception as e:
            sys.stderr.write(f"Warning: Could not create RotatingFileHandler for {log_file}: {e}\n")

        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(JsonFormatter())
        logger.addHandler(stream_handler)

        logger.setLevel(logging.INFO)

    old_factory = logging.getLogRecordFactory()

    def record_factory(*args: Any, **kwargs: Any) -> logging.LogRecord:
        record = old_factory(*args, **kwargs)
        if not hasattr(record, "service"):
            setattr(record, "service", service_name)
        return record

    logging.setLogRecordFactory(record_factory)
    return cast(TrackerLogger, logger)
