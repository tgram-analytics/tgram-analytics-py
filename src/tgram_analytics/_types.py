from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Union

EventProperties = dict[str, Union[str, int, float, bool, None]]


@dataclass(frozen=True)
class BatchOptions:
    """Configuration for the event batching queue."""

    max_size: int = 10
    max_wait: float = 5.0


@dataclass(frozen=True)
class TrackPayload:
    """Request body for POST /api/v1/track."""

    api_key: str
    event_name: str
    session_id: str
    properties: dict[str, Any]
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "api_key": self.api_key,
            "event_name": self.event_name,
            "session_id": self.session_id,
            "properties": self.properties,
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class PageviewPayload:
    """Request body for POST /api/v1/pageview."""

    api_key: str
    session_id: str
    url: str
    referrer: str | None
    timestamp: str
    properties: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "api_key": self.api_key,
            "session_id": self.session_id,
            "url": self.url,
            "referrer": self.referrer,
            "timestamp": self.timestamp,
            "properties": self.properties,
        }
