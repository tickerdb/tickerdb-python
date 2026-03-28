"""Asynchronous TickerAPI client."""

from typing import Any, Dict, List, Optional, Union

import httpx

from .exceptions import (
    AuthenticationError,
    DataUnavailableError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    TickerAPIError,
)
from .types import RateLimits

_DEFAULT_BASE_URL = "https://api.tickerapi.ai/v1"
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
    """Raise a typed TickerAPIError if the response indicates an error."""
    if response.status_code < 400:
        return

    try:
        body = response.json()
    except Exception:
        raise TickerAPIError(
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
    }.get(response.status_code, TickerAPIError)

    raise error_cls(**kwargs)


class AsyncTickerAPI:
    """Asynchronous client for the TickerAPI financial data API.

    Args:
        api_key: Your TickerAPI bearer token.
        base_url: Override the default API base URL.
        timeout: Request timeout in seconds (default 30).
        **httpx_kwargs: Additional keyword arguments forwarded to ``httpx.AsyncClient``.

    Usage::

        import asyncio
        from tickerapi import AsyncTickerAPI

        async def main():
            async with AsyncTickerAPI("your_api_key") as client:
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
                "User-Agent": "tickerapi-python/0.1.0",
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
    ) -> Dict[str, Any]:
        """Get a summary for a single ticker.

        Args:
            ticker: Asset ticker symbol (e.g. ``"AAPL"``).
            timeframe: ``"daily"`` or ``"weekly"`` (default ``"daily"``).
            date: ISO 8601 date string (``YYYY-MM-DD``).

        Returns:
            Dict with ``data`` and ``rate_limits`` keys.
        """
        return await self._request(
            "GET",
            f"/summary/{ticker}",
            params={"timeframe": timeframe, "date": date},
        )

    async def compare(
        self,
        tickers: Union[List[str], str],
        *,
        timeframe: Optional[str] = None,
        date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Compare multiple tickers side-by-side.

        Args:
            tickers: List of ticker symbols or a comma-separated string.
            timeframe: ``"daily"`` or ``"weekly"``.
            date: ISO 8601 date string.

        Returns:
            Dict with ``data`` and ``rate_limits`` keys.
        """
        if isinstance(tickers, list):
            tickers = ",".join(tickers)
        return await self._request(
            "GET",
            "/compare",
            params={"tickers": tickers, "timeframe": timeframe, "date": date},
        )

    async def watchlist(
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
        return await self._request("POST", "/watchlist", json=body)

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

    async def assets(self) -> Dict[str, Any]:
        """List all available assets.

        Returns:
            Dict with ``data`` and ``rate_limits`` keys.
        """
        return await self._request("GET", "/assets")

    async def scan_oversold(
        self,
        *,
        timeframe: Optional[str] = None,
        asset_class: Optional[str] = None,
        sector: Optional[str] = None,
        min_severity: Optional[str] = None,
        sort_by: Optional[str] = None,
        limit: Optional[int] = None,
        date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Scan for oversold assets.

        Args:
            timeframe: ``"daily"`` or ``"weekly"``.
            asset_class: ``"stock"``, ``"crypto"``, ``"etf"``, or ``"all"``.
            sector: Filter by sector.
            min_severity: ``"oversold"`` or ``"deep_oversold"``.
            sort_by: ``"severity"``, ``"days_oversold"``, or ``"condition_percentile"``.
            limit: Max results (1-50).
            date: ISO 8601 date string.

        Returns:
            Dict with ``data`` and ``rate_limits`` keys.
        """
        return await self._request(
            "GET",
            "/scan/oversold",
            params={
                "timeframe": timeframe,
                "asset_class": asset_class,
                "sector": sector,
                "min_severity": min_severity,
                "sort_by": sort_by,
                "limit": limit,
                "date": date,
            },
        )

    async def scan_breakouts(
        self,
        *,
        timeframe: Optional[str] = None,
        asset_class: Optional[str] = None,
        sector: Optional[str] = None,
        direction: Optional[str] = None,
        sort_by: Optional[str] = None,
        limit: Optional[int] = None,
        date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Scan for breakout patterns.

        Args:
            timeframe: ``"daily"`` or ``"weekly"``.
            asset_class: ``"stock"``, ``"crypto"``, ``"etf"``, or ``"all"``.
            sector: Filter by sector.
            direction: ``"bullish"``, ``"bearish"``, or ``"all"``.
            sort_by: ``"volume_ratio"``, ``"level_strength"``, or ``"condition_percentile"``.
            limit: Max results (1-50).
            date: ISO 8601 date string.

        Returns:
            Dict with ``data`` and ``rate_limits`` keys.
        """
        return await self._request(
            "GET",
            "/scan/breakouts",
            params={
                "timeframe": timeframe,
                "asset_class": asset_class,
                "sector": sector,
                "direction": direction,
                "sort_by": sort_by,
                "limit": limit,
                "date": date,
            },
        )

    async def scan_unusual_volume(
        self,
        *,
        timeframe: Optional[str] = None,
        asset_class: Optional[str] = None,
        sector: Optional[str] = None,
        min_ratio_band: Optional[str] = None,
        sort_by: Optional[str] = None,
        limit: Optional[int] = None,
        date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Scan for unusual volume activity.

        Args:
            timeframe: ``"daily"`` or ``"weekly"``.
            asset_class: ``"stock"``, ``"crypto"``, ``"etf"``, or ``"all"``.
            sector: Filter by sector.
            min_ratio_band: ``"extremely_low"``, ``"low"``, ``"normal"``,
                ``"elevated"``, ``"high"``, or ``"extremely_high"``.
            sort_by: ``"volume_percentile"``.
            limit: Max results (1-50).
            date: ISO 8601 date string.

        Returns:
            Dict with ``data`` and ``rate_limits`` keys.
        """
        return await self._request(
            "GET",
            "/scan/unusual-volume",
            params={
                "timeframe": timeframe,
                "asset_class": asset_class,
                "sector": sector,
                "min_ratio_band": min_ratio_band,
                "sort_by": sort_by,
                "limit": limit,
                "date": date,
            },
        )

    async def scan_valuation(
        self,
        *,
        timeframe: Optional[str] = None,
        sector: Optional[str] = None,
        direction: Optional[str] = None,
        min_severity: Optional[str] = None,
        sort_by: Optional[str] = None,
        limit: Optional[int] = None,
        date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Scan for valuation outliers.

        Args:
            timeframe: ``"daily"`` or ``"weekly"``.
            sector: Filter by sector.
            direction: ``"undervalued"``, ``"overvalued"``, or ``"all"``.
            min_severity: ``"deep_value"`` or ``"extreme_premium"``.
            sort_by: ``"valuation_percentile"`` or ``"pe_vs_history"``.
            limit: Max results (1-50).
            date: ISO 8601 date string.

        Returns:
            Dict with ``data`` and ``rate_limits`` keys.
        """
        return await self._request(
            "GET",
            "/scan/valuation",
            params={
                "timeframe": timeframe,
                "sector": sector,
                "direction": direction,
                "min_severity": min_severity,
                "sort_by": sort_by,
                "limit": limit,
                "date": date,
            },
        )

    async def scan_insider_activity(
        self,
        *,
        timeframe: Optional[str] = None,
        sector: Optional[str] = None,
        direction: Optional[str] = None,
        sort_by: Optional[str] = None,
        limit: Optional[int] = None,
        date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Scan for notable insider trading activity.

        Args:
            timeframe: ``"daily"`` or ``"weekly"``.
            sector: Filter by sector.
            direction: ``"buying"``, ``"selling"``, or ``"all"``.
            sort_by: ``"zone_severity"``, ``"shares_volume"``, or ``"net_ratio"``.
            limit: Max results (1-50).
            date: ISO 8601 date string.

        Returns:
            Dict with ``data`` and ``rate_limits`` keys.
        """
        return await self._request(
            "GET",
            "/scan/insider-activity",
            params={
                "timeframe": timeframe,
                "sector": sector,
                "direction": direction,
                "sort_by": sort_by,
                "limit": limit,
                "date": date,
            },
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

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncTickerAPI":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
