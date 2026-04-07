"""Synchronous TickerDB client."""

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


class SearchQuery:
    """Fluent query builder for the search endpoint.

    Usage::

        results = client.query() \\
            .eq("momentum_rsi_zone", "oversold") \\
            .eq("sector", "Technology") \\
            .select("ticker", "sector", "momentum_rsi_zone") \\
            .sort("extremes_condition_percentile", "asc") \\
            .limit(10) \\
            .execute()
    """

    def __init__(self, client: "TickerDB") -> None:
        self._client = client
        self._filters: list = []
        self._fields: Optional[List[str]] = None
        self._sort_by: Optional[str] = None
        self._sort_direction: Optional[str] = None
        self._limit: Optional[int] = None
        self._offset: Optional[int] = None
        self._timeframe: Optional[str] = None

    def eq(self, field: str, value: Any) -> "SearchQuery":
        self._filters.append({"field": field, "op": "eq", "value": value})
        return self

    def neq(self, field: str, value: Any) -> "SearchQuery":
        self._filters.append({"field": field, "op": "neq", "value": value})
        return self

    def in_(self, field: str, values: list) -> "SearchQuery":
        self._filters.append({"field": field, "op": "in", "value": values})
        return self

    def gt(self, field: str, value: Any) -> "SearchQuery":
        self._filters.append({"field": field, "op": "gt", "value": value})
        return self

    def gte(self, field: str, value: Any) -> "SearchQuery":
        self._filters.append({"field": field, "op": "gte", "value": value})
        return self

    def lt(self, field: str, value: Any) -> "SearchQuery":
        self._filters.append({"field": field, "op": "lt", "value": value})
        return self

    def lte(self, field: str, value: Any) -> "SearchQuery":
        self._filters.append({"field": field, "op": "lte", "value": value})
        return self

    def select(self, *fields: str) -> "SearchQuery":
        self._fields = list(fields)
        return self

    def sort(self, field: str, direction: str = "desc") -> "SearchQuery":
        self._sort_by = field
        self._sort_direction = direction
        return self

    def limit(self, n: int) -> "SearchQuery":
        self._limit = n
        return self

    def offset(self, n: int) -> "SearchQuery":
        self._offset = n
        return self

    def timeframe(self, tf: str) -> "SearchQuery":
        self._timeframe = tf
        return self

    def execute(self) -> Dict[str, Any]:
        """Execute the built query and return results."""
        return self._client.search(
            filters=self._filters,
            fields=self._fields,
            sort_by=self._sort_by,
            sort_direction=self._sort_direction,
            limit=self._limit,
            offset=self._offset,
            timeframe=self._timeframe,
        )


class TickerDB:
    """Synchronous client for the TickerDB financial data API.

    Args:
        api_key: Your TickerDB bearer token.
        base_url: Override the default API base URL.
        timeout: Request timeout in seconds (default 30).
        **httpx_kwargs: Additional keyword arguments forwarded to ``httpx.Client``.

    Usage::

        from tickerdb import TickerDB

        client = TickerDB("your_api_key")
        result = client.summary("AAPL")
        print(result["data"])
        print(result["rate_limits"])
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = _DEFAULT_BASE_URL,
        timeout: float = _DEFAULT_TIMEOUT,
        **httpx_kwargs: Any,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = httpx.Client(
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

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send a request and return parsed data + rate limits."""
        url = f"{self._base_url}{path}"

        # Strip None values from params
        if params:
            params = {k: v for k, v in params.items() if v is not None}

        response = self._client.request(method, url, params=params, json=json)
        _raise_for_status(response)

        data = response.json()
        rate_limits = _parse_rate_limits(response.headers)

        return {"data": data, "rate_limits": rate_limits}

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    def summary(
        self,
        ticker: str,
        *,
        timeframe: Optional[str] = None,
        date: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        field: Optional[str] = None,
        band: Optional[str] = None,
        limit: Optional[int] = None,
        before: Optional[str] = None,
        after: Optional[str] = None,
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
            field: Band field name for event queries (e.g. ``"rsi_zone"``).
            band: Filter to a specific band value (e.g. ``"deep_oversold"``).
            limit: Max event results (1-100). Only used with ``field``.
            before: Return events before this date (``YYYY-MM-DD``).
            after: Return events after this date (``YYYY-MM-DD``).
            context_ticker: Cross-asset correlation ticker (e.g. ``"SPY"``).
            context_field: Band field on context ticker.
            context_band: Required band on context ticker.

        Returns:
            Dict with ``data`` and ``rate_limits`` keys.
        """
        return self._request(
            "GET",
            f"/summary/{ticker}",
            params={
                "timeframe": timeframe,
                "date": date,
                "start": start,
                "end": end,
                "field": field,
                "band": band,
                "limit": limit,
                "before": before,
                "after": after,
                "context_ticker": context_ticker,
                "context_field": context_field,
                "context_band": context_band,
            },
        )

    def search(
        self,
        *,
        filters: Optional[Dict[str, Any]] = None,
        timeframe: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        fields: Optional[List[str]] = None,
        sort_by: Optional[str] = None,
        sort_direction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Search for assets matching filter criteria.

        Args:
            filters: Dict of filter criteria.
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
        return self._request("GET", "/search", params=params)

    def query(self) -> SearchQuery:
        """Create a fluent query builder for the search endpoint.

        Usage::

            results = client.query() \\
                .eq("momentum_rsi_zone", "oversold") \\
                .eq("sector", "Technology") \\
                .select("ticker", "sector", "momentum_rsi_zone") \\
                .sort("extremes_condition_percentile", "asc") \\
                .limit(10) \\
                .execute()

        Returns:
            A :class:`SearchQuery` builder instance.
        """
        return SearchQuery(self)

    def schema(self) -> Dict[str, Any]:
        """Get the schema of available fields and their valid band values.

        Returns:
            Dict with ``data`` and ``rate_limits`` keys.
        """
        return self._request("GET", "/schema/fields")

    def watchlist(
        self,
        tickers: List[str],
        *,
        timeframe: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get watchlist data for multiple tickers.

        Args:
            tickers: List of ticker symbols.
            timeframe: ``"daily"`` or ``"weekly"``.

        Returns:
            Dict with ``data`` and ``rate_limits`` keys.
        """
        body: Dict[str, Any] = {"tickers": tickers}
        if timeframe is not None:
            body["timeframe"] = timeframe
        return self._request("POST", "/watchlist", json=body)

    def watchlist_changes(
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
        return self._request("GET", "/watchlist/changes", params=params)

    # ------------------------------------------------------------------
    # Webhook management
    # ------------------------------------------------------------------

    def list_webhooks(self) -> Dict[str, Any]:
        """List all webhooks for the current account.

        Returns:
            Dict with ``data`` and ``rate_limits`` keys.
        """
        return self._request("GET", "/webhooks")

    def create_webhook(
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
        return self._request("POST", "/webhooks", json=body)

    def update_webhook(
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
        return self._request("PUT", "/webhooks", json=body)

    def delete_webhook(self, id: str) -> Dict[str, Any]:
        """Delete a webhook.

        Args:
            id: The webhook ID to delete.

        Returns:
            Dict with ``data`` and ``rate_limits`` keys.
        """
        return self._request("DELETE", "/webhooks", json={"id": id})

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self) -> "TickerDB":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
