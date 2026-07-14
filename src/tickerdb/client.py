"""Synchronous TickerDB client."""

from typing import Any, Dict, List, Optional

import httpx

from . import _endpoints as endpoints
from ._transport import (
    DEFAULT_BASE_URL,
    DEFAULT_TIMEOUT,
    RequestSpec,
    build_envelope,
    clean_params,
    default_headers,
    raise_for_status,
)
from .query import BaseSearchQuery


class SearchQuery(BaseSearchQuery):
    """Synchronous fluent query builder for the search endpoint.

    See :class:`tickerdb.query.BaseSearchQuery` for the builder methods.
    """

    def execute(self) -> Dict[str, Any]:
        """Execute the built query and return results."""
        return self._client.search(**self._search_kwargs())


class TickerDB:
    """Synchronous client for the TickerDB financial data API.

    Args:
        api_key: Your TickerDB bearer token.
        base_url: Override the default API base URL.
        timeout: Request timeout in seconds (default 30).
        **httpx_kwargs: Additional keyword arguments forwarded to ``httpx.Client``.

    Usage::

        from tickerdb import TickerDB

        client = TickerDB("tdb_your_api_key")
        result = client.summary("AAPL")
        print(result["data"])
        print(result["rate_limits"])
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        **httpx_kwargs: Any,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            headers=default_headers(api_key),
            timeout=timeout,
            **httpx_kwargs,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _send(self, spec: RequestSpec) -> Dict[str, Any]:
        """Execute a request spec and return the response envelope."""
        response = self._client.request(
            spec.method,
            f"{self._base_url}{spec.path}",
            params=clean_params(spec.params),
            json=spec.json,
        )
        raise_for_status(response)
        return build_envelope(response)

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
                ``"trend.direction"``, ``"momentum.rsi_zone"``, or
                ``"fundamentals.free_cash_flow"``.
            meta: Snapshot and history modes only. Set ``True`` to include
                sibling ``_meta`` / ``status_meta`` stability objects.
                Explicit ``*_meta`` field paths still work without this flag.
            sample: Date range mode only. Use ``"even"`` to evenly sample
                snapshots across the full ``start``/``end`` span.
            field: Band field name for event queries (e.g.
                ``"momentum_rsi_zone"``, ``"pattern_bull_flag"``,
                ``"pattern_ascending_triangle"``, or
                ``"trend_distance_ma50"``, or
                ``"fundamentals_free_cash_flow"``).
            band: Filter to a specific band value (e.g. ``"deep_oversold"``).
                MA distance event fields also support grouped aliases
                ``"above"`` and ``"below"``.
            limit: For event mode, max results (1-50), returned newest-first
                by default. For ``sample="even"``
                date ranges, requested sampled rows capped by plan.
            offset: Pagination offset for history/sample date-range modes.
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
        return self._send(endpoints.summary(
            ticker,
            timeframe=timeframe,
            date=date,
            start=start,
            end=end,
            fields=fields,
            meta=meta,
            sample=sample,
            field=field,
            band=band,
            limit=limit,
            offset=offset,
            before=before,
            after=after,
            stats=stats,
            context_ticker=context_ticker,
            context_field=context_field,
            context_band=context_band,
        ))

    def search(
        self,
        *,
        filters: Optional[List[Dict[str, Any]]] = None,
        timeframe: Optional[str] = None,
        date: Optional[str] = None,
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
            date: Point-in-time snapshot date (``YYYY-MM-DD``) to search
                against. History depth is capped by your plan.
            limit: Max results to return.
            offset: Pagination offset.
            fields: Column names to return (e.g.
                ``["ticker", "sector", "momentum_rsi_zone"]``); ``ticker`` is
                always included. Use ``["*"]`` for every field, or omit for a
                sensible default set. See ``/v1/schema/fields`` (or
                :meth:`schema`) for the full catalogue, including raw MA values
                (``ma8``-``ma200``), per-MA slopes, and
                ``fundamentals_free_cash_flow``.
            sort_by: Column name to sort results by. Must be a valid field
                from the schema.
            sort_direction: ``"asc"`` or ``"desc"`` (default ``"desc"``).

        Returns:
            Dict with ``data`` and ``rate_limits`` keys.
        """
        return self._send(endpoints.search(
            filters=filters,
            timeframe=timeframe,
            date=date,
            limit=limit,
            offset=offset,
            fields=fields,
            sort_by=sort_by,
            sort_direction=sort_direction,
        ))

    def query(self) -> SearchQuery:
        """Create a fluent query builder for the search endpoint.

        See :class:`SearchQuery` (and its base
        :class:`tickerdb.query.BaseSearchQuery`) for the chainable methods and
        a usage example.

        Returns:
            A :class:`SearchQuery` builder instance.
        """
        return SearchQuery(self)

    def schema(self) -> Dict[str, Any]:
        """Get the schema of available fields and their valid band values.

        Returns:
            Dict with ``data`` and ``rate_limits`` keys.
        """
        return self._send(endpoints.schema())

    def account(self) -> Dict[str, Any]:
        """Get the authenticated account's tier, limits, usage, and credits.

        This is a metadata call and does **not** consume your monthly request
        quota, so it is safe to poll before running a batch job.

        Returns:
            Dict with ``data`` and ``rate_limits`` keys. ``data`` contains
            ``tier``, ``tier_full``, ``email``, ``limits`` (plan caps),
            ``usage`` (``monthly_requests_used``, ``monthly_requests_remaining``,
            ``credit_balance``), ``scheduled_tier``, and ``scheduled_change_at``.
        """
        return self._send(endpoints.account())

    def ohlcv(
        self,
        ticker: str,
        *,
        start: Optional[str] = None,
        end: Optional[str] = None,
        cursor: Optional[str] = None,
        order: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get daily OHLCV bars for a ticker.

        Bars are split/dividend-adjusted for equities and unadjusted for
        crypto. History depth is capped by your plan (``history_days``). This
        endpoint is **credit-metered**: 100 bars per credit (minimum 1). A
        request that would exceed your credit balance raises
        :class:`~tickerdb.InsufficientCreditsError`.

        Results are cursor-paginated. Follow ``next_cursor`` while
        ``has_more`` is true, or use :meth:`iter_ohlcv` to stream every bar.

        Args:
            ticker: Asset ticker symbol (e.g. ``"AAPL"``).
            start: Range start date (``YYYY-MM-DD``).
            end: Range end date (``YYYY-MM-DD``).
            cursor: Pagination cursor (a date) from a prior ``next_cursor``.
            order: ``"asc"`` or ``"desc"`` (default ``"desc"``).
            limit: Bars per page (1-1000, default 100).

        Returns:
            Dict with ``data`` and ``rate_limits`` keys.
        """
        return self._send(endpoints.ohlcv(
            ticker, start=start, end=end, cursor=cursor, order=order, limit=limit,
        ))

    def iter_ohlcv(
        self,
        ticker: str,
        *,
        start: Optional[str] = None,
        end: Optional[str] = None,
        order: Optional[str] = None,
        page_size: Optional[int] = None,
    ):
        """Yield OHLCV bars across all pages, auto-following the cursor.

        Each item is a single bar dict (``date``, ``open``, ``high``, ``low``,
        ``close``, ``volume``). Note that each page is a separate credit-metered
        request.

        Args:
            ticker: Asset ticker symbol (e.g. ``"AAPL"``).
            start: Range start date (``YYYY-MM-DD``).
            end: Range end date (``YYYY-MM-DD``).
            order: ``"asc"`` or ``"desc"`` (default ``"desc"``).
            page_size: Bars per underlying request (1-1000, default 100).

        Yields:
            Individual OHLCV bar dicts.
        """
        cursor: Optional[str] = None
        while True:
            data = self.ohlcv(
                ticker,
                start=start,
                end=end,
                cursor=cursor,
                order=order,
                limit=page_size,
            )["data"]
            for bar in data.get("bars", []):
                yield bar
            cursor = data.get("next_cursor")
            if not data.get("has_more") or not cursor:
                break

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
