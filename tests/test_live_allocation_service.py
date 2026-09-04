"""
Tests for the live allocation service.

The service must:
  * derive its user list from the live_sessions table (no client input)
  * map every live user onto a canonical Game Theory activity
  * never invent weights
  * handle dynamic N users (1, 10, 70, 100, 200, 373, …)
"""

import os
import secrets
import sys
import tempfile
import uuid

import pytest

from backend.services.live_allocation_service import build_live_allocation_request

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def _isolated_db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.unlink(path)
    return path


@pytest.fixture
def clean_accounts(monkeypatch):
    """Point the production accounts_db at a brand-new SQLite file so
    every test gets a clean slate. The real on-disk accounts DB is
    never touched."""
    from backend.database import accounts_db as adb
    fresh = _isolated_db_path()
    monkeypatch.setattr(adb, "DB_PATH", fresh)
    adb.init_db()
    yield adb


def _register(adb, username: str, reason: str = "Online Gaming") -> str:
    ok, _ = adb.create_account(
        username=username,
        password="Passw0rd!",
        full_name=username.title(),
        role="user",
        usage_reason=reason,
        device_count=1,
    )
    assert ok, f"could not create {username}"
    return username


def _session_for(adb, username: str) -> str:
    sid = secrets.token_urlsafe(24)
    adb.create_live_session(
        session_id=sid,
        username=username,
        ip_address="127.0.0.1",
        user_agent="pytest",
    )
    return sid


class TestBuildLiveAllocationRequest:
    def test_empty_when_no_sessions(self, clean_accounts):
        users, meta = build_live_allocation_request()
        assert users == []
        assert meta["unique_user_count"] == 0

    def test_one_live_user(self, clean_accounts):
        adb = clean_accounts
        _register(adb, "user_one", "Online Gaming")
        _session_for(adb, "user_one")
        users, meta = build_live_allocation_request()
        assert meta["unique_user_count"] == 1
        assert len(users) == 1
        u = users[0]
        assert u["user_id"] == "user_one"
        assert u["activity"] == "gaming"
        assert u["requested_bandwidth"] > 0

    def test_activity_canonical(self, clean_accounts):
        adb = clean_accounts
        from backend.game_theory.congestion_game import ACTIVITY_WEIGHTS
        _register(adb, "alice", "Online Classes / Study")
        _register(adb, "bob1", "Video Streaming")
        _register(adb, "carol", "General Browsing")
        for n in ("alice", "bob1", "carol"):
            _session_for(adb, n)
        users, _ = build_live_allocation_request()
        activities = {u["user_id"]: u["activity"] for u in users}
        assert activities["alice"] == "online_class"
        assert activities["bob1"] == "streaming"
        assert activities["carol"] == "browsing"
        for u in users:
            assert u["activity"] in ACTIVITY_WEIGHTS

    def test_dedup_per_user(self, clean_accounts):
        adb = clean_accounts
        _register(adb, "dup_user")
        _session_for(adb, "dup_user")
        _session_for(adb, "dup_user")
        users, meta = build_live_allocation_request()
        assert meta["unique_user_count"] == 1
        assert len(users) == 1

    @pytest.mark.parametrize("count", [1, 10, 70, 100, 200, 373])
    def test_dynamic_user_counts(self, clean_accounts, count):
        adb = clean_accounts
        for i in range(count):
            _register(adb, f"dyn_user_{i}", "General Browsing")
            _session_for(adb, f"dyn_user_{i}")
        users, meta = build_live_allocation_request()
        assert meta["unique_user_count"] == count
        assert len(users) == count
        assert all(u["requested_bandwidth"] > 0 for u in users)

    def test_requested_bandwidth_contract(self, clean_accounts):
        adb = clean_accounts
        for i in range(50):
            _register(adb, f"uniq_{i}", "General Browsing")
            _session_for(adb, f"uniq_{i}")
        users1, _ = build_live_allocation_request()
        assert len(users1) == 50
        for u in users1:
            assert u["requested_bandwidth"] > 0
            assert 1.0 <= u["requested_bandwidth"] <= 25.0

        # Determinism: a second call with the same live-session population
        # must produce the identical per-user requested_bandwidth values.
        users2, _ = build_live_allocation_request()
        vals1 = {u["user_id"]: u["requested_bandwidth"] for u in users1}
        vals2 = {u["user_id"]: u["requested_bandwidth"] for u in users2}
        assert vals1 == vals2

    def test_total_bandwidth_propagated(self, clean_accounts):
        adb = clean_accounts
        _register(adb, "t_user")
        _session_for(adb, "t_user")
        _, meta = build_live_allocation_request(total_bandwidth=125.0)
        assert meta["total_bandwidth"] == 125.0
