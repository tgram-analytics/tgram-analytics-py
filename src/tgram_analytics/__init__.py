"""tgram-analytics — lightweight Python SDK for server-side analytics."""

from ._async_client import AsyncTGA
from ._client import TGA
from ._types import (
    BatchOptions,
    EventProperties,
    EventPropertyScalar,
    EventPropertyValue,
)

__all__ = [
    "TGA",
    "AsyncTGA",
    "BatchOptions",
    "EventProperties",
    "EventPropertyScalar",
    "EventPropertyValue",
]
__version__ = "0.2.0"
