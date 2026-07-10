"""Tests for the fluent search query builder."""

import json

from tickerdb import AsyncSearchQuery, SearchQuery
from tickerdb.query import BaseSearchQuery


def test_subclasses_share_base():
    assert issubclass(SearchQuery, BaseSearchQuery)
    assert issubclass(AsyncSearchQuery, BaseSearchQuery)


def test_chaining_returns_same_instance_and_builds_kwargs():
    q = (
        SearchQuery(client=None)
        .eq("sector", "Technology")
        .gt("market_cap", 1000)
        .select("ticker", "sector")
        .sort("volume_percentile", "asc")
        .limit(5)
        .offset(2)
        .timeframe("weekly")
        .date("2025-02-01")
    )
    assert isinstance(q, SearchQuery)
    kwargs = q._search_kwargs()
    assert kwargs["filters"] == [
        {"field": "sector", "op": "eq", "value": "Technology"},
        {"field": "market_cap", "op": "gt", "value": 1000},
    ]
    assert kwargs["fields"] == ["ticker", "sector"]
    assert kwargs["sort_by"] == "volume_percentile"
    assert kwargs["sort_direction"] == "asc"
    assert kwargs["limit"] == 5
    assert kwargs["offset"] == 2
    assert kwargs["timeframe"] == "weekly"
    assert kwargs["date"] == "2025-02-01"


def test_execute_calls_client_search(client, recorder):
    client.query().in_("momentum_rsi_zone", ["oversold", "deep_oversold"]).execute()
    filters = json.loads(recorder.last.url.params["filters"])
    assert filters == [
        {"field": "momentum_rsi_zone", "op": "in", "value": ["oversold", "deep_oversold"]}
    ]


async def test_async_execute(async_client, recorder):
    await async_client.query().eq("sector", "Tech").execute()
    assert recorder.last.url.path == "/v1/search"
