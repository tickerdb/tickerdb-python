# TickerDB - Market context for agents.

[![PyPI version](https://img.shields.io/pypi/v/tickerdb.svg)](https://pypi.org/project/tickerdb/)
[![Python versions](https://img.shields.io/pypi/pyversions/tickerdb.svg)](https://pypi.org/project/tickerdb/)

Connect your agent to pre-computed market context that improves reasoning and reduces token usage.

- Sync and async clients
- Full type hints for IDE autocompletion
- Typed exceptions for every error class
- Rate limit information on every response

**Full API documentation:** [https://tickerdb.com/docs](https://tickerdb.com/docs)

## Installation

```bash
pip install tickerdb
```

## Quick Start

### Synchronous

```python
from tickerdb import TickerDB

client = TickerDB("tdb_your_api_key")

# Get a ticker summary
result = client.summary("AAPL")
print(result["data"])
print(result["data"]["as_of_date"])

# Rate limit info is included on every response
print(result["rate_limits"]["requests_remaining"])
```

### Asynchronous

```python
import asyncio
from tickerdb import AsyncTickerDB

async def main():
    async with AsyncTickerDB("tdb_your_api_key") as client:
        result = await client.summary("AAPL")
        print(result["data"])

asyncio.run(main())
```

## Endpoints

### Summary

Get a detailed summary for a single ticker.

```python
result = client.summary("AAPL")
result = client.summary("AAPL", timeframe="weekly")
result = client.summary("AAPL", date="2025-01-15")
```

Summary payloads are intentionally forward-compatible. Current snapshots include top-level freshness like `as_of_date`, same-candle `ohlcv.open/high/low/close/volume`, richer `volume` fields such as `price_direction_on_volume`, raw support/resistance prices such as `support_level.level_price`, optional level metadata such as `support_level.status_meta` when requested, Pro `sector_context` fields like `agreement` and `overbought_count`, and stock-only fundamentals such as `fundamentals.free_cash_flow` and nested `fundamentals.insider_activity` when available.

Summary stays band-first by default, so sibling `_meta` / `status_meta` stability objects are omitted unless you opt in:

```python
result = client.summary("AAPL", meta=True)
result = client.summary(
    "AAPL",
    fields=["trend.direction", "trend.direction_meta", "fundamentals.free_cash_flow"],
)
```

MA distance fields are available both in snapshots and events:

```python
result = client.summary("AAPL", fields=["trend.distance_from_ma_band.ma_50"])
print(result["data"]["trend"]["distance_from_ma_band"]["ma_50"])
# "proximity_above"
```

Semantic MA fields are available in the same `trend` object:

```python
result = client.summary(
    "AAPL",
    fields=[
        "trend.ma_slopes.ma_8",
        "trend.ma_slopes.ma_20",
        "trend.ma_slopes.ma_40",
        "trend.ma_slopes.ma_50",
        "trend.ma_slopes.ma_100",
        "trend.ma_slopes.ma_200",
        "trend.ma_compression_band",
        "trend.ma_crossover_event",
    ],
)
```

### Summary with Date Range

Get a summary series for one ticker across a date range by passing `start` and `end`.

```python
result = client.summary("AAPL", start="2025-01-01", end="2025-03-31")
result = client.summary("AAPL", timeframe="weekly", start="2024-01-01", end="2025-03-31")
```

### Summary with Events Filter

Query event occurrences for a specific band field.

```python
result = client.summary("AAPL", field="momentum_rsi_zone", band="deep_oversold")
result = client.summary("AAPL", field="extremes_condition", band="deep_oversold")
result = client.summary("AAPL", field="fundamentals_free_cash_flow", band="moderate_surplus")
result = client.summary("BTCUSD", field="trend_distance_ma50", band="above")
result = client.summary(
    "BTCUSD",
    field="trend_distance_ma50",
    band="above",
    context_ticker="SPY",
    context_field="trend_distance_ma50",
    context_band="below",
)
```

For MA distance event fields such as `trend_distance_ma50`, grouped `band="above"` and `band="below"` aliases are supported in addition to granular values like `proximity_above`.

Use `stats=True` when you want aggregated outcomes instead of raw event rows:

```python
result = client.summary(
    "SOLUSD",
    field="trend_distance_ma20",
    band="above",
    context_ticker="QQQ",
    context_field="trend_distance_ma20",
    context_band="above",
    before="2025-07-01",
    stats=True,
)
print(result["data"]["stats"])
```

### Watchlist

Get the saved watchlist snapshot for the authenticated account.

```python
result = client.watchlist()
print(result["data"]["as_of_date"])
result = client.watchlist(date="2025-01-15")
```

Add tickers to the saved watchlist:

```python
result = client.add_to_watchlist(["AAPL", "MSFT", "TSLA"])
```

Remove tickers from the saved watchlist:

```python
result = client.remove_from_watchlist(["TSLA"])
```

### Watchlist Changes

Get field-level state changes for your saved watchlist tickers since the last pipeline run.

```python
result = client.watchlist_changes()
result = client.watchlist_changes(timeframe="weekly")
```

### Band Stability Metadata

Summary omits sibling `_meta` objects by default so the primary band label stays front-and-center. Set `meta=True` to include full paid-tier stability metadata across the response, or request just the few `*_meta` fields you need via `fields`.

Summary and watchlist responses also include `as_of_date` so you can tell which market session the snapshot represents.

```python
result = client.summary("AAPL", meta=True)
data = result["data"]

# The band value itself
print(data["trend"]["direction"])          # "uptrend"

# Stability metadata for that band
print(data["trend"]["direction_meta"])
# {"stability": "established", "periods_in_current_state": 18, "flips_recent": 1, "flips_lookback": 20}

# Type hints available
from tickerdb import Stability, BandMeta
```

`Stability` is one of `"fresh"`, `"holding"`, `"established"`, or `"volatile"`. `BandMeta` contains the full metadata dict. Stability metadata is available on Plus and Pro tiers only.

Stability context also appears in **Watchlist**, which still includes paid-tier `_meta` objects by default, and in **Watchlist Changes**, which include stability fields inline for each changed band.

### Query Builder

The SDK includes a fluent query builder for searching assets by categorical state. Chain methods in order: select, filters, sort, limit.

```python
results = client.query() \
    .select('ticker', 'sector', 'trend_distance_ma50', 'momentum_rsi_zone', 'fundamentals_free_cash_flow') \
    .eq('trend_distance_ma50', 'proximity_above') \
    .eq('fundamentals_free_cash_flow', 'moderate_surplus') \
    .eq('sector', 'Technology') \
    .sort('extremes_condition_percentile', 'asc') \
    .limit(10) \
    .execute()
```

Pass `.date("2025-01-15")` (or `client.search(..., date="2025-01-15")`) to run the query against a point-in-time snapshot. History depth is capped by your plan.

### Account

Check your plan tier, limits, usage, and credit balance. This call does **not** consume your monthly request quota.

```python
result = client.account()
print(result["data"]["usage"]["monthly_requests_remaining"])
print(result["data"]["usage"]["credit_balance"])
```

### OHLCV

Get daily OHLCV bars for a ticker (split/dividend-adjusted for equities, unadjusted for crypto). Results are cursor-paginated and **credit-metered** (100 bars per credit, minimum 1). History depth is capped by your plan.

```python
result = client.ohlcv("AAPL", start="2025-01-01", end="2025-03-31")
for bar in result["data"]["bars"]:
    print(bar["date"], bar["close"])

# Follow the cursor manually...
if result["data"]["has_more"]:
    nxt = client.ohlcv("AAPL", cursor=result["data"]["next_cursor"])

# ...or stream every bar across pages automatically
for bar in client.iter_ohlcv("AAPL", start="2025-01-01"):
    print(bar["date"], bar["close"])
```

If a request would exceed your credit balance, `InsufficientCreditsError` is raised with `credits_required` and `credits_remaining` attributes.

### Screeners

List, create, update, and delete saved screeners. Built-in "default" screeners and your saved "custom" screeners are returned together.

```python
result = client.list_screeners()
print(result["data"]["screeners"])

created = client.create_screener(
    name="Oversold tech",
    filters=[
        {"field": "momentum_rsi_zone", "op": "in", "value": ["deep_oversold", "oversold"]},
        {"field": "sector", "op": "eq", "value": "Technology"},
    ],
    sort={"field": "market_cap", "direction": "desc"},
)
screener_id = created["data"]["screener"]["id"]

client.update_screener(screener_id, name="Oversold tech (updated)")
client.delete_screener(screener_id)                 # delete a custom screener
client.delete_screener("oversold", kind="default")  # hide a built-in screener
```

Filters support value operators (`eq`, `neq`, `in`, `gt`, `gte`, `lt`, `lte`, `exists`) and change filters (`{"type": "change", "field": ..., "from": ..., "to": ...}`).

### Webhooks

Manage webhooks and inspect their delivery history.

```python
hooks = client.list_webhooks()
created = client.create_webhook("https://example.com/hook", events={"daily": True})
webhook_id = created["data"]["id"]

client.update_webhook(webhook_id, active=False)
client.delete_webhook(webhook_id)

# Recent delivery attempts (status, retries, HTTP status, errors)
deliveries = client.webhook_deliveries(limit=20)
deliveries = client.webhook_deliveries(webhook_id=webhook_id)
```

### Teams

View teams and manage members (most write actions require a business plan and owner/admin role).

```python
teams = client.get_teams()

team_id = client.create_team("Research")["data"]["team"]["id"]
client.invite_member(team_id, "analyst@example.com", role="member")
client.promote_member(team_id, user_id, role="admin")
client.set_seats(team_id, total_seats=10)
client.rename_team(team_id, "Research & Strategy")

# Also: remove_member, cancel_invite, resend_invite, leave_team
```

All team methods are also available on `AsyncTickerDB` with `await`.

## Error Handling

The SDK raises typed exceptions for all API errors:

```python
from tickerdb import TickerDB, TickerDBError, RateLimitError, NotFoundError

client = TickerDB("tdb_your_api_key")

try:
    result = client.summary("INVALID_TICKER")
except NotFoundError as e:
    print(f"Ticker not found: {e.message}")
except RateLimitError as e:
    print(f"Rate limited! Resets at: {e.reset}")
    print(f"Upgrade: {e.upgrade_url}")
except TickerDBError as e:
    print(f"API error [{e.status_code}]: {e.message}")
```

### Exception Hierarchy

| Exception | Status Code | Description |
|---|---|---|
| `TickerDBError` | any | Base exception for all API errors |
| `AuthenticationError` | 401 | Invalid or missing API key |
| `ForbiddenError` | 403 | Endpoint restricted to higher tier |
| `NotFoundError` | 404 | Asset not found |
| `RateLimitError` | 429 | Rate limit exceeded |
| `InsufficientCreditsError` | 429 | Credit-metered request (e.g. OHLCV) exceeds your credit balance |
| `DataUnavailableError` | 503 | Data temporarily unavailable |

`InsufficientCreditsError` subclasses `RateLimitError` (so existing `except RateLimitError` handlers still catch it) and adds `credits_required` and `credits_remaining` attributes.

All exceptions include `status_code`, `error_type`, `message`, and optionally `upgrade_url` and `reset` attributes.

## Rate Limits

Every response includes a `rate_limits` dict parsed from the API headers:

```python
result = client.summary("AAPL")
limits = result["rate_limits"]

print(limits["request_limit"])           # Total request limit
print(limits["requests_remaining"])      # Requests remaining
print(limits["request_reset"])           # Reset timestamp
print(limits["hourly_request_limit"])    # Hourly limit
print(limits["hourly_requests_remaining"])  # Hourly remaining
```

## Links

- [TickerDB Website](https://tickerdb.com)
- [API Documentation](https://tickerdb.com/docs)
- [PyPI Package](https://pypi.org/project/tickerdb/)
