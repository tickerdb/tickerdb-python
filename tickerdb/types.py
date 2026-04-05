"""TypedDict definitions for TickerDB SDK parameters and responses."""

import sys
from typing import Any, Dict, List, Optional

if sys.version_info >= (3, 8):
    from typing import Literal, TypedDict
else:
    from typing_extensions import Literal, TypedDict


# ---------------------------------------------------------------------------
# Common types
# ---------------------------------------------------------------------------

Timeframe = Literal["daily", "weekly"]
AssetClass = Literal["stock", "crypto", "etf", "all"]
Stability = Literal["fresh", "holding", "established", "volatile"]
WebhookEvents = Dict[str, bool]

# ---------------------------------------------------------------------------
# Rate limit information returned with every response
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Stability metadata (attached to band fields in summary/watchlist responses)
# ---------------------------------------------------------------------------


class BandMeta(TypedDict, total=False):
    """Stability metadata for a band field (Plus/Pro tiers).

    Appears as a sibling key with ``_meta`` suffix next to each band value
    in summary, compare, and watchlist responses (e.g. ``rsi_zone_meta``).
    """

    timeframe: Timeframe
    periods_in_current_state: int
    flips_recent: int
    flips_lookback: str
    stability: Stability


# ---------------------------------------------------------------------------
# Events response types
# ---------------------------------------------------------------------------


class Event(TypedDict, total=False):
    """A single band transition event returned by the events endpoint."""

    date: str
    band: str
    prev_band: str
    stability_at_entry: Optional[Stability]
    flips_recent_at_entry: Optional[int]
    flips_lookback: Optional[str]
    duration_days: Optional[int]
    duration_weeks: Optional[int]
    aftermath: Optional[Dict[str, Any]]


class EventsContext(TypedDict):
    """Cross-asset correlation context in events responses."""

    ticker: str
    field: str
    band: str


class EventsResponse(TypedDict, total=False):
    """Full response envelope from the events endpoint."""

    ticker: str
    field: str
    timeframe: str
    events: List[Event]
    total_occurrences: int
    query_range: str
    context: Optional[EventsContext]


class EventsParams(TypedDict, total=False):
    """Parameters for the events endpoint."""

    ticker: str
    field: str
    timeframe: Timeframe
    band: str
    limit: int
    before: str
    after: str
    context_ticker: str
    context_field: str
    context_band: str


# ---------------------------------------------------------------------------
# Scan parameter TypedDicts (for IDE autocompletion)
# ---------------------------------------------------------------------------


class OversoldParams(TypedDict, total=False):
    """Parameters for the oversold scan endpoint."""

    timeframe: Timeframe
    asset_class: AssetClass
    sector: str
    min_severity: Literal["oversold", "deep_oversold"]
    sort_by: Literal["severity", "days_oversold", "condition_percentile"]
    limit: int
    date: str


class BreakoutsParams(TypedDict, total=False):
    """Parameters for the breakouts scan endpoint."""

    timeframe: Timeframe
    asset_class: AssetClass
    sector: str
    direction: Literal["bullish", "bearish", "all"]
    sort_by: Literal["volume_ratio", "level_strength", "condition_percentile"]
    limit: int
    date: str


class UnusualVolumeParams(TypedDict, total=False):
    """Parameters for the unusual volume scan endpoint."""

    timeframe: Timeframe
    asset_class: AssetClass
    sector: str
    min_ratio_band: Literal[
        "extremely_low", "low", "normal", "above_average", "high", "extremely_high"
    ]
    sort_by: Literal["volume_percentile"]
    limit: int
    date: str


class ValuationParams(TypedDict, total=False):
    """Parameters for the valuation scan endpoint."""

    timeframe: Timeframe
    sector: str
    direction: Literal["undervalued", "overvalued", "all"]
    min_severity: Literal["deep_value", "deeply_overvalued"]
    sort_by: Literal["valuation_percentile", "pe_vs_history"]
    limit: int
    date: str


class InsiderActivityParams(TypedDict, total=False):
    """Parameters for the insider activity scan endpoint."""

    timeframe: Timeframe
    sector: str
    direction: Literal["buying", "selling", "all"]
    sort_by: Literal["zone_severity", "shares_volume", "net_ratio"]
    limit: int
    date: str


# ---------------------------------------------------------------------------
# API response wrapper
# ---------------------------------------------------------------------------


class APIResponse(TypedDict):
    """Every SDK method returns a dict with parsed JSON data and rate limits."""

    data: Any
    rate_limits: RateLimits


class HistoryRow(TypedDict, total=False):
    date: str
    schema_version: str
    summary: Dict[str, Any]
    levels: Optional[Dict[str, Any]]


class HistoryResponse(TypedDict, total=False):
    ticker: str
    timeframe: Timeframe
    start: str
    end: str
    row_count: int
    rows: List[HistoryRow]


class HistoryParams(TypedDict):
    ticker: str
    start: str
    end: str
    timeframe: Timeframe
