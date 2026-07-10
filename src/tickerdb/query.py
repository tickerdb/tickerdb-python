"""Shared fluent query builder for the search endpoint.

``BaseSearchQuery`` holds all the builder state and logic; the sync and async
clients each subclass it and implement only ``execute()``.
"""

from typing import Any, Dict, List, Optional, TypeVar

# Bound to the base so chained builder calls return the concrete subclass type
# (``SearchQuery`` or ``AsyncSearchQuery``), preserving IDE autocompletion.
Q = TypeVar("Q", bound="BaseSearchQuery")


class BaseSearchQuery:
    """Fluent query builder for the search endpoint.

    Usage::

        results = client.query() \\
            .eq("trend_distance_ma50", "proximity_above") \\
            .eq("sector", "Technology") \\
            .select("ticker", "sector", "trend_distance_ma50") \\
            .sort("extremes_condition_percentile", "asc") \\
            .limit(10) \\
            .execute()

    ``execute()`` is provided by the concrete sync/async subclass.
    """

    def __init__(self, client: Any) -> None:
        self._client = client
        self._filters: List[Dict[str, Any]] = []
        self._fields: Optional[List[str]] = None
        self._sort_by: Optional[str] = None
        self._sort_direction: Optional[str] = None
        self._limit: Optional[int] = None
        self._offset: Optional[int] = None
        self._timeframe: Optional[str] = None
        self._date: Optional[str] = None

    def eq(self: Q, field: str, value: Any) -> Q:
        self._filters.append({"field": field, "op": "eq", "value": value})
        return self

    def neq(self: Q, field: str, value: Any) -> Q:
        self._filters.append({"field": field, "op": "neq", "value": value})
        return self

    def in_(self: Q, field: str, values: list) -> Q:
        self._filters.append({"field": field, "op": "in", "value": values})
        return self

    def gt(self: Q, field: str, value: Any) -> Q:
        self._filters.append({"field": field, "op": "gt", "value": value})
        return self

    def gte(self: Q, field: str, value: Any) -> Q:
        self._filters.append({"field": field, "op": "gte", "value": value})
        return self

    def lt(self: Q, field: str, value: Any) -> Q:
        self._filters.append({"field": field, "op": "lt", "value": value})
        return self

    def lte(self: Q, field: str, value: Any) -> Q:
        self._filters.append({"field": field, "op": "lte", "value": value})
        return self

    def select(self: Q, *fields: str) -> Q:
        self._fields = list(fields)
        return self

    def sort(self: Q, field: str, direction: str = "desc") -> Q:
        self._sort_by = field
        self._sort_direction = direction
        return self

    def limit(self: Q, n: int) -> Q:
        self._limit = n
        return self

    def offset(self: Q, n: int) -> Q:
        self._offset = n
        return self

    def timeframe(self: Q, tf: str) -> Q:
        self._timeframe = tf
        return self

    def date(self: Q, d: str) -> Q:
        self._date = d
        return self

    def _search_kwargs(self) -> Dict[str, Any]:
        """Collect the accumulated state as keyword args for ``client.search``."""
        return dict(
            filters=self._filters,
            fields=self._fields,
            sort_by=self._sort_by,
            sort_direction=self._sort_direction,
            limit=self._limit,
            offset=self._offset,
            timeframe=self._timeframe,
            date=self._date,
        )
