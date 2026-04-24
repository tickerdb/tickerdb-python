"""Asynchronous TickerDB client."""

from typing import Any, Dict, List, Optional

import httpx

from .exceptions import (
    AuthenticationError,
    DataUnavailableError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    TickerDBError,
)
from .types import RateLimits

_DEFAULT_BASE_URL = "https://api.tickerdb.com/v1"
_DEFAULT_TIMEOUT = 30.0


def _parse_rate_limits(headers: httpx.Headers) -> RateLimits:
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


def _raise_for_status(response: httpx.Response) -> None:
    """Raise a typed TickerDBError if the response indicates an error."""
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

    error_cls = {
        401: AuthenticationError,
        403: ForbiddenError,
        404: NotFoundError,
        429: RateLimitError,
        503: DataUnavailableError,
    }.get(response.status_code, TickerDBError)

    raise error_cls(**kwargs)


class AsyncSearchQuery:
    """Fluent query builder for the async search endpoint.

    Usage::

        results = await client.query() \\
            .eq("trend_distance_ma50", "slightly_above") \\
            .eq("sector", "Technology") \\
            .select("ticker", "sector", "trend_distance_ma50") \\
            .sort("extremes_condition_percentile", "asc") \\
            .limit(10) \\
            .execute()
    """

    def __init__(self, client: "AsyncTickerDB") -> None:
        self._client = client
        self._filters: list = []
        self._fields: Optional[List[str]] = None
        self._sort_by: Optional[str] = None
        self._sort_direction: Optional[str] = None
        self._limit: Optional[int] = None
        self._offset: Optional[int] = None
        self._timeframe: Optional[str] = None

    def eq(self, field: str, value: Any) -> "AsyncSearchQuery":
        self._filters.append({"field": field, "op": "eq", "value": value})
        return self

    def neq(self, field: str, value: Any) -> "AsyncSearchQuery":
        self._filters.append({"field": field, "op": "neq", "value": value})
        return self

    def in_(self, field: str, values: list) -> "AsyncSearchQuery":
        self._filters.append({"field": field, "op": "in", "value": values})
        return self

    def gt(self, field: str, value: Any) -> "AsyncSearchQuery":
        self._filters.append({"field": field, "op": "gt", "value": value})
        return self

    def gte(self, field: str, value: Any) -> "AsyncSearchQuery":
        self._filters.append({"field": field, "op": "gte", "value": value})
        return self

    def lt(self, field: str, value: Any) -> "AsyncSearchQuery":
        self._filters.append({"field": field, "op": "lt", "value": value})
        return self

    def lte(self, field: str, value: Any) -> "AsyncSearchQuery":
        self._filters.append({"field": field, "op": "lte", "value": value})
        return self

    def select(self, *fields: str) -> "AsyncSearchQuery":
        self._fields = list(fields)
        return self

    def sort(self, field: str, direction: str = "desc") -> "AsyncSearchQuery":
        self._sort_by = field
        self._sort_direction = direction
        return self

    def limit(self, n: int) -> "AsyncSearchQuery":
        self._limit = n
        return self

    def offset(self, n: int) -> "AsyncSearchQuery":
        self._offset = n
        return self

    def timeframe(self, tf: str) -> "AsyncSearchQuery":
        self._timeframe = tf
        return self

    async def execute(self) -> Dict[str, Any]:
        """Execute the built query and return results."""
        return await self._client.search(
            filters=self._filters,
            fields=self._fields,
            sort_by=self._sort_by,
            sort_direction=self._sort_direction,
            limit=self._limit,
            offset=self._offset,
            timeframe=self._timeframe,
        )


