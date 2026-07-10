"""Shared transport concerns for the sync and async clients.

This module is the single home for everything that does not depend on whether
the client is synchronous or asynchronous: default configuration, request
specifications, response-envelope building, rate-limit header parsing, and the
mapping from HTTP error responses to typed exceptions.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx

from ._version import __version__
from .exceptions import (
    AuthenticationError,
    DataUnavailableError,
    ForbiddenError,
    InsufficientCreditsError,
    NotFoundError,
    RateLimitError,
    TickerDBError,
)
from .types import RateLimits

DEFAULT_BASE_URL = "https://api.tickerdb.com/v1"
DEFAULT_TIMEOUT = 30.0
USER_AGENT = f"tickerdb-python/{__version__}"


@dataclass(frozen=True)
class RequestSpec:
    """A transport-agnostic description of a single HTTP request.

    Endpoint builders return one of these; each client turns it into an actual
    request. ``None`` values in ``params`` are dropped before sending.
    """

    method: str
    path: str
    params: Optional[Dict[str, Any]] = None
    json: Optional[Dict[str, Any]] = None


def default_headers(api_key: str) -> Dict[str, str]:
    """Build the default request headers for an authenticated client."""
    return {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
    }


def clean_params(params: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Drop ``None`` values so unset optional parameters are not sent."""
    if not params:
        return params
    return {k: v for k, v in params.items() if v is not None}


def parse_rate_limits(headers: httpx.Headers) -> RateLimits:
    """Extract rate-limit information from response headers."""

    def _int_or_none(key: str) -> Optional[int]:
        val = headers.get(key)
        if val is None:
            return None
        try:
            return int(val)
        except (ValueError, TypeError):
            return None

    return RateLimits(
        request_limit=_int_or_none("X-Request-Limit"),
        requests_used=_int_or_none("X-Requests-Used"),
        requests_remaining=_int_or_none("X-Requests-Remaining"),
        request_reset=headers.get("X-Request-Reset"),
        hourly_request_limit=_int_or_none("X-Hourly-Request-Limit"),
        hourly_requests_used=_int_or_none("X-Hourly-Requests-Used"),
        hourly_requests_remaining=_int_or_none("X-Hourly-Requests-Remaining"),
        hourly_request_reset=headers.get("X-Hourly-Request-Reset"),
    )


def raise_for_status(response: httpx.Response) -> None:
    """Raise a typed :class:`TickerDBError` if the response indicates an error."""
    if response.status_code < 400:
        return

    try:
        body = response.json()
    except Exception:
        raise TickerDBError(
            status_code=response.status_code,
            error_type="unknown_error",
            message=response.text or "Unknown error",
        )

    error = body.get("error", {})
    error_type = error.get("type", "unknown_error")
    message = error.get("message", "Unknown error")
    upgrade_url = error.get("upgrade_url")
    reset = error.get("reset")

    kwargs: Dict[str, Any] = dict(
        status_code=response.status_code,
        error_type=error_type,
        message=message,
        upgrade_url=upgrade_url,
        reset=reset,
        raw=body,
    )

    if response.status_code == 429 and error_type == "insufficient_credits":
        error_cls: Any = InsufficientCreditsError
    else:
        error_cls = {
            401: AuthenticationError,
            403: ForbiddenError,
            404: NotFoundError,
            429: RateLimitError,
            503: DataUnavailableError,
        }.get(response.status_code, TickerDBError)

    raise error_cls(**kwargs)


def build_envelope(response: httpx.Response) -> Dict[str, Any]:
    """Build the ``{"data", "rate_limits"}`` envelope returned by every method."""
    return {
        "data": response.json(),
        "rate_limits": parse_rate_limits(response.headers),
    }
