"""
Activity / Usage-reason mapping.

The user-facing vocabulary used at registration and on the live
dashboard does not always match the exact keys in the Game Theory
``ACTIVITY_WEIGHTS`` table. This module provides a single, well-tested
mapping so the live frontend cannot accidentally map every active user
to the fallback weight of 1.0.

No new weights are invented here; the function only normalises the
existing values declared in ``backend.game_theory.congestion_game``.
"""

from __future__ import annotations

from typing import Iterable, List, Optional, Tuple

from backend.game_theory.congestion_game import ACTIVITY_WEIGHTS


# Canonical backend activity keys (must match ACTIVITY_WEIGHTS keys).
CANONICAL_ACTIVITIES: Tuple[str, ...] = tuple(ACTIVITY_WEIGHTS.keys())


# Mapping from human-friendly registration reasons to the canonical
# activity keys recognised by the Game Theory engine. Keys are
# lower-cased and stripped before lookup.
_REASON_MAP = {
    "online classes / study": "online_class",
    "online classes": "online_class",
    "online_class": "online_class",
    "work from home": "browsing",
    "work": "browsing",
    "video streaming": "streaming",
    "streaming": "streaming",
    "online gaming": "gaming",
    "gaming": "gaming",
    "video conferencing": "online_class",
    "conferencing": "online_class",
    "social media": "browsing",
    "software downloads": "downloading",
    "downloads": "downloading",
    "downloading": "downloading",
    "smart home devices": "browsing",
    "general browsing": "browsing",
    "browsing": "browsing",
    "other": "browsing",
}


def normalise_activity(value: Optional[str]) -> str:
    """Map a user-supplied activity / usage reason onto a canonical key.

    The default category is the lowest-impact one (``browsing``) because
    that is the most honest assumption when the user did not provide a
    meaningful answer.  Callers can detect this fallback by checking
    :func:`is_canonical`.
    """
    if not value:
        return "browsing"
    cleaned = str(value).strip().lower()
    if not cleaned:
        return "browsing"
    if cleaned in ACTIVITY_WEIGHTS:
        return cleaned
    mapped = _REASON_MAP.get(cleaned)
    if mapped and mapped in ACTIVITY_WEIGHTS:
        return mapped
    # Try a few simple normalisations.
    cleaned = cleaned.replace("-", "_").replace(" ", "_")
    if cleaned in ACTIVITY_WEIGHTS:
        return cleaned
    return "browsing"


def is_canonical(value: str) -> bool:
    return value in ACTIVITY_WEIGHTS


def normalise_many(values: Iterable[Optional[str]]) -> List[str]:
    return [normalise_activity(v) for v in values]