class AsyncTickerDB:
    """Asynchronous client for the TickerDB financial data API.

    Args:
        api_key: Your TickerDB bearer token.
        base_url: Override the default API base URL.
        timeout: Request timeout in seconds (default 30).
        **httpx_kwargs: Additional keyword arguments forwarded to ``httpx.AsyncClient``.

    Usage::

        import asyncio
        from tickerdb import AsyncTickerDB

        async def main():
            async with AsyncTickerDB("tdb_your_api_key") as client:
                result = await client.summary("AAPL")
                print(result["data"])

        asyncio.run(main())
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = _DEFAULT_BASE_URL,
        timeout: float = _DEFAULT_TIMEOUT,
        **httpx_kwargs: Any,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
                "User-Agent": "tickerdb-python/0.1.0",
            },
            timeout=timeout,
            **httpx_kwargs,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send a request and return parsed data + rate limits."""
        url = f"{self._base_url}{path}"

        if params:
            params = {k: v for k, v in params.items() if v is not None}

        response = await self._client.request(method, url, params=params, json=json)
        _raise_for_status(response)

        data = response.json()
        rate_limits = _parse_rate_limits(response.headers)

        return {"data": data, "rate_limits": rate_limits}

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    async def summary(
        self,
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
        before: Optional[str] = None,
        after: Optional[str] = None,
        stats: Optional[bool] = None,
        context_ticker: Optional[str] = None,
        context_field: Optional[str] = None,
        context_band: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get a summary for a single ticker.

        Supports 4 modes depending on which parameters are provided:

        - **Snapshot** (default): Current categorical state.
        - **Historical snapshot**: Pass ``date`` for a point-in-time snapshot.
        - **Historical series**: Pass ``start``/``end`` for a date range.
        - **Events**: Pass ``field`` (and optionally ``band``) for band
          transition history with aftermath data.

        Args:
            ticker: Asset ticker symbol (e.g. ``"AAPL"``).
            timeframe: ``"daily"`` or ``"weekly"`` (default ``"daily"``).
            date: ISO 8601 date string (``YYYY-MM-DD``) for point-in-time.
            start: Range start date (``YYYY-MM-DD``). Use with ``end``.
            end: Range end date (``YYYY-MM-DD``). Use with ``start``.
            fields: Optional list of summary fields to return. Supports
                sections like ``"trend"`` and dotted paths like
                ``"trend.direction"`` or ``"momentum.rsi_zone"``.
            meta: Snapshot and history modes only. Set ``True`` to include
                sibling ``_meta`` / ``status_meta`` stability objects.
                Explicit ``*_meta`` field paths still work without this flag.
            sample: Date range mode only. Use ``"even"`` to evenly sample
                snapshots across the full ``start``/``end`` span.
            field: Band field name for event queries (e.g.
                ``"momentum_rsi_zone"`` or ``"trend_distance_ma50"``).
            band: Filter to a specific band value (e.g. ``"deep_oversold"``).
                MA distance event fields also support grouped aliases
                ``"above"`` and ``"below"``.
            limit: For event mode, max results (1-50), returned newest-first
                by default. For ``sample="even"``
                date ranges, requested sampled rows capped by plan.
            before: Return events before this date (``YYYY-MM-DD``).
            after: Return events after this date (``YYYY-MM-DD``).
            stats: Event mode only. Set ``True`` to return aggregate stats
                instead of raw event rows.
            context_ticker: Cross-asset correlation ticker (e.g. ``"SPY"``).
            context_field: Band field on context ticker (e.g.
                ``"trend_direction"`` or ``"trend_distance_ma50"``).
            context_band: Required band on context ticker.

        Returns:
            Dict with ``data`` and ``rate_limits`` keys.
        """
        import json as _json

        params: Dict[str, Any] = {
            "timeframe": timeframe,
            "date": date,
            "start": start,
            "end": end,
            "sample": sample,
            "field": field,
            "band": band,
            "limit": limit,
            "before": before,
            "after": after,
            "stats": "true" if stats else None,
            "context_ticker": context_ticker,
            "context_field": context_field,
            "context_band": context_band,
        }
        if fields is not None:
            params["fields"] = _json.dumps(fields)
        if meta is not None:
            params["meta"] = "true" if meta else "false"

        return await self._request(
            "GET",
            f"/summary/{ticker}",
            params=params,
        )

    async def search(
        self,
        *,
        filters: Optional[List[Dict[str, Any]]] = None,
        timeframe: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        fields: Optional[List[str]] = None,
        sort_by: Optional[str] = None,
        sort_direction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Search for assets matching filter criteria.

        Args:
            filters: List of ``{"field", "op", "value"}`` filter objects.
                Example: ``[{"field": "momentum_rsi_zone", "op": "eq", "value": "oversold"}]``.
                Canonical field names come from ``/v1/schema/fields`` and use
                flat snake_case.
            timeframe: ``"daily"`` or ``"weekly"``.
            limit: Max results to return.
            offset: Pagination offset.
            fields: List of column names to return (e.g.
                ``["ticker", "sector", "momentum_rsi_zone"]``).
                Use ``["*"]`` for all 120+ fields. Default if omitted: ticker,
                asset_class, sector, performance, trend_direction, momentum_rsi_zone,
                extremes_condition, extremes_condition_rarity, volatility_regime,
                volume_ratio_band, fundamentals_valuation_zone, range_position.
                ``ticker`` is always included.
            sort_by: Column name to sort results by. Must be a valid field
                from the schema.
            sort_direction: ``"asc"`` or ``"desc"`` (default ``"desc"``).

        Returns:
            Dict with ``data`` and ``rate_limits`` keys.
        """
        import json as _json

        params: Dict[str, Any] = {
            "timeframe": timeframe,
            "limit": limit,
            "offset": offset,
            "sort_by": sort_by,
            "sort_direction": sort_direction,
        }
        if filters is not None:
            params["filters"] = _json.dumps(filters)
        if fields is not None:
            params["fields"] = _json.dumps(fields)
        return await self._request("GET", "/search", params=params)

    def query(self) -> AsyncSearchQuery:
        """Create a fluent query builder for the search endpoint.

        Usage::

            results = await client.query() \\
                .eq("trend_distance_ma50", "slightly_above") \\
                .eq("sector", "Technology") \\
                .select("ticker", "sector", "trend_distance_ma50") \\
                .sort("extremes_condition_percentile", "asc") \\
                .limit(10) \\
                .execute()

        Returns:
            An :class:`AsyncSearchQuery` builder instance.
        """
        return AsyncSearchQuery(self)

    async def schema(self) -> Dict[str, Any]:
        """Get the schema of available fields and their valid band values.

        Returns:
            Dict with ``data`` and ``rate_limits`` keys.
        """
        return await self._request("GET", "/schema/fields")

    async def watchlist(
        self,
        *,
        date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get the saved watchlist snapshot for the authenticated account.

        Args:
            date: Optional point-in-time snapshot date (``YYYY-MM-DD``).

        Returns:
            Dict with ``data`` and ``rate_limits`` keys.
        """
        params: Dict[str, str] = {}
        if date is not None:
            params["date"] = date
        return await self._request("GET", "/watchlist", params=params)

    async def add_to_watchlist(
        self,
        tickers: List[str],
    ) -> Dict[str, Any]:
        """Add ticker symbols to the saved watchlist.

        Args:
            tickers: List of ticker symbols to save.

        Returns:
            Dict with ``data`` and ``rate_limits`` keys.
        """
        return await self._request(
            "POST",
            "/watchlist",
            json={"tickers": [str(t).strip().upper() for t in tickers]},
        )

    async def remove_from_watchlist(
        self,
        tickers: List[str],
    ) -> Dict[str, Any]:
        """Remove ticker symbols from the saved watchlist.

        Args:
            tickers: List of ticker symbols to remove.

        Returns:
            Dict with ``data`` and ``rate_limits`` keys.
        """
        return await self._request(
            "DELETE",
            "/watchlist",
            json={"tickers": [str(t).strip().upper() for t in tickers]},
        )

    async def watchlist_changes(
        self,
        *,
        timeframe: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get field-level state changes for your saved watchlist tickers.

        Returns structured diffs showing what changed since the last pipeline
        run (day-over-day for daily, week-over-week for weekly). Available on
        all tiers.

        Args:
            timeframe: ``"daily"`` or ``"weekly"``.

        Returns:
            Dict with ``data`` and ``rate_limits`` keys.
        """
        params: Dict[str, str] = {}
        if timeframe is not None:
            params["timeframe"] = timeframe
        return await self._request("GET", "/watchlist/changes", params=params)

    # ------------------------------------------------------------------
    # Webhook management
    # ------------------------------------------------------------------

    async def list_webhooks(self) -> Dict[str, Any]:
        """List all webhooks for the current account.

        Returns:
            Dict with ``data`` and ``rate_limits`` keys.
        """
        return await self._request("GET", "/webhooks")

    async def create_webhook(
        self,
        url: str,
        events: Optional[Dict[str, bool]] = None,
    ) -> Dict[str, Any]:
        """Create a new webhook.

        Args:
            url: The URL to receive webhook events.
            events: Dict mapping event names to enabled booleans.

        Returns:
            Dict with ``data`` and ``rate_limits`` keys.
        """
        body: Dict[str, Any] = {"url": url}
        if events is not None:
            body["events"] = events
        return await self._request("POST", "/webhooks", json=body)

    async def update_webhook(
        self,
        id: str,
        *,
        url: Optional[str] = None,
        events: Optional[Dict[str, bool]] = None,
        active: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Update an existing webhook.

        Args:
            id: The webhook ID.
            url: New URL for the webhook.
            events: Updated event subscriptions.
            active: Whether the webhook is active.

        Returns:
            Dict with ``data`` and ``rate_limits`` keys.
        """
        body: Dict[str, Any] = {"id": id}
        if url is not None:
            body["url"] = url
        if events is not None:
            body["events"] = events
        if active is not None:
            body["active"] = active
        return await self._request("PUT", "/webhooks", json=body)

    async def delete_webhook(self, id: str) -> Dict[str, Any]:
        """Delete a webhook.

        Args:
            id: The webhook ID to delete.

        Returns:
            Dict with ``data`` and ``rate_limits`` keys.
        """
        return await self._request("DELETE", "/webhooks", json={"id": id})

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncTickerDB":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
