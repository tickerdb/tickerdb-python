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
Stability = Literal["fresh", "holding", "established", "volatile"]
SearchOperator = Literal["eq", "neq", "in", "gt", "gte", "lt", "lte"]
SchemaFieldType = Literal["text", "integer", "numeric", "boolean", "bigint"]
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
    in summary responses when requested and in watchlist responses
    (e.g. ``rsi_zone_meta``).
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


# ---------------------------------------------------------------------------
# Search types
# ---------------------------------------------------------------------------


class SearchFilter(TypedDict):
    """Single search filter using canonical schema field names."""

    field: str
    op: SearchOperator
    value: Any


class SearchParams(TypedDict, total=False):
    """Parameters for the search endpoint."""

    filters: List[SearchFilter]
    timeframe: Timeframe
    limit: int
    offset: int
    fields: List[str]
    sort_by: str
    sort_direction: Literal["asc", "desc"]


class SearchResponse(TypedDict, total=False):
    """Response from the search endpoint."""

    timeframe: Timeframe
    date: Optional[str]
    fields: List[str]
    filter_count: int
    result_count: int
    results: List[Dict[str, Any]]


class SchemaField(TypedDict, total=False):
    """Queryable field definition from the schema endpoint."""

    name: str
    type: SchemaFieldType
    category: str
    values: List[str]
    description: str


# ---------------------------------------------------------------------------
# Schema types
# ---------------------------------------------------------------------------


class SchemaResponse(TypedDict, total=False):
    """Response from the schema/fields endpoint."""

    total_fields: int
    categories: List[str]
    operators: List[SearchOperator]
    fields: List[SchemaField]


# ---------------------------------------------------------------------------
# API response wrapper
# ---------------------------------------------------------------------------


class APIResponse(TypedDict):
    """Every SDK method returns a dict with parsed JSON data and rate limits."""

    data: Any
    rate_limits: RateLimits
