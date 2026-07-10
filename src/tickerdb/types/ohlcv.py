"""OHLCV endpoint types."""

from typing import List, Optional

from .common import Literal, TypedDict

__all__ = ["OhlcvBar", "OhlcvResponse"]


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
