from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
from typing import Any

import httpx

from ._queue import SyncQueue
from ._transport import send_sync
from ._types import BatchOptions, EventProperties, PageviewPayload, TrackPayload

logger = logging.getLogger("tgram_analytics")


class TGA:
    """Synchronous tgram-analytics client.

    Create one instance per application (not per request).
    Supports context manager protocol for automatic resource cleanup.

    Example::

        with TGA("proj_xxx", "https://analytics.example.com") as tga:
            tga.track("signup", "session-123", {"plan": "pro"})
    """

    def __init__(
        self,
        api_key: str,
        server_url: str,
        *,
        batch: bool | BatchOptions = False,
        timeout: float = 10.0,
    ) -> None:
        if not api_key or not api_key.startswith("proj_"):
            raise ValueError(
                "Invalid API key. Keys must start with 'proj_'. "
                "Get yours from the Telegram bot with /projects."
            )
        if not server_url:
            raise ValueError("server_url is required.")
        if server_url.startswith("http://"):
            logger.warning(
                "tgram-analytics: server_url uses http:// — all data including "
                "your API key will be sent in cleartext. Use https:// in production."
            )

        self._api_key = api_key
        self._server_url = server_url.rstrip("/")
        self._client = httpx.Client(timeout=timeout)
        self._session_properties: dict[str, EventProperties] = {}
        self._session_lock = threading.Lock()
        self._queue: SyncQueue | None = None

        if batch:
            opts = batch if isinstance(batch, BatchOptions) else BatchOptions()
            self._queue = SyncQueue(self._server_url, self._client, opts)

    def __enter__(self) -> TGA:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def track(
        self,
        event_name: str,
        session_id: str,
        properties: EventProperties | None = None,
    ) -> None:
        """Track a custom event."""
        with self._session_lock:
            merged = {
                **self._session_properties.get(session_id, {}),
                **(properties or {}),
            }
        payload = TrackPayload(
            api_key=self._api_key,
            event_name=event_name,
            session_id=session_id,
            properties=merged,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self._dispatch("/api/v1/track", payload.to_dict())

    def pageview(
        self,
        session_id: str,
        url: str,
        referrer: str | None = None,
        properties: EventProperties | None = None,
    ) -> None:
        """Track a pageview event."""
        with self._session_lock:
            merged = {
                **self._session_properties.get(session_id, {}),
                **(properties or {}),
            }
        payload = PageviewPayload(
            api_key=self._api_key,
            session_id=session_id,
            url=url,
            referrer=referrer,
            timestamp=datetime.now(timezone.utc).isoformat(),
            properties=merged,
        )
        self._dispatch("/api/v1/pageview", payload.to_dict())

    def identify(self, session_id: str, properties: EventProperties) -> None:
        """Attach persistent properties to all subsequent events for this session."""
        with self._session_lock:
            existing = self._session_properties.get(session_id, {})
            self._session_properties[session_id] = {**existing, **properties}

    def forget(self, session_id: str) -> None:
        """Remove stored identify() properties for a session."""
        with self._session_lock:
            self._session_properties.pop(session_id, None)

    def flush(self) -> None:
        """Flush batched events. No-op if batching is disabled."""
        if self._queue is not None:
            self._queue.flush()

    def close(self) -> None:
        """Flush pending events and close the HTTP client."""
        self.flush()
        self._client.close()

    def _dispatch(self, endpoint: str, payload: dict[str, Any]) -> None:
        if self._queue is not None:
            self._queue.push(endpoint, payload)
        else:
            send_sync(self._client, f"{self._server_url}{endpoint}", payload)
