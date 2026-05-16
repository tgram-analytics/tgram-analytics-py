from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Union

#: A single JSON-safe scalar — the building block of :data:`EventProperties`.
EventPropertyScalar = Union[str, int, float, bool, None]

#: One value in an :data:`EventProperties` dict — either a scalar or a list
#: of scalars. Nested lists and dict values are intentionally not part of
#: the type so the server-side JSONB column stays cheap to query.
EventPropertyValue = Union[EventPropertyScalar, list[EventPropertyScalar]]

#: Arbitrary key-value properties attached to events.
#:
#: Values must be JSON-serialisable scalars — ``str``, ``int``, ``float``,
#: ``bool``, ``None`` — or a ``list`` of those scalars (e.g. for
#: multi-select onboarding answers like
#: ``{"interest": ["vertical_to_horizontal", "unsure"]}``).
#:
#: Every array property is sorted server-side at write time, so
#: ``GROUP BY properties->'foo'`` collapses equivalent combinations into
#: a single bucket without read-time normalisation. No naming convention
#: required. If insertion order matters for some property, serialize the
#: list to a string instead.
EventProperties = dict[str, EventPropertyValue]


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
