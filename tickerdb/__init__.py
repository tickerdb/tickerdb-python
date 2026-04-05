"""TickerDB Python SDK - Financial data at your fingertips.

Usage::

    from tickerdb import TickerDB

    client = TickerDB("your_api_key")
    result = client.summary("AAPL")

For async usage::

    from tickerdb import AsyncTickerDB

    async with AsyncTickerDB("your_api_key") as client:
        result = await client.summary("AAPL")
"""

from .async_client import AsyncTickerDB
from .client import TickerDB
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
    EventsParams,
    EventsResponse,
    HistoryParams,
    HistoryResponse,
    HistoryRow,
    RateLimits,
    Stability,
)

__all__ = [
    "TickerDB",
    "AsyncTickerDB",
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
    "EventsParams",
    "EventsResponse",
    "HistoryParams",
    "HistoryResponse",
    "HistoryRow",
    "RateLimits",
    "Stability",
]

__version__ = "0.1.0"
