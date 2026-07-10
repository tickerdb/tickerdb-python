"""Common shared types used across the SDK."""

from typing import Any, Literal, Optional, TypedDict

__all__ = [
    "Timeframe",
    "Stability",
    "RateLimits",
    "APIResponse",
]

Timeframe = Literal["daily", "weekly"]
Stability = Literal["fresh", "holding", "established", "volatile"]


class RateLimits(TypedDict, total=False):
    """Rate limit information parsed from response headers."""

    request_limit: Optional[int]
    requests_used: Optional[int]
    requests_remaining: Optional[int]
    request_reset: Optional[str]
    hourly_request_limit: Optional[int]
    hourly_requests_used: Optional[int]
    hourly_requests_remaining: Optional[int]
    hourly_request_reset: Optional[str]


class APIResponse(TypedDict):
    """Every SDK method returns a dict with parsed JSON data and rate limits."""

    data: Any
    rate_limits: RateLimits
