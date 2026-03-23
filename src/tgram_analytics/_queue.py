from __future__ import annotations

import asyncio
import logging
import threading
from dataclasses import dataclass
from typing import Any

import httpx

from ._transport import send_async, send_sync
from ._types import BatchOptions

logger = logging.getLogger("tgram_analytics")


@dataclass
class QueuedEvent:
    endpoint: str
    payload: dict[str, Any]


class SyncQueue:
    """Thread-safe batching queue with background timer flush."""

    def __init__(
        self, server_url: str, client: httpx.Client, options: BatchOptions
    ) -> None:
        self._server_url = server_url
        self._client = client
        self._options = options
        self._buffer: list[QueuedEvent] = []
        self._lock = threading.Lock()
        self._timer: threading.Timer | None = None

    def push(self, endpoint: str, payload: dict[str, Any]) -> None:
        to_flush: list[QueuedEvent] = []
        with self._lock:
            self._buffer.append(QueuedEvent(endpoint=endpoint, payload=payload))
            if len(self._buffer) >= self._options.max_size:
                if self._timer is not None:
                    self._timer.cancel()
                    self._timer = None
                to_flush = self._buffer[:]
                self._buffer.clear()
            elif self._timer is None:
                self._timer = threading.Timer(self._options.max_wait, self._timer_callback)
                self._timer.daemon = True
                self._timer.start()
        self._send_events(to_flush)

    def flush(self) -> None:
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None
            events = self._buffer[:]
            self._buffer.clear()
        self._send_events(events)

    def _timer_callback(self) -> None:
        with self._lock:
            self._timer = None
            events = self._buffer[:]
            self._buffer.clear()
        self._send_events(events)

    def _send_events(self, events: list[QueuedEvent]) -> None:
        for ev in events:
            send_sync(self._client, f"{self._server_url}{ev.endpoint}", ev.payload)


class AsyncQueue:
    """Async batching queue with asyncio.Task-based timer flush."""

    def __init__(
        self, server_url: str, client: httpx.AsyncClient, options: BatchOptions
    ) -> None:
        self._server_url = server_url
        self._client = client
        self._options = options
        self._buffer: list[QueuedEvent] = []
        self._timer_task: asyncio.Task[None] | None = None

    def push(self, endpoint: str, payload: dict[str, Any]) -> None:
        self._buffer.append(QueuedEvent(endpoint=endpoint, payload=payload))
        if len(self._buffer) >= self._options.max_size:
            if self._timer_task is not None:
                self._timer_task.cancel()
                self._timer_task = None
            asyncio.ensure_future(self.flush())
        elif self._timer_task is None:
            self._timer_task = asyncio.ensure_future(self._timer_flush())

    async def _timer_flush(self) -> None:
        await asyncio.sleep(self._options.max_wait)
        await self.flush()

    async def flush(self) -> None:
        if self._timer_task is not None:
            self._timer_task.cancel()
            self._timer_task = None
        events = self._buffer[:]
        self._buffer.clear()
        for ev in events:
            await send_async(
                self._client, f"{self._server_url}{ev.endpoint}", ev.payload
            )
