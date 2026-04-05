"""Exceptions for the TickerDB SDK."""

from typing import Any, Dict, Optional


class TickerDBError(Exception):
    """Raised when the TickerDB returns an error response.

    Attributes:
        status_code: HTTP status code of the response.
        error_type: Error type string from the API (e.g. "authentication_error").
        message: Human-readable error message.
        upgrade_url: URL to upgrade the API plan (present on 403/429 errors).
        reset: Rate limit reset timestamp (present on 429 errors).
        raw: The full parsed error body from the API.
    """

    def __init__(
        self,
        status_code: int,
        error_type: str,
        message: str,
        upgrade_url: Optional[str] = None,
        reset: Optional[str] = None,
        raw: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.status_code = status_code
        self.error_type = error_type
        self.message = message
        self.upgrade_url = upgrade_url
        self.reset = reset
        self.raw = raw or {}
        super().__init__(f"[{status_code}] {error_type}: {message}")


class AuthenticationError(TickerDBError):
    """Raised on 401 responses (invalid or missing API key)."""


class ForbiddenError(TickerDBError):
    """Raised on 403 responses (tier-restricted endpoint)."""


class NotFoundError(TickerDBError):
    """Raised on 404 responses (asset not found)."""


class RateLimitError(TickerDBError):
    """Raised on 429 responses (rate limit exceeded)."""


class DataUnavailableError(TickerDBError):
    """Raised on 503 responses (data temporarily unavailable)."""
