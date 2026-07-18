from __future__ import annotations

from collections.abc import Callable
import time
from typing import TypeVar

T = TypeVar("T")


def with_retries(func: Callable[[], T], retries: int = 2, delay_seconds: float = 0.3) -> T:
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            return func()
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt == retries:
                break
            time.sleep(delay_seconds)

    if last_error is not None:
        raise last_error
    raise RuntimeError("Retry wrapper reached an unexpected state")
