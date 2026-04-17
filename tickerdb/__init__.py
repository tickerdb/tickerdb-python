"""TickerDB Python SDK - Financial data at your fingertips.

Usage::

    from tickerdb import TickerDB

    client = TickerDB("tdb_your_api_key")
    result = client.summary("AAPL")

For async usage::

    from tickerdb import AsyncTickerDB

    async with AsyncTickerDB("tdb_your_api_key") as client:
        result = await client.summary("AAPL")
"""

from .async_client import AsyncSearchQuery, AsyncTickerDB
from .client import SearchQuery, TickerDB
from .exceptions import (
    AuthenticationError,
    DataUnavailableError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    TickerDBError,
)
from .types import (
    APIResponse,
    BandMeta,
    Event,
    EventsContext,
    EventsResponse,
    RateLimits,
    SchemaResponse,
    SearchParams,
    SearchResponse,
    Stability,
)

__all__ = [
    "TickerDB",
    "AsyncTickerDB",
    "SearchQuery",
    "AsyncSearchQuery",
    "TickerDBError",
    "AuthenticationError",
    "ForbiddenError",
    "NotFoundError",
    "RateLimitError",
    "DataUnavailableError",
    "APIResponse",
    "BandMeta",
    "Event",
    "EventsContext",
    "EventsResponse",
    "RateLimits",
    "SchemaResponse",
    "SearchParams",
    "SearchResponse",
    "Stability",
]

__version__ = "0.1.0"
