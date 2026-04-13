# TickerDB Python SDK

[![PyPI version](https://img.shields.io/pypi/v/tickerdb.svg)](https://pypi.org/project/tickerdb/)
[![Python versions](https://img.shields.io/pypi/pyversions/tickerdb.svg)](https://pypi.org/project/tickerdb/)

The official Python SDK for [TickerDB](https://tickerdb.com) -- financial data and market intelligence API.

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

client = TickerDB("your_api_key")

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
    async with AsyncTickerDB("your_api_key") as client:
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

Every band field (trend direction, momentum zone, etc.) now includes a sibling `_meta` object with stability context. This tells you how long a state has been held, how often it has flipped recently, and an overall stability label.

Summary and watchlist responses also include `as_of_date` so you can tell which market session the snapshot represents.

```python
result = client.summary("AAPL")
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

Stability context also appears in **Watchlist Changes**, which include stability fields for each changed band.

### Query Builder

The SDK includes a fluent query builder for searching assets by categorical state. Chain methods in order: select, filters, sort, limit.

```python
results = client.query() \
    .select('ticker', 'sector', 'momentum_rsi_zone') \
    .eq('momentum_rsi_zone', 'oversold') \
    .eq('sector', 'Technology') \
    .sort('extremes_condition_percentile', 'asc') \
    .limit(10) \
    .execute()
```

## Error Handling

The SDK raises typed exceptions for all API errors:

```python
from tickerdb import TickerDB, TickerDBError, RateLimitError, NotFoundError

client = TickerDB("your_api_key")

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
| `DataUnavailableError` | 503 | Data temporarily unavailable |

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
