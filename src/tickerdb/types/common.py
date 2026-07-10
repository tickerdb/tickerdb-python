"""Common shared types and the typing-compatibility shim.

The ``Literal`` / ``TypedDict`` imports here are re-exported so the other
``types`` submodules can import them from one place instead of repeating the
version check.
"""

import sys
from typing import Any, Optional

if sys.version_info >= (3, 8):
    from typing import Literal, TypedDict
else:
    from typing_extensions import Literal, TypedDict

__all__ = [
    "Literal",
    "TypedDict",
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
