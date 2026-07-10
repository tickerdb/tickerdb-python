"""Read-only smoke test against the live TickerDB API.

Exercises the main read endpoints with a real API key so you can confirm the
SDK talks to production correctly. It performs no writes (no webhook/screener/
team mutations), so it is safe to run against any account.

Usage::

    # bash / macOS / Linux
    export TICKERDB_API_KEY=tdb_your_key
    python examples/smoke_test.py

    # PowerShell
    $env:TICKERDB_API_KEY = "tdb_your_key"
    python examples/smoke_test.py
"""

import os
import sys

from tickerdb import TickerDB, TickerDBError


def main() -> int:
    api_key = os.environ.get("TICKERDB_API_KEY")
    if not api_key:
        print("Set TICKERDB_API_KEY first (see the module docstring).")
        return 2

    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"

    with TickerDB(api_key) as client:
        try:
            acct = client.account()["data"]
            print(f"account : tier={acct.get('tier')} "
                  f"remaining={acct['usage']['monthly_requests_remaining']} "
                  f"credits={acct['usage'].get('credit_balance')}")

            summ = client.summary(ticker)
            print(f"summary : {ticker} as_of={summ['data'].get('as_of_date')} "
                  f"(rate-limit remaining={summ['rate_limits'].get('requests_remaining')})")

            fields = client.schema()["data"].get("fields", [])
            print(f"schema  : {len(fields)} queryable fields")

            res = client.search(
                filters=[{"field": "momentum_rsi_zone", "op": "eq", "value": "oversold"}],
                limit=3,
            )["data"]
            print(f"search  : {res.get('result_count')} results for RSI=oversold")

            bars = client.ohlcv(ticker, limit=5)["data"].get("bars", [])
            print(f"ohlcv   : {len(bars)} bars, latest close="
                  f"{bars[0]['close'] if bars else 'n/a'}")

            wl = client.watchlist()["data"]
            print(f"watchlist: as_of={wl.get('as_of_date')}")
        except TickerDBError as e:
            print(f"\nAPI error [{e.status_code}] {e.error_type}: {e.message}")
            return 1

    print("\nAll read endpoints responded OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
