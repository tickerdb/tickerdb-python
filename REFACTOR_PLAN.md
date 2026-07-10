# TickerDB Python SDK — Clean Architecture Refactor Plan

Restructure the SDK for clean separation of concerns, eliminate the large
sync/async duplication, and make naming consistent — **without breaking the
public API** that was just shipped in the `feat/api-v1-parity` work.

## Goals

1. **DRY** — one home for shared logic (transport, error mapping, rate-limit
   parsing, request building). Today it is copy-pasted across two 950-line files.
2. **Separation of concerns** — transport / endpoint definitions / typed models /
   public client surface each live in their own module.
3. **Clear, consistent naming** — predictable module names, no inline imports,
   typed return envelope instead of raw dicts.
4. **Non-breaking** — keep the flat method surface (`client.summary(...)`,
   `client.ohlcv(...)`) and the `{"data", "rate_limits"}` result shape.

## Current problems (measured)

| Problem | Evidence |
| --- | --- |
| Sync/async near-duplication | `client.py` = 950 lines, `async_client.py` = 963 lines, ~95% identical |
| Shared helpers copied verbatim | `_parse_rate_limits`, `_raise_for_status`, `_DEFAULT_BASE_URL`, `_DEFAULT_TIMEOUT` defined in **both** clients |
| Query builders duplicated | `SearchQuery` and `AsyncSearchQuery` differ only in `execute()` |
| Inline imports | `import json as _json` appears **4×** inside method bodies |
| Untyped return | every method returns `Dict[str, Any]`; callers index `result["data"]` with no type help |
| One monolithic client class | 9 endpoint groups (summary, search, schema, account, ohlcv, watchlist, screeners, webhooks, teams) in a single class |
| `types.py` growing flat | 388 lines, all models in one file |

---

## Target architecture

Keep the flat public API; split the internals into focused modules, and adopt a
`src/` layout so the package can only be imported when actually installed (this
catches missing-file / packaging bugs before users do).

```
tickerdb-python/
  pyproject.toml
  README.md
  tests/
  src/
    tickerdb/
      __init__.py        # PUBLIC surface only: re-exports + __all__
      _version.py        # version single source of truth (already done)
      py.typed           # PEP 561 marker: ship inline types to type checkers

      exceptions.py      # exception hierarchy (unchanged)

      _transport.py      # NEW — the ONE copy of shared transport concerns:
                         #   - RequestSpec (method, path, params, json)
                         #   - parse_rate_limits(headers) -> RateLimits
                         #   - raise_for_status(response)  (error-class mapping)
                         #   - build_envelope(response) -> {"data", "rate_limits"}
                         #   - DEFAULT_BASE_URL, DEFAULT_TIMEOUT, USER_AGENT

      _endpoints.py      # NEW — pure functions, no I/O. Each returns a RequestSpec
                         #   and owns the param/JSON assembly. Shared by both clients.

      query.py           # NEW — BaseSearchQuery holds filter/sort/limit state and
                         #   builds the RequestSpec; sync/async subclasses only
                         #   implement execute().

      client.py          # TickerDB (sync): owns httpx.Client + thin typed methods
                         #   that call _endpoints.* and self._send(spec).
      async_client.py    # AsyncTickerDB (async): same, with httpx.AsyncClient.

      types/             # NEW package (split of the current flat types.py):
        __init__.py      #   re-exports everything (keeps `from tickerdb.types import X`)
        common.py        #   RateLimits, Timeframe, Stability, APIResponse, enums
        summary.py       #   BandMeta, Event, EventsContext, EventsResponse
        search.py        #   SearchFilter, SearchParams, SearchResponse, SchemaField...
        account.py       #   AccountResponse, AccountLimits, AccountUsage
        ohlcv.py         #   OhlcvBar, OhlcvResponse
        screeners.py     #   Screener, ScreenerFilter, ScreenerSort, ScreenersResponse
        teams.py         #   Team, TeamMember, TeamInvite, TeamsResponse, ...
        webhooks.py      #   WebhookDelivery, WebhookDeliveriesResponse, WebhookEvents
```

