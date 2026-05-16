"""Runtime validator for :data:`EventProperties`.

The static type annotation covers most callers, but Python's gradual
typing lets unchecked code (no ``mypy``, ``cast()``, ``Any``) bypass it.
This module is the runtime safety net that fails loudly when an
unsupported shape is about to be sent to the server, so developer
mistakes surface in tests rather than as silent server-side 422s.

Allowed value shapes:

* scalar:        ``str | int | float | bool | None``
* scalar list:   ``list[str | int | float | bool | None]``

Anything else (``dict``, nested ``list``, ``tuple``, ``set``, custom
objects) raises :class:`TypeError` with a message that names the bad
key, the position in the list when relevant, and the calling method.
"""

from __future__ import annotations

import math
from typing import Any

from ._types import EventProperties

# ``bool`` is a subclass of ``int`` in Python, so this is just the right
# set of primitive types — ``isinstance(True, _SCALAR_TYPES)`` is True.
_SCALAR_TYPES: tuple[type, ...] = (str, int, float, bool, type(None))


def _is_scalar(v: Any) -> bool:
    """Return True iff *v* is a JSON-safe scalar.

    ``NaN`` and ``±Infinity`` are JSON-unsafe (``json.dumps`` raises by
    default and silently serialises them with ``allow_nan=True``) so
    they are excluded even though they are technically ``float``\\ s.
    """
    if not isinstance(v, _SCALAR_TYPES):
        return False
    return not (isinstance(v, float) and not math.isfinite(v))


def _describe(v: Any) -> str:
    if isinstance(v, float) and not math.isfinite(v):
        return "NaN" if math.isnan(v) else "Infinity"
    return type(v).__name__


def validate_properties(props: EventProperties, method: str) -> None:
    """Validate a properties dict before it is sent or merged.

    :param props:  The properties dict. Mutates nothing.
    :param method: Calling method name (``"track"`` or ``"identify"``);
                   included in error messages to make debugging painless.
    :raises TypeError: When any value (or list element) is not a JSON-safe
                       scalar.
    """
    for key, value in props.items():
        if _is_scalar(value):
            continue

        if isinstance(value, list):
            for i, item in enumerate(value):
                if _is_scalar(item):
                    continue
                raise TypeError(
                    f"tgram_analytics.{method}(): properties[{key!r}][{i}] "
                    f"must be a scalar (str, int, float, bool, None); "
                    f"got {_describe(item)}. Lists may only contain scalar "
                    "primitives — dicts, nested lists, NaN, and Infinity "
                    "are not allowed."
                )
            continue

        raise TypeError(
            f"tgram_analytics.{method}(): properties[{key!r}] must be a "
            "scalar (str, int, float, bool, None) or a list of those "
            f"scalars; got {_describe(value)}."
        )
