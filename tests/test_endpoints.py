"""Unit tests for the pure request builders in tickerdb._endpoints.

These need no HTTP mocking: each builder returns a RequestSpec we can assert on.
"""

import json

from tickerdb import _endpoints as endpoints


def test_summary_encodes_fields_and_maps_flags():
    spec = endpoints.summary(
        "AAPL", timeframe="daily", fields=["trend.direction"], meta=True, stats=True
    )
    assert spec.method == "GET"
    assert spec.path == "/summary/AAPL"
    assert spec.params["timeframe"] == "daily"
    assert spec.params["fields"] == json.dumps(["trend.direction"])
    assert spec.params["meta"] == "true"
    assert spec.params["stats"] == "true"
    # unset stays None (dropped later by the transport layer)
    assert spec.params["date"] is None


def test_summary_meta_false_and_no_stats():
    spec = endpoints.summary("AAPL", meta=False)
    assert spec.params["meta"] == "false"
    assert spec.params["stats"] is None


def test_search_encodes_filters_and_fields():
    spec = endpoints.search(
        filters=[{"field": "sector", "op": "eq", "value": "Technology"}],
        fields=["ticker", "sector"],
        date="2025-01-15",
    )
    assert spec.method == "GET"
    assert spec.path == "/search"
    assert json.loads(spec.params["filters"])[0]["field"] == "sector"
    assert spec.params["fields"] == json.dumps(["ticker", "sector"])
    assert spec.params["date"] == "2025-01-15"


def test_ohlcv_path_and_params():
    spec = endpoints.ohlcv("AAPL", start="2025-01-01", order="asc", limit=500)
    assert spec.path == "/ohlcv/AAPL"
    assert spec.params == {
        "start": "2025-01-01",
        "end": None,
        "cursor": None,
        "order": "asc",
        "limit": 500,
    }


def test_watchlist_mutations_normalize_tickers():
    add = endpoints.add_to_watchlist([" aapl ", "msft"])
    assert add.method == "POST"
    assert add.json == {"tickers": ["AAPL", "MSFT"]}

    remove = endpoints.remove_from_watchlist(["tsla"])
    assert remove.method == "DELETE"
    assert remove.json == {"tickers": ["TSLA"]}


def test_bare_builders():
    assert endpoints.schema().path == "/schema/fields"
    assert endpoints.account().path == "/account"
