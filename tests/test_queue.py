from __future__ import annotations

import asyncio
import time

import httpx
import pytest
import respx

from tgram_analytics._queue import AsyncQueue, SyncQueue
from tgram_analytics._types import BatchOptions

SERVER = "https://analytics.example.com"


class TestSyncQueue:
    @respx.mock
    def test_flushes_on_max_size(self) -> None:
        respx.post(f"{SERVER}/api/v1/track").mock(return_value=httpx.Response(202))
        with httpx.Client() as client:
            q = SyncQueue(SERVER, client, BatchOptions(max_size=2, max_wait=60.0))
            q.push("/api/v1/track", {"a": 1})
            assert respx.calls.call_count == 0
            q.push("/api/v1/track", {"a": 2})
            assert respx.calls.call_count == 2

    @respx.mock
    def test_manual_flush(self) -> None:
        respx.post(f"{SERVER}/api/v1/track").mock(return_value=httpx.Response(202))
        with httpx.Client() as client:
            q = SyncQueue(SERVER, client, BatchOptions(max_size=100, max_wait=60.0))
            q.push("/api/v1/track", {"a": 1})
            q.push("/api/v1/track", {"a": 2})
            assert respx.calls.call_count == 0
            q.flush()
            assert respx.calls.call_count == 2

    @respx.mock
    def test_empty_flush_noop(self) -> None:
        with httpx.Client() as client:
            q = SyncQueue(SERVER, client, BatchOptions())
            q.flush()  # should not raise

    @respx.mock
    def test_timer_flush(self) -> None:
        respx.post(f"{SERVER}/api/v1/track").mock(return_value=httpx.Response(202))
        with httpx.Client() as client:
            q = SyncQueue(SERVER, client, BatchOptions(max_size=100, max_wait=0.1))
            q.push("/api/v1/track", {"a": 1})
            assert respx.calls.call_count == 0
            time.sleep(0.3)
            assert respx.calls.call_count == 1


class TestAsyncQueue:
    @respx.mock
    @pytest.mark.asyncio
    async def test_manual_flush(self) -> None:
        respx.post(f"{SERVER}/api/v1/track").mock(return_value=httpx.Response(202))
        async with httpx.AsyncClient() as client:
            q = AsyncQueue(SERVER, client, BatchOptions(max_size=100, max_wait=60.0))
            q.push("/api/v1/track", {"a": 1})
            q.push("/api/v1/track", {"a": 2})
            await q.flush()
            assert respx.calls.call_count == 2

    @respx.mock
    @pytest.mark.asyncio
    async def test_flushes_on_max_size(self) -> None:
        respx.post(f"{SERVER}/api/v1/track").mock(return_value=httpx.Response(202))
        async with httpx.AsyncClient() as client:
            q = AsyncQueue(SERVER, client, BatchOptions(max_size=2, max_wait=60.0))
            q.push("/api/v1/track", {"a": 1})
            q.push("/api/v1/track", {"a": 2})
            # Let the ensure_future flush task run
            await asyncio.sleep(0.05)
            assert respx.calls.call_count == 2

    @respx.mock
    @pytest.mark.asyncio
    async def test_timer_flush(self) -> None:
        respx.post(f"{SERVER}/api/v1/track").mock(return_value=httpx.Response(202))
        async with httpx.AsyncClient() as client:
            q = AsyncQueue(SERVER, client, BatchOptions(max_size=100, max_wait=0.1))
            q.push("/api/v1/track", {"a": 1})
            await asyncio.sleep(0.3)
            assert respx.calls.call_count == 1
