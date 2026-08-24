"""In-memory login-attempt limiter. Deliberately simple (no Redis) since this app runs as a
single process -- a distributed rate limiter would be needed if that ever changes."""
import time
from collections import defaultdict

MAX_ATTEMPTS = 5
WINDOW_SECONDS = 15 * 60

_failed_attempts: dict[str, list[float]] = defaultdict(list)


def _prune(key: str, now: float) -> None:
    _failed_attempts[key] = [t for t in _failed_attempts[key] if now - t < WINDOW_SECONDS]


def is_locked_out(key: str) -> bool:
    now = time.monotonic()
    _prune(key, now)
    return len(_failed_attempts[key]) >= MAX_ATTEMPTS


def record_failed_attempt(key: str) -> None:
    _failed_attempts[key].append(time.monotonic())


def clear_attempts(key: str) -> None:
    _failed_attempts.pop(key, None)
