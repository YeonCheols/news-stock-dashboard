"""Bounded retry support for transient external-data failures."""

from collections.abc import Callable
import time
from typing import TypeVar

from src.config import DATA_REQUEST_MAX_RETRIES, DATA_REQUEST_RETRY_DELAY_SECONDS


T = TypeVar("T")


def run_with_retries(operation: Callable[[], T]) -> T:
    """Run an operation with exponential backoff and re-raise its final error."""
    for attempt in range(DATA_REQUEST_MAX_RETRIES + 1):
        try:
            return operation()
        except Exception:
            if attempt == DATA_REQUEST_MAX_RETRIES:
                raise
            time.sleep(DATA_REQUEST_RETRY_DELAY_SECONDS * (2**attempt))
    raise RuntimeError("unreachable")
