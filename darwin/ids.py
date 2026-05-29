"""Small ID helpers for the DARWIN simulator.

These IDs are not cryptographic. They are readable simulator tokens.
Production identity generation is intentionally deferred.
"""

from __future__ import annotations

from itertools import count

_counters: dict[str, count] = {}


def make_id(prefix: str) -> str:
    """Return a stable-looking simulator ID such as ``dev_0001``."""
    if not prefix or not prefix.replace("_", "").isalnum():
        raise ValueError("prefix must be a non-empty alphanumeric token")
    counter = _counters.setdefault(prefix, count(1))
    return f"{prefix}_{next(counter):04d}"
