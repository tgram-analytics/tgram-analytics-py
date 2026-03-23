from __future__ import annotations

import httpx
import pytest
import respx

from tgram_analytics._transport import send_async, send_sync

SERVER = "https://analytics.example.com"
URL = f"{SERVER}/api/v1/track"
PAYLOAD = {"api_key": "proj_test", "event_name": "test", "session_id": "s1", "properties": {}}


class TestSendSync:
    @respx.mock
    def test_success(self) -> None:
        respx.post(URL).mock(return_value=httpx.Response(202))
        with httpx.Client() as client:
            send_sync(client, URL, PAYLOAD)
        assert respx.calls.call_count == 1

    @respx.mock
    def test_logs_4xx(self, caplog: pytest.LogCaptureFixture) -> None:
        respx.post(URL).mock(return_value=httpx.Response(400))
        with httpx.Client() as client:
            send_sync(client, URL, PAYLOAD)
        assert "returned 400" in caplog.text

    def test_swallows_network_error(self) -> None:
        with httpx.Client() as client:
            # Unreachable host — should not raise
            send_sync(client, "http://192.0.2.1:1/nope", PAYLOAD)


class TestSendAsync:
    @respx.mock
    @pytest.mark.asyncio
    async def test_success(self) -> None:
        respx.post(URL).mock(return_value=httpx.Response(202))
        async with httpx.AsyncClient() as client:
            await send_async(client, URL, PAYLOAD)
        assert respx.calls.call_count == 1

    @respx.mock
    @pytest.mark.asyncio
    async def test_logs_4xx(self, caplog: pytest.LogCaptureFixture) -> None:
        respx.post(URL).mock(return_value=httpx.Response(429))
        async with httpx.AsyncClient() as client:
            await send_async(client, URL, PAYLOAD)
        assert "returned 429" in caplog.text

    @pytest.mark.asyncio
    async def test_swallows_network_error(self) -> None:
        async with httpx.AsyncClient() as client:
            await send_async(client, "http://192.0.2.1:1/nope", PAYLOAD)
