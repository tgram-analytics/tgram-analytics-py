from __future__ import annotations

import json

import httpx
import pytest
import respx

from tgram_analytics import TGA, BatchOptions

SERVER = "https://analytics.example.com"
API_KEY = "proj_testkey123"


def last_request_body() -> dict:
    return json.loads(respx.calls.last.request.content)


class TestConstructor:
    def test_rejects_invalid_api_key(self) -> None:
        with pytest.raises(ValueError, match="proj_"):
            TGA("bad_key", SERVER)

    def test_rejects_empty_api_key(self) -> None:
        with pytest.raises(ValueError):
            TGA("", SERVER)

    def test_rejects_empty_server_url(self) -> None:
        with pytest.raises(ValueError, match="server_url"):
            TGA(API_KEY, "")

    def test_strips_trailing_slash(self) -> None:
        with TGA(API_KEY, f"{SERVER}/") as tga:
            assert tga._server_url == SERVER


class TestTrack:
    @respx.mock
    def test_sends_correct_payload(self) -> None:
        respx.post(f"{SERVER}/api/v1/track").mock(return_value=httpx.Response(202))
        with TGA(API_KEY, SERVER) as tga:
            tga.track("signup", "sess-1", {"plan": "pro"})
        body = last_request_body()
        assert body["api_key"] == API_KEY
        assert body["event_name"] == "signup"
        assert body["session_id"] == "sess-1"
        assert body["properties"]["plan"] == "pro"
        assert "timestamp" in body

    @respx.mock
    def test_merges_identify_properties(self) -> None:
        respx.post(f"{SERVER}/api/v1/track").mock(return_value=httpx.Response(202))
        with TGA(API_KEY, SERVER) as tga:
            tga.identify("sess-1", {"locale": "en"})
            tga.track("click", "sess-1")
        body = last_request_body()
        assert body["properties"]["locale"] == "en"

    @respx.mock
    def test_per_event_overrides_identify(self) -> None:
        respx.post(f"{SERVER}/api/v1/track").mock(return_value=httpx.Response(202))
        with TGA(API_KEY, SERVER) as tga:
            tga.identify("sess-1", {"plan": "free"})
            tga.track("upgrade", "sess-1", {"plan": "pro"})
        body = last_request_body()
        assert body["properties"]["plan"] == "pro"

    @respx.mock
    def test_identify_scoped_to_session(self) -> None:
        respx.post(f"{SERVER}/api/v1/track").mock(return_value=httpx.Response(202))
        with TGA(API_KEY, SERVER) as tga:
            tga.identify("sess-1", {"plan": "pro"})
            tga.track("click", "sess-2")
        body = last_request_body()
        assert "plan" not in body["properties"]


class TestPageview:
    @respx.mock
    def test_sends_correct_payload(self) -> None:
        respx.post(f"{SERVER}/api/v1/pageview").mock(return_value=httpx.Response(202))
        with TGA(API_KEY, SERVER) as tga:
            tga.pageview("sess-1", "/dashboard", "https://google.com")
        body = last_request_body()
        assert body["api_key"] == API_KEY
        assert body["session_id"] == "sess-1"
        assert body["url"] == "/dashboard"
        assert body["referrer"] == "https://google.com"
        assert "timestamp" in body

    @respx.mock
    def test_referrer_defaults_to_none(self) -> None:
        respx.post(f"{SERVER}/api/v1/pageview").mock(return_value=httpx.Response(202))
        with TGA(API_KEY, SERVER) as tga:
            tga.pageview("sess-1", "/home")
        body = last_request_body()
        assert body["referrer"] is None


class TestIdentifyAndForget:
    def test_identify_merges_incrementally(self) -> None:
        tga = TGA(API_KEY, SERVER)
        tga.identify("s1", {"a": 1})
        tga.identify("s1", {"b": 2})
        assert tga._session_properties["s1"] == {"a": 1, "b": 2}
        tga.close()

    def test_forget_removes_properties(self) -> None:
        tga = TGA(API_KEY, SERVER)
        tga.identify("s1", {"a": 1})
        tga.forget("s1")
        assert "s1" not in tga._session_properties
        tga.close()

    def test_forget_noop_for_unknown_session(self) -> None:
        tga = TGA(API_KEY, SERVER)
        tga.forget("nonexistent")  # should not raise
        tga.close()


