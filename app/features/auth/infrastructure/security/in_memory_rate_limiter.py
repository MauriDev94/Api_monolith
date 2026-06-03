from collections import defaultdict
from datetime import UTC, datetime, timedelta
from threading import Lock

from app.core.exceptions.exceptions import TooManyRequestsError
from app.features.auth.application.contracts.rate_limiter import RateLimiter


class InMemoryRateLimiter(RateLimiter):
    """Simple in-memory limiter for local/prototype environments."""

    def __init__(self) -> None:
        self._hits: dict[str, list[datetime]] = defaultdict(list)
        self._lock = Lock()

    def check_or_raise(self, key: str, limit: int, window_seconds: int) -> None:
        now = datetime.now(UTC)
        cutoff = now - timedelta(seconds=window_seconds)

        with self._lock:
            active_hits = [hit for hit in self._hits[key] if hit > cutoff]
            if len(active_hits) >= limit:
                raise TooManyRequestsError("Too many requests, try again later")
            active_hits.append(now)
            self._hits[key] = active_hits
