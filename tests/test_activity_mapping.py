"""
Tests for the activity / usage-reason mapping.

These tests guard the front-end ↔ Game Theory vocabulary so a
caller cannot accidentally end up with the default 1.0 weight for
every live user.
"""

import pytest

from backend.game_theory.congestion_game import ACTIVITY_WEIGHTS
from backend.services.activity_mapping import (
    CANONICAL_ACTIVITIES,
    is_canonical,
    normalise_activity,
    normalise_many,
)


class TestNormaliseActivity:
    @pytest.mark.parametrize("raw,expected", [
        ("Online Classes / Study", "online_class"),
        ("Online Classes", "online_class"),
        ("Work From Home", "browsing"),
        ("Video Streaming", "streaming"),
        ("Online Gaming", "gaming"),
        ("Video Conferencing", "online_class"),
        ("Software Downloads", "downloading"),
        ("General Browsing", "browsing"),
        ("browsing", "browsing"),
        ("streaming", "streaming"),
        ("gaming", "gaming"),
        ("", "browsing"),
        (None, "browsing"),
        ("Mystery Value", "browsing"),
    ])
    def test_known_values(self, raw, expected):
        assert normalise_activity(raw) == expected

    def test_canonical_activities_match_engine(self):
        # Any new activity introduced in the engine must already be
        # declared here; otherwise the front-end silently uses the
        # default weight for every user.
        for key in ACTIVITY_WEIGHTS:
            assert key in CANONICAL_ACTIVITIES
        assert set(CANONICAL_ACTIVITIES) == set(ACTIVITY_WEIGHTS.keys())

    def test_normalise_many(self):
        out = normalise_many(["Online Gaming", "Video Streaming", None, "weird"])
        assert out == ["gaming", "streaming", "browsing", "browsing"]

    def test_is_canonical(self):
        assert is_canonical("gaming") is True
        assert is_canonical("not-a-real-activity") is False

    def test_output_always_canonical(self):
        for value in [None, "", "Mystery", "online_class", "GAMING", "Streaming"]:
            assert normalise_activity(value) in ACTIVITY_WEIGHTS
