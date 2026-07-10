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


def test_create_screener_omits_unset_fields():
    spec = endpoints.create_screener(
        filters=[{"field": "sector", "op": "eq", "value": "Tech"}], name="X"
    )
    assert spec.method == "POST"
    assert spec.json == {
        "filters": [{"field": "sector", "op": "eq", "value": "Tech"}],
        "name": "X",
    }


def test_update_screener_includes_id_and_only_provided_fields():
    spec = endpoints.update_screener("s1", name="new")
    assert spec.method == "PUT"
    assert spec.json == {"id": "s1", "name": "new"}


def test_delete_screener_default_kind():
    spec = endpoints.delete_screener("s1")
    assert spec.json == {"id": "s1", "kind": "custom"}


def test_update_webhook_only_provided_fields():
    spec = endpoints.update_webhook("wh_1", active=False)
    assert spec.json == {"id": "wh_1", "active": False}


def test_webhook_deliveries_params():
    spec = endpoints.webhook_deliveries(webhook_id="wh_1", limit=20)
    assert spec.path == "/webhooks/deliveries"
    assert spec.params == {"webhook_id": "wh_1", "limit": 20}


def test_team_action_drops_none_and_sets_action():
    spec = endpoints.team_action("invite", team_id="t1", email="a@b.com", role=None)
    assert spec.method == "POST"
    assert spec.path == "/team"
    assert spec.json == {"action": "invite", "team_id": "t1", "email": "a@b.com"}


def test_bare_builders():
    assert endpoints.schema().path == "/schema/fields"
    assert endpoints.account().path == "/account"
    assert endpoints.list_screeners().path == "/screeners"
    assert endpoints.list_webhooks().path == "/webhooks"
    assert endpoints.get_teams().path == "/team"
