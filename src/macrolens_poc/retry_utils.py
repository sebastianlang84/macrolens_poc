from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Optional, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class RetryConfig:
    """Retry configuration for transient provider failures.

    Notes:
    - Exponential backoff is deterministic (no jitter) to keep runs reproducible.
    - Errors are re-raised after the final attempt.
    """

    max_attempts: int = 3
    base_delay_s: float = 0.5
    max_delay_s: float = 8.0
    multiplier: float = 2.0


def simple_retry(
    fn: Callable[[], T],
    max_attempts: int = 3,
    delay: float = 1.0,
    exceptions: tuple = (Exception,),
) -> T:
    """Simple retry wrapper for basic use cases."""
    cfg = RetryConfig(max_attempts=max_attempts, base_delay_s=delay)
    return retry_call(
        fn,
        cfg=cfg,
        should_retry=lambda e: isinstance(e, exceptions),
    )


def retry_call(
    fn: Callable[[], T],
    *,
    cfg: RetryConfig,
    should_retry: Callable[[Exception], bool],
    on_retry: Optional[Callable[[int, Exception, float], None]] = None,
) -> T:
    """Call `fn` with retry + exponential backoff.

    Parameters:
      - fn: callable to execute
      - cfg: retry configuration
      - should_retry: predicate for retryable exceptions
      - on_retry: optional callback (attempt_index, exc, delay_s)

    attempt_index is 1-based and refers to the attempt that *failed*.
    """

    if cfg.max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")

    attempt = 0
    while True:
        attempt += 1
        try:
            return fn()
        except Exception as exc:
            if attempt >= cfg.max_attempts or not should_retry(exc):
                raise

            delay_s = min(cfg.max_delay_s, cfg.base_delay_s * (cfg.multiplier ** (attempt - 1)))
            if on_retry is not None:
                on_retry(attempt, exc, delay_s)
            time.sleep(delay_s)
