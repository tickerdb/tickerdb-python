# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-07-10

Full parity with the TickerDB `/v1` API plus an internal refactor. **No breaking
changes** — every existing method, argument, and the `{"data", "rate_limits"}`
result shape is unchanged, so upgrading from 0.1.x is drop-in.

### Added

- `account()` — plan tier, limits, usage, and credit balance (does not consume
  the monthly quota).
- `ohlcv()` and `iter_ohlcv()` — daily OHLCV bars (split/dividend-adjusted for
  equities, unadjusted for crypto), cursor-paginated and credit-metered;
  `iter_ohlcv()` streams every bar across pages.
- `search(date=...)` and a `.date()` method on the query builder for
  point-in-time snapshot searches.
- `summary(offset=...)` for paging history/sample ranges.
- `InsufficientCreditsError` — raised by credit-metered calls (e.g. OHLCV) that
  would exceed the account's credit balance. Subclasses `RateLimitError` and
  carries `credits_required` / `credits_remaining`.
- Typed models for every new endpoint, exported from the package root.
- Test suite (pytest, mocked transport), a read-only `examples/smoke_test.py`,
  and a `dev` optional-dependencies group.

### Changed

- Internal refactor (no user-facing impact): shared transport layer
  (`_transport`), pure request builders (`_endpoints`), a unified
  `BaseSearchQuery`, a `src/` layout, and a domain-split `types/` package.
- Version is now a single source of truth in `_version.py`, read dynamically by
  the build backend; the `User-Agent` header derives from it.

## [0.1.18] and earlier

See the [git history](https://github.com/tickerdb/tickerdb-python/commits/main)
and [PyPI release history](https://pypi.org/project/tickerdb/#history) for
releases prior to this changelog.

[Unreleased]: https://github.com/tickerdb/tickerdb-python/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/tickerdb/tickerdb-python/compare/v0.1.18...v0.2.0
