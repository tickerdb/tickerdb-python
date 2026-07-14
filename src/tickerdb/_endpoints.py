"""Pure request builders for the TickerDB API.

Each function assembles the path, query params, and/or JSON body for one
endpoint and returns a :class:`RequestSpec`. They perform no I/O and are shared
by both the sync and async clients, so request shaping lives in exactly one
place. ``None`` query params are dropped later by the transport layer.
"""

import json
from typing import Any, Dict, List, Optional

from ._transport import RequestSpec


def _normalize_tickers(tickers: List[str]) -> List[str]:
    """Uppercase and trim ticker symbols for watchlist mutations."""
    return [str(t).strip().upper() for t in tickers]


# ---------------------------------------------------------------------------
# Summary / search / schema
# ---------------------------------------------------------------------------


def summary(
    ticker: str,
    *,
    timeframe: Optional[str] = None,
    date: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    fields: Optional[List[str]] = None,
    meta: Optional[bool] = None,
    sample: Optional[str] = None,
    field: Optional[str] = None,
    band: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    stats: Optional[bool] = None,
    context_ticker: Optional[str] = None,
    context_field: Optional[str] = None,
    context_band: Optional[str] = None,
) -> RequestSpec:
    params: Dict[str, Any] = {
        "timeframe": timeframe,
        "date": date,
        "start": start,
        "end": end,
        "sample": sample,
        "field": field,
        "band": band,
        "limit": limit,
        "offset": offset,
        "before": before,
        "after": after,
        "stats": "true" if stats else None,
        "context_ticker": context_ticker,
        "context_field": context_field,
        "context_band": context_band,
    }
    if fields is not None:
        params["fields"] = json.dumps(fields)
    if meta is not None:
        params["meta"] = "true" if meta else "false"
    return RequestSpec("GET", f"/summary/{ticker}", params=params)


def search(
    *,
    filters: Optional[List[Dict[str, Any]]] = None,
    timeframe: Optional[str] = None,
    date: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    fields: Optional[List[str]] = None,
    sort_by: Optional[str] = None,
    sort_direction: Optional[str] = None,
) -> RequestSpec:
    params: Dict[str, Any] = {
        "timeframe": timeframe,
        "date": date,
        "limit": limit,
        "offset": offset,
        "sort_by": sort_by,
        "sort_direction": sort_direction,
    }
    if filters is not None:
        params["filters"] = json.dumps(filters)
    if fields is not None:
        params["fields"] = json.dumps(fields)
    return RequestSpec("GET", "/search", params=params)


def schema() -> RequestSpec:
    return RequestSpec("GET", "/schema/fields")


# ---------------------------------------------------------------------------
# Account / OHLCV
# ---------------------------------------------------------------------------


def account() -> RequestSpec:
    return RequestSpec("GET", "/account")


def ohlcv(
    ticker: str,
    *,
    start: Optional[str] = None,
    end: Optional[str] = None,
    cursor: Optional[str] = None,
    order: Optional[str] = None,
    limit: Optional[int] = None,
) -> RequestSpec:
    return RequestSpec(
        "GET",
        f"/ohlcv/{ticker}",
        params={
            "start": start,
            "end": end,
            "cursor": cursor,
            "order": order,
            "limit": limit,
        },
    )


# ---------------------------------------------------------------------------
# Watchlist
# ---------------------------------------------------------------------------


def watchlist(*, date: Optional[str] = None) -> RequestSpec:
    return RequestSpec("GET", "/watchlist", params={"date": date})


def add_to_watchlist(tickers: List[str]) -> RequestSpec:
    return RequestSpec("POST", "/watchlist", json={"tickers": _normalize_tickers(tickers)})


def remove_from_watchlist(tickers: List[str]) -> RequestSpec:
    return RequestSpec(
        "DELETE", "/watchlist", json={"tickers": _normalize_tickers(tickers)}
    )


def watchlist_changes(*, timeframe: Optional[str] = None) -> RequestSpec:
    return RequestSpec("GET", "/watchlist/changes", params={"timeframe": timeframe})


