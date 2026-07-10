"""Shared fixtures: clients wired to a request-recording mock transport."""

import httpx
import pytest

from tickerdb import AsyncTickerDB, TickerDB


class Recorder:
    """Records outgoing requests and returns a canned JSON response."""

    def __init__(self, payload=None, headers=None):
        self.requests = []
        self._payload = payload if payload is not None else {"ok": True}
        self._headers = headers or {"X-Requests-Remaining": "9"}

    def __call__(self, request):
        self.requests.append(request)
        return httpx.Response(200, json=self._payload, headers=self._headers)

    @property
    def last(self):
        return self.requests[-1]


@pytest.fixture
def recorder():
    return Recorder()


@pytest.fixture
def client(recorder):
    c = TickerDB("tdb_test", transport=httpx.MockTransport(recorder))
    yield c
    c.close()


@pytest.fixture
async def async_client(recorder):
    c = AsyncTickerDB("tdb_test", transport=httpx.MockTransport(recorder))
    yield c
    await c.close()
