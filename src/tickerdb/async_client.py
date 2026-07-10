"""Asynchronous TickerDB client."""

from typing import Any, Dict, List, Optional

import httpx

from ._transport import (
    DEFAULT_BASE_URL,
    DEFAULT_TIMEOUT,
    build_envelope,
    clean_params,
    default_headers,
    raise_for_status,
)


class AsyncSearchQuery:
    """Fluent query builder for the async search endpoint.

    Usage::

        results = await client.query() \\
            .eq("trend_distance_ma50", "proximity_above") \\
            .eq("sector", "Technology") \\
            .select("ticker", "sector", "trend_distance_ma50", "fundamentals_free_cash_flow") \\
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
        self._date: Optional[str] = None

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

    def date(self, d: str) -> "AsyncSearchQuery":
        self._date = d
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
            date=self._date,
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
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        **httpx_kwargs: Any,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            headers=default_headers(api_key),
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
        response = await self._client.request(
            method, url, params=clean_params(params), json=json
        )
        raise_for_status(response)
        return build_envelope(response)

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
            "offset": offset,
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
            fields: List of column names to return (e.g.
                ``["ticker", "sector", "momentum_rsi_zone"]``).
                Use ``["*"]`` for all 120+ fields. Default if omitted: ticker,
                asset_class, sector, performance, trend_direction, trend_ma20_slope,
                trend_ma_compression_band, trend_ma_crossover_event, momentum_rsi_zone,
                extremes_condition, extremes_condition_rarity, volatility_regime,
                volume_ratio_band, pattern_bull_flag, pattern_bear_flag,
                pattern_ascending_triangle, pattern_descending_triangle,
                pattern_symmetrical_triangle, pattern_rising_wedge,
                pattern_falling_wedge,
                fundamentals_valuation_zone, range_position.
                Request fundamentals_free_cash_flow explicitly for the stock-only
                free cash flow burn/surplus band.
                Request ma8 through ma200 for raw MA values.
                Request trend_ma8_slope through trend_ma200_slope for the full MA
                slope set.
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
            "date": date,
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
                .eq("trend_distance_ma50", "proximity_above") \\
                .eq("sector", "Technology") \\
                .select("ticker", "sector", "trend_distance_ma50", "fundamentals_free_cash_flow") \\
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

    async def account(self) -> Dict[str, Any]:
        """Get the authenticated account's tier, limits, usage, and credits.

        This is a metadata call and does **not** consume your monthly request
        quota, so it is safe to poll before running a batch job.

        Returns:
            Dict with ``data`` and ``rate_limits`` keys. ``data`` contains
            ``tier``, ``tier_full``, ``email``, ``limits`` (plan caps),
            ``usage`` (``monthly_requests_used``, ``monthly_requests_remaining``,
            ``credit_balance``), ``scheduled_tier``, and ``scheduled_change_at``.
        """
        return await self._request("GET", "/account")

    async def ohlcv(
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
        params: Dict[str, Any] = {
            "start": start,
            "end": end,
            "cursor": cursor,
            "order": order,
            "limit": limit,
        }
        return await self._request("GET", f"/ohlcv/{ticker}", params=params)

    async def iter_ohlcv(
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
            result = await self.ohlcv(
                ticker,
                start=start,
                end=end,
                cursor=cursor,
                order=order,
                limit=page_size,
            )
            data = result["data"]
            for bar in data.get("bars", []):
                yield bar
            cursor = data.get("next_cursor")
            if not data.get("has_more") or not cursor:
                break

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
    # Screeners
    # ------------------------------------------------------------------

    async def list_screeners(self) -> Dict[str, Any]:
        """List saved (custom) and built-in (default) screeners.

        Returns:
            Dict with ``data`` and ``rate_limits`` keys. ``data`` contains
            ``defaults``, ``saved``, ``screeners`` (both combined), and
            ``fields`` (the queryable field catalogue).
        """
        return await self._request("GET", "/screeners")

    async def create_screener(
        self,
        *,
        filters: List[Dict[str, Any]],
        name: Optional[str] = None,
        timeframe: Optional[str] = None,
        sort: Optional[Dict[str, Any]] = None,
        limit_count: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Create a saved custom screener.

        Args:
            filters: List of filter objects (up to 12). Value filters use
                ``{"field", "op", "value"}`` with ``op`` in
                ``eq/neq/in/gt/gte/lt/lte/exists``. Change filters use
                ``{"type": "change", "field", "from", "to"}``.
            name: Optional display name (derived from filters if omitted).
            timeframe: ``"daily"`` or ``"weekly"`` (default ``"daily"``).
            sort: Optional ``{"field", "direction"}`` sort object.
            limit_count: Result cap when the screener is run (1-50).

        Returns:
            Dict with ``data`` and ``rate_limits`` keys. ``data.screener`` is
            the created screener. ``return_fields`` are derived server-side
            from the filters and sort.
        """
        body: Dict[str, Any] = {"filters": filters}
        if name is not None:
            body["name"] = name
        if timeframe is not None:
            body["timeframe"] = timeframe
        if sort is not None:
            body["sort"] = sort
        if limit_count is not None:
            body["limit_count"] = limit_count
        return await self._request("POST", "/screeners", json=body)

    async def update_screener(
        self,
        id: str,
        *,
        filters: Optional[List[Dict[str, Any]]] = None,
        name: Optional[str] = None,
        timeframe: Optional[str] = None,
        sort: Optional[Dict[str, Any]] = None,
        limit_count: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Update a saved custom screener.

        Only the provided fields are changed; omitted fields keep their
        current value.

        Args:
            id: The screener ID.
            filters: Replacement filter list (see :meth:`create_screener`).
            name: New display name.
            timeframe: ``"daily"`` or ``"weekly"``.
            sort: Replacement ``{"field", "direction"}`` sort object.
            limit_count: Result cap when the screener is run (1-50).

        Returns:
            Dict with ``data`` and ``rate_limits`` keys.
        """
        body: Dict[str, Any] = {"id": id}
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
        return await self._request("PUT", "/screeners", json=body)

    async def delete_screener(
        self,
        id: str,
        *,
        kind: str = "custom",
    ) -> Dict[str, Any]:
        """Delete a custom screener or hide a built-in default screener.

        Args:
            id: The screener ID.
            kind: ``"custom"`` to delete a saved screener (default), or
                ``"default"`` to hide a built-in screener from your account.

        Returns:
            Dict with ``data`` and ``rate_limits`` keys.
        """
        return await self._request(
            "DELETE", "/screeners", json={"id": id, "kind": kind}
        )

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

    async def webhook_deliveries(
        self,
        *,
        webhook_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get recent webhook delivery attempts (status, retries, errors).

        Args:
            webhook_id: Only return deliveries for this webhook. Omit to
                return deliveries across all of your webhooks.
            limit: Max records to return (default 50, max 200).

        Returns:
            Dict with ``data`` and ``rate_limits`` keys. ``data`` contains
            ``deliveries`` (each with ``status``, ``attempt_count``,
            ``http_status``, ``error``, timestamps, etc.), ``count``, and
            ``limit``.
        """
        params: Dict[str, Any] = {
            "webhook_id": webhook_id,
            "limit": limit,
        }
        return await self._request("GET", "/webhooks/deliveries", params=params)

    # ------------------------------------------------------------------
    # Team management
    # ------------------------------------------------------------------

    async def get_teams(self) -> Dict[str, Any]:
        """List teams you belong to and your pending team invites.

        Available on all tiers (viewing is not gated). Returns:
            Dict with ``data`` and ``rate_limits`` keys. ``data`` contains
            ``teams`` and ``my_pending_invites``.
        """
        return await self._request("GET", "/team")

    async def _team_action(self, action: str, **body: Any) -> Dict[str, Any]:
        """POST an action to the team endpoint, dropping ``None`` values."""
        payload: Dict[str, Any] = {"action": action}
        payload.update({k: v for k, v in body.items() if v is not None})
        return await self._request("POST", "/team", json=payload)

    async def create_team(self, name: str) -> Dict[str, Any]:
        """Create a team (requires a business plan).

        Args:
            name: Team name (1-100 characters).
        """
        return await self._team_action("create", name=name)

    async def invite_member(
        self,
        team_id: str,
        email: str,
        role: str = "member",
    ) -> Dict[str, Any]:
        """Invite a member to a team (owner/admin only, business plan).

        Args:
            team_id: The team ID.
            email: Invitee email address.
            role: ``"member"`` (default) or ``"admin"``.
        """
        return await self._team_action(
            "invite", team_id=team_id, email=email, role=role
        )

    async def remove_member(self, team_id: str, user_id: str) -> Dict[str, Any]:
        """Remove a member from a team (owner/admin only).

        The removed member is downgraded to the Starter tier.

        Args:
            team_id: The team ID.
            user_id: The member's user ID.
        """
        return await self._team_action(
            "remove_member", team_id=team_id, user_id=user_id
        )

    async def cancel_invite(self, team_id: str, invite_id: str) -> Dict[str, Any]:
        """Cancel a pending team invite (owner/admin only).

        Args:
            team_id: The team ID.
            invite_id: The invite ID to cancel.
        """
        return await self._team_action(
            "cancel_invite", team_id=team_id, invite_id=invite_id
        )

    async def resend_invite(self, team_id: str, invite_id: str) -> Dict[str, Any]:
        """Resend a pending invite email and refresh its expiry (owner/admin).

        Args:
            team_id: The team ID.
            invite_id: The invite ID to resend.
        """
        return await self._team_action(
            "resend_invite", team_id=team_id, invite_id=invite_id
        )

    async def promote_member(
        self,
        team_id: str,
        user_id: str,
        role: str,
    ) -> Dict[str, Any]:
        """Change a member's role (owner/admin only).

        Args:
            team_id: The team ID.
            user_id: The member's user ID.
            role: ``"admin"`` or ``"member"``.
        """
        return await self._team_action(
            "promote", team_id=team_id, user_id=user_id, role=role
        )

    async def leave_team(self, team_id: str) -> Dict[str, Any]:
        """Leave a team (owners cannot leave).

        Leaving downgrades your account to the Starter tier.

        Args:
            team_id: The team ID.
        """
        return await self._team_action("leave", team_id=team_id)

    async def rename_team(self, team_id: str, name: str) -> Dict[str, Any]:
        """Rename a team (owner only).

        Args:
            team_id: The team ID.
            name: New team name (1-100 characters).
        """
        return await self._team_action("rename", team_id=team_id, name=name)

    async def set_seats(self, team_id: str, total_seats: int) -> Dict[str, Any]:
        """Set total team seat capacity (owner only, business plan).

        ``total_seats`` is the desired total capacity (included + extra).
        Adjusts the Stripe subscription; adding seats charges a prorated
        amount immediately.

        Args:
            team_id: The team ID.
            total_seats: Desired total seat count.
        """
        return await self._team_action(
            "set_seats", team_id=team_id, total_seats=total_seats
        )

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
