from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger("tgram_analytics")


def send_sync(client: httpx.Client, url: str, payload: dict[str, Any]) -> None:
    """Fire-and-forget sync send. Logs errors, never raises."""
    try:
        resp = client.post(url, json=payload)
        if resp.status_code >= 400:
            logger.warning("tgram-analytics: %s returned %d", url, resp.status_code)
    except Exception:
        logger.debug("tgram-analytics: failed to send to %s", url, exc_info=True)


async def send_async(client: httpx.AsyncClient, url: str, payload: dict[str, Any]) -> None:
    """Fire-and-forget async send. Logs errors, never raises."""
    try:
        resp = await client.post(url, json=payload)
        if resp.status_code >= 400:
            logger.warning("tgram-analytics: %s returned %d", url, resp.status_code)
    except Exception:
        logger.debug("tgram-analytics: failed to send to %s", url, exc_info=True)
