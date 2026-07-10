"""Screener types."""

from typing import Any, List, Optional

from .common import Literal, Timeframe, TypedDict
from .search import SchemaField

__all__ = [
    "ScreenerOperator",
    "ScreenerFilter",
    "ScreenerSort",
    "Screener",
    "ScreenersResponse",
]

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
