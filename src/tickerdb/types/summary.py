"""Summary and events response types."""

from typing import Any, Dict, List, Optional

from .common import Stability, Timeframe, TypedDict

__all__ = ["BandMeta", "Event", "EventsContext", "EventsResponse"]


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
