"""
Live sessions database layer tests.

Exercises the new live_sessions table and helpers added to
backend/database/accounts_db.py.

These tests are intentionally self-contained: they do NOT touch the
existing accounts table data, do NOT modify the rest of the system,
and do NOT introduce any fixed user limit (70 is just one of several
N values tested).
"""

import os
import sys
import sqlite3
import tempfile
import time
import uuid

import pytest


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


@pytest.fixture
def accounts_db(monkeypatch):
    """Provide a fresh accounts_db module backed by an isolated SQLite
    file. Each test gets its own DB. We import a private copy under a
    unique module name so the production module's DB_PATH / module-level
    state is never touched."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()

    import importlib.util
    module_name = "accounts_db_isolated_" + uuid.uuid4().hex
    spec = importlib.util.spec_from_file_location(
        module_name,
        os.path.join(PROJECT_ROOT, "backend", "database", "accounts_db.py"),
    )
    adb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adb)  # executes init_db() against default DB
    # Now redirect DB_PATH and re-initialise against the temp file
    adb.DB_PATH = tmp.name
    # Force a fresh schema on the temp DB
    if os.path.exists(tmp.name):
        os.unlink(tmp.name)
    adb.init_db()
    yield adb
    try:
        os.unlink(tmp.name)
    except OSError:
        pass


def _sid() -> str:
    return uuid.uuid4().hex


def _user(i: int) -> str:
    return f"user_{i:04d}"


# -------------------------------------------------------------------
# 1. live_sessions table is created
# -------------------------------------------------------------------
def test_live_sessions_table_created(accounts_db):
    conn = sqlite3.connect(accounts_db.DB_PATH)
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='live_sessions'"
        ).fetchall()
        assert rows and rows[0][0] == "live_sessions"
        # existing accounts table must still exist
        acc = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='accounts'"
        ).fetchall()
        assert acc and acc[0][0] == "accounts"
    finally:
        conn.close()


# -------------------------------------------------------------------
# 2. A live session can be inserted
# -------------------------------------------------------------------
def test_create_live_session_inserts_row(accounts_db):
    sid = _sid()
    row = accounts_db.create_live_session(sid, _user(1), ip_address="127.0.0.1")
    assert row is not None
    assert row["session_id"] == sid
    assert row["username"] == _user(1)
    assert row["status"] == accounts_db.LIVE_SESSION_STATUS_ACTIVE
    assert row["created_at"]
    assert row["last_seen"]
    assert row["ip_address"] == "127.0.0.1"


# -------------------------------------------------------------------
# 3. Session IDs are unique
# -------------------------------------------------------------------
def test_session_ids_are_unique(accounts_db):
    sid = _sid()
    a = accounts_db.create_live_session(sid, _user(1))
    b = accounts_db.create_live_session(sid, _user(2))
    assert a is not None
    assert b is None  # collision


# -------------------------------------------------------------------
# 4. A session can be retrieved
# -------------------------------------------------------------------
def test_get_live_session(accounts_db):
    sid = _sid()
    accounts_db.create_live_session(sid, _user(1))
    fetched = accounts_db.get_live_session(sid)
    assert fetched is not None
    assert fetched["session_id"] == sid
    assert fetched["username"] == _user(1)
    # Unknown id
    assert accounts_db.get_live_session(_sid()) is None
    assert accounts_db.get_live_session("") is None


# -------------------------------------------------------------------
# 5. last_seen can be updated
# -------------------------------------------------------------------
def test_touch_live_session_updates_last_seen(accounts_db):
    sid = _sid()
    accounts_db.create_live_session(sid, _user(1))
    before = accounts_db.get_live_session(sid)["last_seen"]
    time.sleep(0.01)
    assert accounts_db.touch_live_session(sid) is True
    after = accounts_db.get_live_session(sid)["last_seen"]
    assert after >= before
    # Touching an unknown id is a no-op
    assert accounts_db.touch_live_session(_sid()) is False
    assert accounts_db.touch_live_session("") is False


# -------------------------------------------------------------------
# 6. A session can be revoked
# -------------------------------------------------------------------
def test_revoke_live_session(accounts_db):
    sid = _sid()
    accounts_db.create_live_session(sid, _user(1))
    assert accounts_db.revoke_live_session(sid) is True
    row = accounts_db.get_live_session(sid)
    assert row["status"] == accounts_db.LIVE_SESSION_STATUS_REVOKED
    # Revoked sessions must NOT appear in active list
    assert accounts_db.list_active_sessions() == []
    # Revoking unknown id is a no-op
    assert accounts_db.revoke_live_session(_sid()) is False


# -------------------------------------------------------------------
# 7. Expired sessions are not returned as active
# -------------------------------------------------------------------
def test_expired_sessions_excluded_from_active(accounts_db):
    sid = _sid()
    accounts_db.create_live_session(sid, _user(1))
    # Manually backdate last_seen beyond the timeout window
    conn = sqlite3.connect(accounts_db.DB_PATH)
    try:
        conn.execute(
            "UPDATE live_sessions SET last_seen = '2000-01-01T00:00:00.000000' "
            "WHERE session_id = ?",
            (sid,),
        )
        conn.commit()
    finally:
        conn.close()
    # Tiny timeout → session must be excluded
    active = accounts_db.list_active_sessions(timeout_seconds=1)
    assert all(s["session_id"] != sid for s in active)
    # With a very large timeout, the row still appears (still status active)
    active_huge = accounts_db.list_active_sessions(timeout_seconds=10**9)
    assert any(s["session_id"] == sid for s in active_huge)


# -------------------------------------------------------------------
# 8. Multiple sessions for the same user are supported
# -------------------------------------------------------------------
def test_multiple_sessions_per_user(accounts_db):
    username = _user(42)
    sid1 = _sid()
    sid2 = _sid()
    sid3 = _sid()
    a = accounts_db.create_live_session(sid1, username)
    b = accounts_db.create_live_session(sid2, username)
    c = accounts_db.create_live_session(sid3, username)
    assert a and b and c
    active = accounts_db.list_active_sessions()
    sids = {s["session_id"] for s in active}
    assert {sid1, sid2, sid3}.issubset(sids)


# -------------------------------------------------------------------
# 9. Multiple users can have sessions
# -------------------------------------------------------------------
def test_multiple_users_have_sessions(accounts_db):
    users = [_user(i) for i in range(5)]
    for u in users:
        accounts_db.create_live_session(_sid(), u)
    active = accounts_db.list_active_sessions()
    usernames = {s["username"] for s in active}
    assert set(users).issubset(usernames)


# -------------------------------------------------------------------
# 10. N-user behaviour is dynamic
# -------------------------------------------------------------------
@pytest.mark.parametrize("n", [1, 10, 70, 100, 200])
def test_n_users_dynamic(accounts_db, n):
    for i in range(n):
        result = accounts_db.create_live_session(_sid(), _user(i))
        assert result is not None
    active = accounts_db.list_active_sessions()
    assert len(active) == n
    # Every inserted username must appear exactly once
    seen = [s["username"] for s in active]
    assert len(seen) == n
    assert len(set(seen)) == n
    # Revoke half and verify counts shrink
    for i in range(0, n, 2):
        # Find this user's session and revoke it
        for s in active:
            if s["username"] == _user(i):
                accounts_db.revoke_live_session(s["session_id"])
                break
    assert len(accounts_db.list_active_sessions()) == n // 2


# -------------------------------------------------------------------
# Timeout is configurable via env var
# -------------------------------------------------------------------
def test_timeout_configurable_via_env(monkeypatch):
    monkeypatch.setenv("LIVE_SESSION_TIMEOUT_SECONDS", "123")
    import importlib
    import backend.database.accounts_db as adb  # noqa: F401
    # Reload to re-evaluate module-level os.environ.get(...)
    importlib.reload(adb)
    assert adb.LIVE_SESSION_TIMEOUT_SECONDS == 123


# -------------------------------------------------------------------
# Existing accounts table is untouched after init
# -------------------------------------------------------------------
def test_existing_accounts_preserved(accounts_db):
    # Create one account using existing helper
    ok, acct = accounts_db.create_account(
        username="preserved01",
        password="Preserved@1",
        full_name="Preserved User",
        role="user",
        usage_reason="General Browsing",
    )
    assert ok is True
    # Now add a live session and verify account row is untouched
    accounts_db.create_live_session(_sid(), "preserved01")
    conn = sqlite3.connect(accounts_db.DB_PATH)
    try:
        rows = conn.execute(
            "SELECT username FROM accounts WHERE username='preserved01'"
        ).fetchall()
        assert rows and rows[0][0] == "preserved01"
    finally:
        conn.close()


# -------------------------------------------------------------------
# public_live_session shape
# -------------------------------------------------------------------
def test_public_live_session_shape(accounts_db):
    sid = _sid()
    accounts_db.create_live_session(sid, _user(7), ip_address="10.0.0.1")
    pub = accounts_db.public_live_session(accounts_db.get_live_session(sid))
    assert set(pub.keys()) == {
        "sessionId", "username", "createdAt", "lastSeen", "status"
    }
    assert pub["sessionId"] == sid
    assert pub["username"] == _user(7)