class TestBatching:
    @respx.mock
    def test_flush_sends_batched_events(self) -> None:
        respx.post(f"{SERVER}/api/v1/track").mock(return_value=httpx.Response(202))
        with TGA(API_KEY, SERVER, batch=BatchOptions(max_size=100)) as tga:
            tga.track("e1", "s1")
            tga.track("e2", "s1")
            assert respx.calls.call_count == 0
            tga.flush()
            assert respx.calls.call_count == 2

    @respx.mock
    def test_flush_noop_without_batching(self) -> None:
        with TGA(API_KEY, SERVER) as tga:
            tga.flush()  # should not raise


class TestErrorHandling:
    @respx.mock
    def test_http_error_does_not_raise(self) -> None:
        respx.post(f"{SERVER}/api/v1/track").mock(return_value=httpx.Response(400))
        with TGA(API_KEY, SERVER) as tga:
            tga.track("test", "s1")  # should not raise

    def test_network_error_does_not_raise(self) -> None:
        with TGA(API_KEY, "http://192.0.2.1:1", timeout=0.5) as tga:
            tga.track("test", "s1")  # should not raise


class TestContextManager:
    @respx.mock
    def test_close_flushes_batched(self) -> None:
        respx.post(f"{SERVER}/api/v1/track").mock(return_value=httpx.Response(202))
        with TGA(API_KEY, SERVER, batch=True) as tga:
            tga.track("e1", "s1")
        # exiting context manager should flush
        assert respx.calls.call_count == 1


class TestArrayProperties:
    """Multi-value (array-valued) properties round-trip end-to-end."""

    @respx.mock
    def test_track_accepts_string_list(self) -> None:
        respx.post(f"{SERVER}/api/v1/track").mock(return_value=httpx.Response(202))
        with TGA(API_KEY, SERVER) as tga:
            tga.track(
                "onboarding_completed",
                "sess-1",
                {"role": "creator", "interest": ["vertical_to_horizontal", "unsure"]},
            )
        body = last_request_body()
        assert body["properties"]["interest"] == ["vertical_to_horizontal", "unsure"]
        assert body["properties"]["role"] == "creator"

    @respx.mock
    def test_track_accepts_int_list(self) -> None:
        respx.post(f"{SERVER}/api/v1/track").mock(return_value=httpx.Response(202))
        with TGA(API_KEY, SERVER) as tga:
            tga.track("e", "s1", {"scores": [1, 2, 3]})
        assert last_request_body()["properties"]["scores"] == [1, 2, 3]

    @respx.mock
    def test_track_preserves_list_order(self) -> None:
        """Sort is a server-side concern (for ``_set``-suffixed keys)."""
        respx.post(f"{SERVER}/api/v1/track").mock(return_value=httpx.Response(202))
        with TGA(API_KEY, SERVER) as tga:
            tga.track("e", "s1", {"tags": ["b", "a", "c"]})
        assert last_request_body()["properties"]["tags"] == ["b", "a", "c"]

    def test_track_rejects_dict_inside_list(self) -> None:
        with TGA(API_KEY, SERVER) as tga, pytest.raises(TypeError, match="tags"):
            tga.track("e", "s1", {"tags": [{"x": 1}]})  # type: ignore[list-item]

    def test_track_rejects_nested_list(self) -> None:
        with TGA(API_KEY, SERVER) as tga, pytest.raises(TypeError, match="tags"):
            tga.track("e", "s1", {"tags": [[1, 2]]})  # type: ignore[list-item]

    def test_identify_accepts_list(self) -> None:
        with TGA(API_KEY, SERVER) as tga:
            tga.identify("s1", {"ab_variants": ["A", "B"]})
            assert tga._session_properties["s1"]["ab_variants"] == ["A", "B"]

    def test_identify_rejects_bad_list(self) -> None:
        with TGA(API_KEY, SERVER) as tga, pytest.raises(TypeError, match="bad"):
            tga.identify("s1", {"bad": [{}]})  # type: ignore[list-item]