### The key pattern: pure request builders + thin transport

The param/JSON assembly (the part that is identical between sync and async)
moves into `_endpoints.py` as pure functions. The clients keep their typed,
documented signatures but their **bodies become one-liners**.

```python
# _transport.py
@dataclass(frozen=True)
class RequestSpec:
    method: str
    path: str
    params: dict | None = None
    json: dict | None = None

# _endpoints.py
def ohlcv(ticker, *, start=None, end=None, cursor=None, order=None, limit=None) -> RequestSpec:
    return RequestSpec("GET", f"/ohlcv/{ticker}", params={
        "start": start, "end": end, "cursor": cursor, "order": order, "limit": limit,
    })

# client.py (sync)
def ohlcv(self, ticker, *, start=None, end=None, cursor=None, order=None, limit=None):
    """<docstring>"""
    return self._send(endpoints.ohlcv(
        ticker, start=start, end=end, cursor=cursor, order=order, limit=limit,
    ))

# async_client.py (async)
async def ohlcv(self, ticker, *, start=None, end=None, cursor=None, order=None, limit=None):
    """<docstring>"""
    return await self._send(endpoints.ohlcv(
        ticker, start=start, end=end, cursor=cursor, order=order, limit=limit,
    ))
```

`_send` is the only place that touches the network:

```python
# client.py
def _send(self, spec: RequestSpec) -> dict:
    params = {k: v for k, v in (spec.params or {}).items() if v is not None}
    resp = self._client.request(spec.method, self._base_url + spec.path,
                                params=params, json=spec.json)
    raise_for_status(resp)
    return build_envelope(resp)
```

**Result:** the request logic + docs for each endpoint live once in
`_endpoints.py`; the clients shrink to typed signatures + one-line delegations.
Estimated ~950 → ~400 lines per client, and the transport/error/rate-limit code
drops from two copies to one.

> Honest note on residual duplication: because Python's sync and async are
> separate call models, the *method signatures* still appear in both clients (and
> the builder). That is inherent and accepted by most mature SDKs. What we remove
> is the duplicated *logic* and *shared helpers*, which is where bugs hide.

---

## Naming & clarity fixes

- **Module names:** `_transport.py`, `_endpoints.py`, `query.py` clearly state
  their concern. Internal helpers lose the leading underscore when they move into
  a private module (e.g. `_raise_for_status` → `raise_for_status` inside
  `_transport`).
- **No inline imports:** move `import json` to module top (kills the 4 `_json`
  aliases).
- **Typed return envelope (optional, non-breaking):** keep returning a mapping
  but make it a typed `APIResponse` `TypedDict` (already exists) so
  `result["data"]` / `result["rate_limits"]` get IDE help. A `.data` /
  `.rate_limits` attribute object would be breaking — leave as a future option.
- **Consistent verbs:** the current method names are already good
  (`list_screeners`, `create_webhook`, `get_teams`, `iter_ohlcv`). Keep them; do
  **not** rename public methods (breaking). Only tidy private names.
- **Constants:** promote `DEFAULT_BASE_URL`, `DEFAULT_TIMEOUT`, and a single
  `USER_AGENT = f"tickerdb-python/{__version__}"` into `_transport.py` so both
  clients import them instead of redefining.

---

## Separation of concerns — who owns what

| Concern | Module |
| --- | --- |
| HTTP session lifecycle (open/close, headers, timeout) | `client.py` / `async_client.py` |
| Turning a request into bytes on the wire | `_transport._send` (per client) |
| What each endpoint's request looks like (path/params/json) | `_endpoints.py` |
| Error → exception mapping | `_transport.raise_for_status` + `exceptions.py` |
| Rate-limit header parsing | `_transport.parse_rate_limits` |
| Fluent search building | `query.py` |
| Data shapes | `types/` package |
| Public surface / exports | `__init__.py` |

