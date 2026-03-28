# TickerAPI Python SDK

[![PyPI version](https://img.shields.io/pypi/v/tickerapi.svg)](https://pypi.org/project/tickerapi/)
[![Python versions](https://img.shields.io/pypi/pyversions/tickerapi.svg)](https://pypi.org/project/tickerapi/)

The official Python SDK for [TickerAPI](https://tickerapi.ai) -- financial data and market intelligence API.

- Sync and async clients
- Full type hints for IDE autocompletion
- Typed exceptions for every error class
- Rate limit information on every response

**Full API documentation:** [https://tickerapi.ai/docs](https://tickerapi.ai/docs)

## Installation

```bash
pip install tickerapi
```

## Quick Start

### Synchronous

```python
from tickerapi import TickerAPI

client = TickerAPI("your_api_key")

# Get a ticker summary
result = client.summary("AAPL")
print(result["data"])

# Rate limit info is included on every response
print(result["rate_limits"]["requests_remaining"])
```

### Asynchronous

```python
import asyncio
from tickerapi import AsyncTickerAPI

async def main():
    async with AsyncTickerAPI("your_api_key") as client:
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

### Compare

Compare multiple tickers side-by-side.

```python
result = client.compare(["AAPL", "MSFT", "GOOGL"])
result = client.compare("AAPL,MSFT,GOOGL", timeframe="weekly")
```

### Watchlist

Post a list of tickers to get watchlist data.

```python
result = client.watchlist(["AAPL", "MSFT", "TSLA"])
result = client.watchlist(["AAPL", "MSFT"], timeframe="weekly")
```

### Watchlist Changes

Get field-level state changes for your saved watchlist tickers since the last pipeline run.

```python
result = client.watchlist_changes()
result = client.watchlist_changes(timeframe="weekly")
```

### Assets

List all available assets.

```python
result = client.assets()
```

### Scan: Oversold

Find oversold assets across markets.

```python
result = client.scan_oversold()
result = client.scan_oversold(
    asset_class="stock",
    min_severity="deep_oversold",
    sort_by="severity",
    limit=10,
)
```

### Scan: Breakouts

Detect breakout patterns.

```python
result = client.scan_breakouts(direction="bullish", asset_class="stock", limit=20)
```

### Scan: Unusual Volume

Spot unusual volume activity.

```python
result = client.scan_unusual_volume(min_ratio_band="high", limit=10)
```

### Scan: Valuation

Find valuation outliers.

```python
result = client.scan_valuation(direction="undervalued", sort_by="pe_vs_history")
```

### Scan: Insider Activity

Track notable insider trading activity.

```python
result = client.scan_insider_activity(direction="buying", sort_by="net_ratio", limit=15)
```

## Error Handling

The SDK raises typed exceptions for all API errors:

```python
from tickerapi import TickerAPI, TickerAPIError, RateLimitError, NotFoundError

client = TickerAPI("your_api_key")

try:
    result = client.summary("INVALID_TICKER")
except NotFoundError as e:
    print(f"Ticker not found: {e.message}")
except RateLimitError as e:
    print(f"Rate limited! Resets at: {e.reset}")
    print(f"Upgrade: {e.upgrade_url}")
except TickerAPIError as e:
    print(f"API error [{e.status_code}]: {e.message}")
```

### Exception Hierarchy

| Exception | Status Code | Description |
|---|---|---|
| `TickerAPIError` | any | Base exception for all API errors |
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

- [TickerAPI Website](https://tickerapi.ai)
- [API Documentation](https://tickerapi.ai/docs)
- [PyPI Package](https://pypi.org/project/tickerapi/)
