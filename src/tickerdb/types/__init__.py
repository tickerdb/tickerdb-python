"""TypedDict definitions for TickerDB SDK parameters and responses.

Types are organized by domain in submodules and re-exported here, so both
``from tickerdb.types import X`` and ``from tickerdb import X`` keep working.
"""

from .account import AccountLimits, AccountResponse, AccountUsage
from .common import APIResponse, RateLimits, Stability, Timeframe
from .ohlcv import OhlcvBar, OhlcvResponse
from .search import (
    SchemaField,
    SchemaFieldType,
    SchemaResponse,
    SearchFilter,
    SearchOperator,
    SearchParams,
    SearchResponse,
)
from .summary import BandMeta, Event, EventsContext, EventsResponse
from .teams import (
    Team,
    TeamInvite,
    TeamMember,
    TeamPendingInvite,
    TeamRole,
    TeamsResponse,
)
from .webhooks import WebhookDeliveriesResponse, WebhookDelivery, WebhookEvents

__all__ = [
    # common
    "Timeframe",
    "Stability",
    "RateLimits",
    "APIResponse",
    # summary / events
    "BandMeta",
    "Event",
    "EventsContext",
    "EventsResponse",
    # search / schema
    "SearchOperator",
    "SchemaFieldType",
    "SearchFilter",
    "SearchParams",
    "SearchResponse",
    "SchemaField",
    "SchemaResponse",
    # account
    "AccountLimits",
    "AccountUsage",
    "AccountResponse",
    # ohlcv
    "OhlcvBar",
    "OhlcvResponse",
    # webhooks
    "WebhookEvents",
    "WebhookDelivery",
    "WebhookDeliveriesResponse",
    # teams
    "TeamRole",
    "TeamMember",
    "TeamInvite",
    "Team",
    "TeamPendingInvite",
    "TeamsResponse",
]
