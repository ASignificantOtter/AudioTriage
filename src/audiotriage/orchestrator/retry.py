from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")
RETRYABLE_EXCEPTIONS = (TimeoutError, ConnectionError, OSError)


def with_retries(
    func: Callable[[], T],
    retries: int = 2,
    delay_seconds: float = 0.3,
    retry_on: tuple[type[Exception], ...] = RETRYABLE_EXCEPTIONS,
) -> T:
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            return func()
        except retry_on as exc:
            last_error = exc
            if attempt == retries:
                break
            time.sleep(delay_seconds)

    if last_error is not None:
        raise last_error
    raise RuntimeError("Retry wrapper reached an unexpected state")
