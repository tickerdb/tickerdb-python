"""TickerAPI Python SDK - Financial data at your fingertips.

Usage::

    from tickerapi import TickerAPI

    client = TickerAPI("your_api_key")
    result = client.summary("AAPL")

For async usage::

    from tickerapi import AsyncTickerAPI

    async with AsyncTickerAPI("your_api_key") as client:
        result = await client.summary("AAPL")
"""

from .async_client import AsyncTickerAPI
from .client import TickerAPI
from .exceptions import (
    AuthenticationError,
    DataUnavailableError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    TickerAPIError,
)

__all__ = [
    "TickerAPI",
    "AsyncTickerAPI",
    "TickerAPIError",
    "AuthenticationError",
    "ForbiddenError",
    "NotFoundError",
    "RateLimitError",
    "DataUnavailableError",
]

__version__ = "0.1.0"
