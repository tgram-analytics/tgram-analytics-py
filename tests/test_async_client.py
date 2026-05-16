from __future__ import annotations

import json

import httpx
import pytest
import respx

from tgram_analytics import AsyncTGA, BatchOptions

SERVER = "https://analytics.example.com"
API_KEY = "proj_testkey123"


def last_request_body() -> dict:
    return json.loads(respx.calls.last.request.content)


class TestAsyncConstructor:
    def test_rejects_invalid_api_key(self) -> None:
        with pytest.raises(ValueError, match="proj_"):
            AsyncTGA("bad_key", SERVER)

    def test_rejects_empty_server_url(self) -> None:
        with pytest.raises(ValueError, match="server_url"):
            AsyncTGA(API_KEY, "")


class TestAsyncTrack:
    @respx.mock
    @pytest.mark.asyncio
    async def test_sends_correct_payload(self) -> None:
        respx.post(f"{SERVER}/api/v1/track").mock(return_value=httpx.Response(202))
        async with AsyncTGA(API_KEY, SERVER, batch=True) as tga:
            tga.track("signup", "sess-1", {"plan": "pro"})
            await tga.flush()
        body = last_request_body()
        assert body["api_key"] == API_KEY
        assert body["event_name"] == "signup"
        assert body["session_id"] == "sess-1"
        assert body["properties"]["plan"] == "pro"

    @respx.mock
    @pytest.mark.asyncio
    async def test_merges_identify_properties(self) -> None:
        respx.post(f"{SERVER}/api/v1/track").mock(return_value=httpx.Response(202))
        async with AsyncTGA(API_KEY, SERVER, batch=True) as tga:
            tga.identify("sess-1", {"locale": "en"})
            tga.track("click", "sess-1")
            await tga.flush()
        body = last_request_body()
        assert body["properties"]["locale"] == "en"

    @respx.mock
    @pytest.mark.asyncio
    async def test_per_event_overrides_identify(self) -> None:
        respx.post(f"{SERVER}/api/v1/track").mock(return_value=httpx.Response(202))
        async with AsyncTGA(API_KEY, SERVER, batch=True) as tga:
            tga.identify("sess-1", {"plan": "free"})
            tga.track("upgrade", "sess-1", {"plan": "pro"})
            await tga.flush()
        body = last_request_body()
        assert body["properties"]["plan"] == "pro"


class TestAsyncPageview:
    @respx.mock
    @pytest.mark.asyncio
    async def test_sends_correct_payload(self) -> None:
        respx.post(f"{SERVER}/api/v1/pageview").mock(return_value=httpx.Response(202))
        async with AsyncTGA(API_KEY, SERVER, batch=True) as tga:
            tga.pageview("sess-1", "/dashboard", "https://google.com")
            await tga.flush()
        body = last_request_body()
        assert body["url"] == "/dashboard"
        assert body["referrer"] == "https://google.com"


class TestAsyncBatching:
    @respx.mock
    @pytest.mark.asyncio
    async def test_flush_sends_batched(self) -> None:
        respx.post(f"{SERVER}/api/v1/track").mock(return_value=httpx.Response(202))
        async with AsyncTGA(API_KEY, SERVER, batch=BatchOptions(max_size=100)) as tga:
            tga.track("e1", "s1")
            tga.track("e2", "s1")
            assert respx.calls.call_count == 0
            await tga.flush()
            assert respx.calls.call_count == 2


class TestAsyncContextManager:
    @respx.mock
    @pytest.mark.asyncio
    async def test_close_flushes_batched(self) -> None:
        respx.post(f"{SERVER}/api/v1/track").mock(return_value=httpx.Response(202))
        async with AsyncTGA(API_KEY, SERVER, batch=True) as tga:
            tga.track("e1", "s1")
        assert respx.calls.call_count == 1


class TestAsyncArrayProperties:
    @respx.mock
    @pytest.mark.asyncio
    async def test_track_accepts_string_list(self) -> None:
        respx.post(f"{SERVER}/api/v1/track").mock(return_value=httpx.Response(202))
        async with AsyncTGA(API_KEY, SERVER, batch=True) as tga:
            tga.track("e", "s1", {"interest": ["a", "b"]})
            await tga.flush()
        assert last_request_body()["properties"]["interest"] == ["a", "b"]

    @pytest.mark.asyncio
    async def test_track_rejects_dict_inside_list(self) -> None:
        async with AsyncTGA(API_KEY, SERVER) as tga:
            with pytest.raises(TypeError, match="tags"):
                tga.track("e", "s1", {"tags": [{}]})  # type: ignore[list-item]

    @pytest.mark.asyncio
    async def test_identify_accepts_list(self) -> None:
        async with AsyncTGA(API_KEY, SERVER) as tga:
            tga.identify("s1", {"ab_variants": ["A", "B"]})
            assert tga._session_properties["s1"]["ab_variants"] == ["A", "B"]

    @pytest.mark.asyncio
    async def test_identify_rejects_bad_list(self) -> None:
        async with AsyncTGA(API_KEY, SERVER) as tga:
            with pytest.raises(TypeError, match="bad"):
                tga.identify("s1", {"bad": [object()]})  # type: ignore[list-item]
