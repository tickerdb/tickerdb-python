"""TypedDict definitions for TickerAPI SDK parameters and responses."""

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
        "extremely_low", "low", "normal", "elevated", "high", "extremely_high"
    ]
    sort_by: Literal["volume_percentile"]
    limit: int
    date: str


class ValuationParams(TypedDict, total=False):
    """Parameters for the valuation scan endpoint."""

    timeframe: Timeframe
    sector: str
    direction: Literal["undervalued", "overvalued", "all"]
    min_severity: Literal["deep_value", "extreme_premium"]
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
