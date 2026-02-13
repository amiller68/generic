import logging
import os
import inspect
from fastapi import Request
from typing import Optional


# Used to log events that span a request on our server
class RequestFormatter(logging.Formatter):
    def format(self, record):
        if hasattr(record, "method"):
            record.method = record.method
        # Note: this should never happen, but if it does, we'll just set the request method and URL to N/A
        else:
            record.method = "N/A"
        if hasattr(record, "url"):
            record.url = record.url
        # Note: this should never happen, but if it does, we'll just set the request method and URL to N/A
        else:
            record.url = "N/A"

        # Add module name if available
        if hasattr(record, "module_name"):
            record.module_name = record.module_name
        else:
            record.module_name = record.module

        return super().format(record)


class Logger:
    logger: logging.Logger
    handler: logging.Handler
    request: Optional[Request]

    def __init__(self, log_path=None, debug=False, request: Optional[Request] = None):
        """
        Initialize a new Log instance
        - log_path - where to send output. If `None` logs are sent to the console
        - debug - whether to set debug level
        - request - optional request context
        """

        # Create the logger
        logger = logging.getLogger(__name__)

        # Set our debug mode
        if debug:
            logging.basicConfig(level=logging.DEBUG)
            # Hide debug logs from other libraries
            logging.getLogger("asyncio").setLevel(logging.WARNING)
            logging.getLogger("aiosqlite").setLevel(logging.WARNING)
        else:
            logging.basicConfig(level=logging.INFO)

        # Set where to send logs
        if log_path is not None and log_path.strip() != "":
            # Create parent directories if they don't exist
            log_path = log_path.strip()
            log_dir = os.path.dirname(log_path)
            os.makedirs(log_dir, exist_ok=True)
            self.handler = logging.FileHandler(log_path)
        else:
            self.handler = logging.StreamHandler()

        if logger.hasHandlers():
            logger.handlers.clear()
        logger.addHandler(self.handler)

        self.logger = logger
        self.request = request

        # Set appropriate formatter based on context
        formatter: logging.Formatter
        if request:
            formatter = RequestFormatter(
                "%(asctime)s - %(module_name)s - %(levelname)s - %(method)s - %(url)s - %(message)s"
            )
        else:
            formatter = logging.Formatter(
                "%(asctime)s - %(module_name)s - %(levelname)s - %(message)s"
            )
        self.handler.setFormatter(formatter)

    # TODO: be better about this
    def get_worker_logger(
        self, name: Optional[str] = None, attempt: Optional[int] = None
    ):
        formatter = logging.Formatter(
            f"[worker] %(asctime)s - {name} - {attempt} - %(levelname)s - %(message)s"
        )
        self.handler.setFormatter(formatter)
        return self.logger

    def with_request(self, request: Request) -> "Logger":
        """Create a new Logger instance with request context"""
        # Create a new logger instance that shares the same underlying logger and handler
        new_logger = Logger.__new__(Logger)
        new_logger.logger = self.logger
        new_logger.handler = self.handler
        new_logger.request = request

        # Update formatter for request context
        formatter = RequestFormatter(
            "%(asctime)s - %(module_name)s - %(levelname)s - %(method)s - %(url)s - %(message)s"
        )
        new_logger.handler.setFormatter(formatter)
        return new_logger

    def _get_caller_info(self):
        """Get the module name of the caller"""
        frame = inspect.currentframe()
        # Go up 2 frames: _get_caller_info -> log method -> actual caller
        if frame is not None and frame.f_back is not None:
            caller_frame = frame.f_back.f_back
            if caller_frame is not None:
                module = inspect.getmodule(caller_frame)
                if module is not None:
                    return module.__name__
        return "unknown"

    def _get_extra(self):
        """Build extra fields for logging"""
        extra = {"module_name": self._get_caller_info()}
        if self.request:
            extra["method"] = self.request.method
            extra["url"] = str(self.request.url)
        return extra

    def info(self, message):
        self.logger.info(message, extra=self._get_extra())

    def debug(self, message):
        self.logger.debug(message, extra=self._get_extra())

    def warn(self, message):
        self.logger.warning(message, extra=self._get_extra())

    def error(self, message):
        self.logger.error(message, extra=self._get_extra())
