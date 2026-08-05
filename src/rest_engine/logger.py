"""Structured logging for the REST engine.

Uses Python's standard `logging` module (no extra dependency). Consumers
of this library can attach their own handlers/formatters to the
"rest_engine" logger; by default a NullHandler is attached so the library
stays silent unless the host application configures logging.
"""

from __future__ import annotations

import logging

logger = logging.getLogger("rest_engine")
logger.addHandler(logging.NullHandler())


def configure_default_logging(level: int = logging.INFO) -> None:
    """Convenience helper for local development / examples.

    Not called automatically by the library — applications should own
    their own logging configuration in production.
    """
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )
    handler.setFormatter(formatter)
    logger.handlers = [handler]
    logger.setLevel(level)
    logger.propagate = False
