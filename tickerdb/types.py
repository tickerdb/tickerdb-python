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
# Account types
# ---------------------------------------------------------------------------


class AccountLimits(TypedDict, total=False):
    """Plan limits reported by the account endpoint."""

    monthly_requests: int
    overage_enabled: bool
    watchlist_limit: int
    search_results: int
    webhook_urls: int
    history_days: int


class AccountUsage(TypedDict, total=False):
    """Current usage reported by the account endpoint."""

    monthly_requests_used: int
    monthly_requests_remaining: int
    credit_balance: int


class AccountResponse(TypedDict, total=False):
    """Response from the account endpoint."""

    tier: str
    tier_full: str
    email: str
    limits: AccountLimits
    usage: AccountUsage
    scheduled_tier: Optional[str]
    scheduled_change_at: Optional[str]


# ---------------------------------------------------------------------------
# OHLCV types
# ---------------------------------------------------------------------------


class OhlcvBar(TypedDict):
    """A single daily OHLCV bar."""

    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class OhlcvResponse(TypedDict, total=False):
    """Response from the OHLCV endpoint.

    OHLCV requests are credit-metered (100 bars per credit, minimum 1) and
    cursor-paginated: follow ``next_cursor`` while ``has_more`` is true.
    """

    ticker: str
    asset_class: str
    currency: Optional[str]
    timeframe: str
    data_status: str
    adjustment: str
    order: Literal["asc", "desc"]
    start: str
    end: Optional[str]
    row_count: int
    has_more: bool
    next_cursor: Optional[str]
    bars: List[OhlcvBar]
    plan_history_days: int
    plan: str


# ---------------------------------------------------------------------------
# Screener types
# ---------------------------------------------------------------------------

ScreenerOperator = Literal[
    "eq", "neq", "in", "gt", "gte", "lt", "lte", "exists", "changed"
]

# Functional TypedDict syntax because ``from`` is a Python keyword and cannot
# be a class attribute.
ScreenerFilter = TypedDict(
    "ScreenerFilter",
    {
        "type": Literal["value", "change"],
        "field": str,
        "op": ScreenerOperator,
        "value": Any,
        "from": Any,
        "to": Any,
        "periods": int,
    },
    total=False,
)


class ScreenerSort(TypedDict):
    """Sort specification for a screener."""

    field: str
    direction: Literal["asc", "desc"]


class Screener(TypedDict, total=False):
    """A saved custom or built-in default screener."""

    id: str
    kind: Literal["default", "custom"]
    name: str
    description: str
    timeframe: Timeframe
    filters: List[ScreenerFilter]
    return_fields: List[str]
    sort: Optional[ScreenerSort]
    readonly: bool


class ScreenersResponse(TypedDict, total=False):
    """Response from the screeners list endpoint."""

    defaults: List[Screener]
    saved: List[Screener]
    screeners: List[Screener]
    fields: List[SchemaField]


# ---------------------------------------------------------------------------
# Webhook delivery types
# ---------------------------------------------------------------------------


class WebhookDelivery(TypedDict, total=False):
    """A single webhook delivery attempt record."""

    id: str
    webhook_id: str
    event_type: str
    timeframe: str
    run_date: str
    status: str
    attempt_count: Optional[int]
    http_status: Optional[int]
    error: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]


class WebhookDeliveriesResponse(TypedDict, total=False):
    """Response from the webhook deliveries endpoint."""

    deliveries: List[WebhookDelivery]
    count: int
    limit: int


# ---------------------------------------------------------------------------
# Team types
# ---------------------------------------------------------------------------

TeamRole = Literal["owner", "admin", "member"]


class TeamMember(TypedDict, total=False):
    """A member of a team."""

    user_id: str
    email: str
    name: Optional[str]
    role: TeamRole
    joined_at: Optional[str]


class TeamInvite(TypedDict, total=False):
    """A pending invite on a team (as seen by owners/admins)."""

    id: str
    email: str
    role: TeamRole
    expires_at: Optional[str]
    created_at: Optional[str]


class Team(TypedDict, total=False):
    """A team the authenticated user belongs to."""

    id: str
    name: str
    max_seats: int
    extra_seats: int
    seats_used: int
    seats_available: int
    your_role: TeamRole
    members: List[TeamMember]
    pending_invites: List[TeamInvite]


class TeamPendingInvite(TypedDict, total=False):
    """A pending invite addressed to the authenticated user."""

    id: str
    team_id: str
    team_name: str
    role: TeamRole
    inviter_email: str
    expires_at: Optional[str]


class TeamsResponse(TypedDict, total=False):
    """Response from the team list endpoint."""

    teams: List[Team]
    my_pending_invites: List[TeamPendingInvite]


# ---------------------------------------------------------------------------
# API response wrapper
# ---------------------------------------------------------------------------


class APIResponse(TypedDict):
    """Every SDK method returns a dict with parsed JSON data and rate limits."""

    data: Any
    rate_limits: RateLimits
