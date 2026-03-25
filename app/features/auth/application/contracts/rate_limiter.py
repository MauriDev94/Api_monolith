from abc import ABC, abstractmethod


class RateLimiter(ABC):
    """Contract for window-based rate limiting."""

    @abstractmethod
    def check_or_raise(self, key: str, limit: int, window_seconds: int) -> None:
        """Raise when the key exceeded allowed attempts in the current window."""
        ...