---

## Migration plan (incremental, each step verifiable)

Do this as a sequence of small, behavior-preserving commits. After each step the
package must import (from an **editable install**, `pip install -e .`) and the
sync/async parity check must pass.

0. **Adopt the `src/` layout.** Mechanical move, do it first so every later step
   lands in the final location. Preserves git history via `git mv`.

   ```bash
   mkdir src
   git mv tickerdb src/tickerdb
   pip install -e .        # from now on, imports resolve to the installed package
   ```

   Then update `pyproject.toml`:

   ```toml
   [tool.hatch.version]
   path = "src/tickerdb/_version.py"   # was "tickerdb/_version.py"

   [tool.hatch.build.targets.wheel]
   packages = ["src/tickerdb"]          # NEW — tell hatchling where the package lives
   ```

   Verify the build still picks up `py.typed` and the dynamic version:
   ```bash
   python -m build
   python -m hatchling version
   ```

1. **Extract `_transport.py`.** Move `_parse_rate_limits`, `_raise_for_status`,
   the constants, and a new `RequestSpec` + `build_envelope`. Have both clients
   import from it. Delete the duplicated copies. *(Pure move — no behavior change.)*
2. **Add `_send(spec)` to each client** and route the existing `_request` calls
   through it. Keep `_request` as a thin shim initially.
3. **Introduce `_endpoints.py`** one endpoint group at a time (summary → search →
   schema → account → ohlcv → watchlist → screeners → webhooks → teams). For each,
   move param assembly into a builder and reduce the two client methods to
   one-line delegations. Move the canonical docstring to the builder (or keep on
   the public method — pick one convention and apply consistently).
4. **Unify the query builder** into `query.py` with a `BaseSearchQuery`; sync/async
   keep only `execute()`.
5. **Split `types.py` into the `types/` package**, with `types/__init__.py`
   re-exporting all names so existing imports keep working. Update `__init__.py`
   if it imports from `.types` (it does).
6. **Cleanup pass:** remove the `_request` shim, module-level `json` import,
   confirm `USER_AGENT` single definition, run linters.
7. **Docs:** no README changes needed (public API unchanged); add a short
   `ARCHITECTURE.md` describing the module map.

---

## Verification

- After every step: `python -c "import tickerdb"` and the parity assertion
  (sync public methods == async public methods).
- Add a **minimal test suite** (currently none) using `respx` to mock httpx:
  one test per endpoint asserting the built method + path + params/json, plus
  error-mapping tests (401→Auth, 429 `insufficient_credits`→InsufficientCredits,
  etc.). This makes the refactor safe and guards future changes.
- `python -m build` / `hatchling version` to confirm packaging still resolves the
  dynamic version, and that the new `types/` package and modules are included.

---

## Decisions to confirm before starting

1. **Keep the flat API (recommended)** vs. move to resource namespaces
   (`client.screeners.list()`, `client.teams.invite(...)`). Namespacing is
   arguably "cleaner" but is a **breaking change** for users who just adopted the
   flat API. Recommendation: keep flat now; revisit namespacing only for a future
   major (1.0).
2. **Docstring home:** on the public client methods (better IDE hover) vs. on the
   `_endpoints` builders (single source). Recommendation: keep docstrings on the
   public methods, keep builders terse.
3. **Typed return envelope:** stay with `dict`/`TypedDict` (non-breaking) vs. a
   `Response` object with `.data`/`.rate_limits` (breaking, nicer ergonomics).
   Recommendation: stay with the mapping for now.

## Non-goals

- Renaming any public method, argument, or the `{"data", "rate_limits"}` result
  shape.
- Changing runtime behavior, endpoints, or error semantics.
- Adding new endpoints (covered by the separate `SDK_UPDATE_PLAN.md`).
