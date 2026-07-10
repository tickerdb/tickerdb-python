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


def _screener_body(
    *,
    filters: Optional[List[Dict[str, Any]]] = None,
    name: Optional[str] = None,
    timeframe: Optional[str] = None,
    sort: Optional[Dict[str, Any]] = None,
    limit_count: Optional[int] = None,
) -> Dict[str, Any]:
    """Build the shared screener create/update body, omitting unset fields."""
    body: Dict[str, Any] = {}
    if filters is not None:
        body["filters"] = filters
    if name is not None:
        body["name"] = name
    if timeframe is not None:
        body["timeframe"] = timeframe
    if sort is not None:
        body["sort"] = sort
    if limit_count is not None:
        body["limit_count"] = limit_count
    return body


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


# ---------------------------------------------------------------------------
# Screeners
# ---------------------------------------------------------------------------


def list_screeners() -> RequestSpec:
    return RequestSpec("GET", "/screeners")


def create_screener(
    *,
    filters: List[Dict[str, Any]],
    name: Optional[str] = None,
    timeframe: Optional[str] = None,
    sort: Optional[Dict[str, Any]] = None,
    limit_count: Optional[int] = None,
) -> RequestSpec:
    body = _screener_body(
        filters=filters, name=name, timeframe=timeframe, sort=sort, limit_count=limit_count
    )
    return RequestSpec("POST", "/screeners", json=body)


def update_screener(
    id: str,
    *,
    filters: Optional[List[Dict[str, Any]]] = None,
    name: Optional[str] = None,
    timeframe: Optional[str] = None,
    sort: Optional[Dict[str, Any]] = None,
    limit_count: Optional[int] = None,
) -> RequestSpec:
    body: Dict[str, Any] = {"id": id}
    body.update(
        _screener_body(
            filters=filters, name=name, timeframe=timeframe, sort=sort, limit_count=limit_count
        )
    )
    return RequestSpec("PUT", "/screeners", json=body)


def delete_screener(id: str, *, kind: str = "custom") -> RequestSpec:
    return RequestSpec("DELETE", "/screeners", json={"id": id, "kind": kind})


# ---------------------------------------------------------------------------
# Webhooks
# ---------------------------------------------------------------------------


def list_webhooks() -> RequestSpec:
    return RequestSpec("GET", "/webhooks")


def create_webhook(url: str, events: Optional[Dict[str, bool]] = None) -> RequestSpec:
    body: Dict[str, Any] = {"url": url}
    if events is not None:
        body["events"] = events
    return RequestSpec("POST", "/webhooks", json=body)


def update_webhook(
    id: str,
    *,
    url: Optional[str] = None,
    events: Optional[Dict[str, bool]] = None,
    active: Optional[bool] = None,
) -> RequestSpec:
    body: Dict[str, Any] = {"id": id}
    if url is not None:
        body["url"] = url
    if events is not None:
        body["events"] = events
    if active is not None:
        body["active"] = active
    return RequestSpec("PUT", "/webhooks", json=body)


def delete_webhook(id: str) -> RequestSpec:
    return RequestSpec("DELETE", "/webhooks", json={"id": id})


def webhook_deliveries(
    *, webhook_id: Optional[str] = None, limit: Optional[int] = None
) -> RequestSpec:
    return RequestSpec(
        "GET",
        "/webhooks/deliveries",
        params={"webhook_id": webhook_id, "limit": limit},
    )


# ---------------------------------------------------------------------------
# Teams
# ---------------------------------------------------------------------------


def get_teams() -> RequestSpec:
    return RequestSpec("GET", "/team")


def team_action(action: str, **body: Any) -> RequestSpec:
    """Build a POST /team action body, dropping ``None`` values."""
    payload: Dict[str, Any] = {"action": action}
    payload.update({k: v for k, v in body.items() if v is not None})
    return RequestSpec("POST", "/team", json=payload)
