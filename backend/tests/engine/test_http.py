import httpx
import pytest
import structlog

from engine import http


def _client(status: int, calls: list[httpx.Request]) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(status)

    return http.make_client(transport=httpx.MockTransport(handler))


def test_retries_503_and_stops_after_two(monkeypatch):
    slept: list[float] = []
    monkeypatch.setattr(http.time, "sleep", slept.append)
    calls: list[httpx.Request] = []

    with structlog.testing.capture_logs() as logs, pytest.raises(httpx.HTTPStatusError):
        http.get("https://example.test/events", client=_client(503, calls))

    assert len(calls) == 3
    assert slept == [1.0, 2.0]
    assert calls[0].headers["user-agent"] == http.USER_AGENT
    assert [entry["status"] for entry in logs] == [503, 503, 503]


def test_404_raises_without_retry(monkeypatch):
    monkeypatch.setattr(http.time, "sleep", lambda seconds: None)
    calls: list[httpx.Request] = []

    with pytest.raises(httpx.HTTPStatusError):
        http.get("https://example.test/events", client=_client(404, calls))

    assert len(calls) == 1
