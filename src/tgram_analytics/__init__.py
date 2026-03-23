"""tgram-analytics — lightweight Python SDK for server-side analytics."""

from ._async_client import AsyncTGA
from ._client import TGA
from ._types import BatchOptions, EventProperties

__all__ = ["TGA", "AsyncTGA", "BatchOptions", "EventProperties"]
__version__ = "0.1.0"
