"""Integration tests driving the clients through a mock transport."""

import json

import httpx

from tickerdb import AsyncTickerDB, TickerDB


def test_summary_request_and_envelope(client, recorder):
    result = client.summary("AAPL", timeframe="daily", date=None)
    # envelope
    assert result["data"] == {"ok": True}
    assert result["rate_limits"]["requests_remaining"] == 9
    # request: path built, None params dropped
    url = recorder.last.url
    assert url.path == "/v1/summary/AAPL"
    assert url.params["timeframe"] == "daily"
    assert "date" not in url.params


def test_search_sends_filters(client, recorder):
    client.search(filters=[{"field": "sector", "op": "eq", "value": "Tech"}])
    filters = json.loads(recorder.last.url.params["filters"])
    assert filters == [{"field": "sector", "op": "eq", "value": "Tech"}]


def test_add_to_watchlist_body(client, recorder):
    client.add_to_watchlist([" aapl ", "msft"])
    assert json.loads(recorder.last.content) == {"tickers": ["AAPL", "MSFT"]}
    assert recorder.last.method == "POST"


def test_iter_ohlcv_follows_cursor():
    # Two pages: first has_more with a cursor, second ends it.
    pages = [
        {"bars": [{"date": "2025-01-02"}], "has_more": True, "next_cursor": "2025-01-02"},
        {"bars": [{"date": "2025-01-01"}], "has_more": False, "next_cursor": None},
    ]
    seen_cursors = []

    def handler(request):
        seen_cursors.append(request.url.params.get("cursor"))
        return httpx.Response(200, json=pages[len(seen_cursors) - 1])

    c = TickerDB("tdb_test", transport=httpx.MockTransport(handler))
    bars = list(c.iter_ohlcv("AAPL", start="2025-01-01"))
    c.close()

    assert [b["date"] for b in bars] == ["2025-01-02", "2025-01-01"]
    # first request has no cursor, second uses the returned next_cursor
    assert seen_cursors == [None, "2025-01-02"]


async def test_async_summary(async_client, recorder):
    result = await async_client.summary("AAPL", timeframe="weekly")
    assert result["data"] == {"ok": True}
    assert recorder.last.url.path == "/v1/summary/AAPL"
    assert recorder.last.url.params["timeframe"] == "weekly"


def test_user_agent_header_present(client):
    ua = client._client.headers["user-agent"]
    assert ua.startswith("tickerdb-python/")


def test_sync_async_method_parity():
    sync = {n for n in dir(TickerDB) if not n.startswith("_")}
    asy = {n for n in dir(AsyncTickerDB) if not n.startswith("_")}
    assert sync == asy
