"""Unit tests for the transport helpers (error mapping, rate limits, envelope)."""

import httpx
import pytest

from tickerdb import (
    AuthenticationError,
    DataUnavailableError,
    ForbiddenError,
    InsufficientCreditsError,
    NotFoundError,
    RateLimitError,
    TickerDBError,
)
from tickerdb._transport import (
    build_envelope,
    clean_params,
    parse_rate_limits,
    raise_for_status,
)


def test_clean_params_drops_none():
    assert clean_params({"a": 1, "b": None, "c": "x"}) == {"a": 1, "c": "x"}
    assert clean_params(None) is None
    assert clean_params({}) == {}


def test_parse_rate_limits_reads_headers():
    headers = httpx.Headers(
        {"X-Request-Limit": "1000", "X-Requests-Remaining": "994", "X-Request-Reset": "later"}
    )
    limits = parse_rate_limits(headers)
    assert limits["request_limit"] == 1000
    assert limits["requests_remaining"] == 994
    assert limits["request_reset"] == "later"
    assert limits["hourly_request_limit"] is None


def test_build_envelope():
    resp = httpx.Response(200, json={"x": 1}, headers={"X-Requests-Remaining": "5"})
    env = build_envelope(resp)
    assert env["data"] == {"x": 1}
    assert env["rate_limits"]["requests_remaining"] == 5


def test_raise_for_status_ok_is_noop():
    raise_for_status(httpx.Response(200, json={}))  # no raise


@pytest.mark.parametrize(
    "status,cls",
    [
        (401, AuthenticationError),
        (403, ForbiddenError),
        (404, NotFoundError),
        (429, RateLimitError),
        (503, DataUnavailableError),
        (400, TickerDBError),
    ],
)
def test_raise_for_status_maps_status_codes(status, cls):
    resp = httpx.Response(status, json={"error": {"type": "x", "message": "m"}})
    with pytest.raises(cls) as exc:
        raise_for_status(resp)
    assert exc.value.status_code == status


def test_insufficient_credits_routing_and_attrs():
    resp = httpx.Response(
        429,
        json={
            "error": {
                "type": "insufficient_credits",
                "message": "need more",
                "credits_required": 5,
                "credits_remaining": 2,
            }
        },
    )
    with pytest.raises(InsufficientCreditsError) as exc:
        raise_for_status(resp)
    assert isinstance(exc.value, RateLimitError)  # still catchable as RateLimitError
    assert exc.value.credits_required == 5
    assert exc.value.credits_remaining == 2


def test_non_json_error_body():
    resp = httpx.Response(500, text="boom")
    with pytest.raises(TickerDBError) as exc:
        raise_for_status(resp)
    assert exc.value.error_type == "unknown_error"
    assert exc.value.status_code == 500
