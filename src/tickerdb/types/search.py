"""Search and schema types."""

from typing import Any, Dict, List, Optional

from .common import Literal, Timeframe, TypedDict

__all__ = [
    "SearchOperator",
    "SchemaFieldType",
    "SearchFilter",
    "SearchParams",
    "SearchResponse",
    "SchemaField",
    "SchemaResponse",
]

SearchOperator = Literal["eq", "neq", "in", "gt", "gte", "lt", "lte"]
SchemaFieldType = Literal["text", "integer", "numeric", "boolean", "bigint"]


class SearchFilter(TypedDict):
    """Single search filter using canonical schema field names."""

    field: str
    op: SearchOperator
    value: Any


class SearchParams(TypedDict, total=False):
    """Parameters for the search endpoint."""

    filters: List[SearchFilter]
    timeframe: Timeframe
    date: str
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


class SchemaResponse(TypedDict, total=False):
    """Response from the schema/fields endpoint."""

    total_fields: int
    categories: List[str]
    operators: List[SearchOperator]
    fields: List[SchemaField]
