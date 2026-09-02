"""
Tests for the authenticated logout endpoint and session expiration
semantics.

POST /api/auth/logout
Authorization: Bearer <sessionId>

Covers:
* Valid Bearer + valid session → logout succeeds, session revoked.
* Revoked session is excluded from list_active_sessions().
* Multiple sessions for one user are revoked independently.
* Missing / malformed Authorization → 401.
* Unknown / already-revoked sessions handled correctly.
* Session ID is never echoed back.
* ?token=<sid> query string alone does NOT authenticate.
* Fresh session → active.
* Session older than configured timeout → expired / inactive.
* Expired session excluded from active-session queries.
* Timeout configuration respected.
* Heartbeat cannot resurrect an already-expired session.
* N-user parametrised logout for N=1,10,70,100,200.
"""

import importlib.util
import json
import os
import sqlite3
import sys
import tempfile
import time
import uuid

import pytest


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_PATH = os.path.join(PROJECT_ROOT, "backend")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)


def _pw(i: int = 0) -> str:
    return f"Lo@Pass{i:04d}1"


def _seed(adb, count: int):
    usernames = []
    for i in range(count):
        uname = f"lo_{i:04d}"
        ok, _ = adb.create_account(
            username=uname,
            password=_pw(i),
            full_name=f"LO User {i}",
            role="user",
            usage_reason="Online Classes / Study",
        )
        assert ok, f"failed to seed {uname}"
        usernames.append(uname)
    return usernames


@pytest.fixture
def auth_client(monkeypatch):
    """Wire the Flask app against an isolated SQLite DB."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()

    spec = importlib.util.spec_from_file_location(
        "accounts_db_isolated_" + uuid.uuid4().hex,
        os.path.join(PROJECT_ROOT, "backend", "database", "accounts_db.py"),
    )
    adb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adb)
    adb.DB_PATH = tmp.name
    if os.path.exists(tmp.name):
        os.unlink(tmp.name)
    adb.init_db()

    import backend.routes.auth_routes as auth_routes
    auth_routes.verify_credentials = adb.verify_credentials
    auth_routes.get_account = adb.get_account
    auth_routes.username_exists = adb.username_exists
    auth_routes.public_account = adb.public_account
    auth_routes.create_account = adb.create_account
    auth_routes.list_accounts = adb.list_accounts
    auth_routes.create_live_session = adb.create_live_session
    auth_routes.get_live_session = adb.get_live_session
    auth_routes.touch_live_session = adb.touch_live_session
    auth_routes.revoke_live_session = adb.revoke_live_session
    auth_routes.LIVE_SESSION_STATUS_ACTIVE = adb.LIVE_SESSION_STATUS_ACTIVE
    auth_routes.LIVE_SESSION_STATUS_REVOKED = adb.LIVE_SESSION_STATUS_REVOKED
    auth_routes.LIVE_SESSION_TIMEOUT_SECONDS = adb.LIVE_SESSION_TIMEOUT_SECONDS

    from backend.app import app
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client, adb

    try:
        os.unlink(tmp.name)
    except OSError:
        pass


def _login(client, username, password):
    return client.post(
        "/api/auth/login",
        data=json.dumps({"username": username, "password": password}),
        content_type="application/json",
    )


def _logout(client, session_id=None, header_value=None, omit_auth=False):
    headers = {}
    if not omit_auth:
        if header_value is not None:
            headers["Authorization"] = header_value
        elif session_id is not None:
            headers["Authorization"] = f"Bearer {session_id}"
    return client.post(
        "/api/auth/logout",
        data=json.dumps({}),
        content_type="application/json",
        headers=headers,
    )


def _heartbeat(client, session_id):
    return client.post(
        "/api/auth/heartbeat",
        data=json.dumps({}),
        content_type="application/json",
        headers={"Authorization": f"Bearer {session_id}"},
    )


def _backdate_session(adb, sid, iso_ts):
    conn = sqlite3.connect(adb.DB_PATH)
    try:
        conn.execute(
            "UPDATE live_sessions SET last_seen = ? WHERE session_id = ?",
            (iso_ts, sid),
        )
        conn.commit()
    finally:
        conn.close()


# ============================================================
# Logout tests
# ============================================================

# Test 1 — Valid Bearer → logout succeeds
def test_valid_logout_succeeds(auth_client):
    client, adb = auth_client
    _seed(adb, 1)
    sid = _login(client, "lo_0000", _pw(0)).get_json()["sessionId"]
    res = _logout(client, session_id=sid)
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert data["status"] == "signed_out"


# Test 2 — Logout revokes the correct session
def test_logout_revokes_session(auth_client):
    client, adb = auth_client
    _seed(adb, 1)
    sid = _login(client, "lo_0000", _pw(0)).get_json()["sessionId"]
    _logout(client, session_id=sid)
    row = adb.get_live_session(sid)
    assert row["status"] == adb.LIVE_SESSION_STATUS_REVOKED


# Test 3 — Revoked session is no longer active
def test_revoked_session_excluded_from_active(auth_client):
    client, adb = auth_client
    _seed(adb, 2)
    sids = [
        _login(client, "lo_0000", _pw(0)).get_json()["sessionId"],
        _login(client, "lo_0001", _pw(1)).get_json()["sessionId"],
    ]
    _logout(client, session_id=sids[0])
    active = adb.list_active_sessions()
    assert all(r["session_id"] != sids[0] for r in active)
    assert any(r["session_id"] == sids[1] for r in active)


# Test 4 — Missing Authorization → rejected
def test_logout_missing_auth_rejected(auth_client):
    client, adb = auth_client
    res = _logout(client, omit_auth=True)
    assert res.status_code == 401
    assert res.get_json()["ok"] is False


# Test 5 — Malformed Authorization → rejected
@pytest.mark.parametrize("bad", ["", "Bearer", "Bearer ", "Token abc", "abc"])
def test_logout_malformed_auth_rejected(auth_client, bad):
    client, adb = auth_client
    res = _logout(client, header_value=bad)
    assert res.status_code == 401


# Test 6 — Unknown session → rejected
def test_logout_unknown_session_rejected(auth_client):
    client, adb = auth_client
    res = _logout(client, session_id=uuid.uuid4().hex)
    assert res.status_code == 401


# Test 7 — Already-revoked session → handled cleanly
def test_logout_already_revoked(auth_client):
    client, adb = auth_client
    _seed(adb, 1)
    sid = _login(client, "lo_0000", _pw(0)).get_json()["sessionId"]
    assert adb.revoke_live_session(sid) is True
    res = _logout(client, session_id=sid)
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert data["status"] == "already_signed_out"


# Test 8 — ?token=<sid> query string does NOT authenticate
def test_logout_query_string_token_rejected(auth_client):
    client, adb = auth_client
    _seed(adb, 1)
    sid = _login(client, "lo_0000", _pw(0)).get_json()["sessionId"]
    res = client.post(
        f"/api/auth/logout?token={sid}",
        data=json.dumps({}),
        content_type="application/json",
        headers={"Authorization": ""},
    )
    assert res.status_code in (400, 401)
    assert res.get_json()["ok"] is False
    # Session should still be active (logout did not succeed)
    row = adb.get_live_session(sid)
    assert row["status"] == adb.LIVE_SESSION_STATUS_ACTIVE


# Test 9 — Session ID is not echoed back
def test_logout_does_not_expose_session_id(auth_client):
    client, adb = auth_client
    _seed(adb, 1)
    sid = _login(client, "lo_0000", _pw(0)).get_json()["sessionId"]
    res = _logout(client, session_id=sid)
    body = res.get_data(as_text=True)
    data = res.get_json()
    assert sid not in body
    for forbidden in ("sessionId", "session_id", "token"):
        assert forbidden not in data


# Test 10 — Two sessions, logout one, other remains active
def test_logout_one_session_leaves_other_active(auth_client):
    client, adb = auth_client
    _seed(adb, 1)
    s1 = _login(client, "lo_0000", _pw(0)).get_json()["sessionId"]
    s2 = _login(client, "lo_0000", _pw(0)).get_json()["sessionId"]
    assert s1 != s2
    _logout(client, session_id=s1)
    assert adb.get_live_session(s1)["status"] == adb.LIVE_SESSION_STATUS_REVOKED
    assert adb.get_live_session(s2)["status"] == adb.LIVE_SESSION_STATUS_ACTIVE
    active = {r["session_id"] for r in adb.list_active_sessions()}
    assert s1 not in active
    assert s2 in active


# ============================================================
# Expiration tests
# ============================================================

# Test 11 — Fresh session is classified active
def test_fresh_session_is_active(auth_client):
    client, adb = auth_client
    _seed(adb, 1)
    sid = _login(client, "lo_0000", _pw(0)).get_json()["sessionId"]
    from backend.routes.auth_routes import live_session_status
    assert live_session_status(adb.get_live_session(sid)) == adb.LIVE_SESSION_STATUS_ACTIVE
    assert any(r["session_id"] == sid for r in adb.list_active_sessions())


# Test 12 — Session older than configured timeout → inactive
def test_old_session_classified_expired(auth_client):
    client, adb = auth_client
    _seed(adb, 1)
    sid = _login(client, "lo_0000", _pw(0)).get_json()["sessionId"]
    # Backdate last_seen to 1 hour ago
    from datetime import datetime, timedelta
    old_ts = (datetime.utcnow() - timedelta(hours=1)).isoformat()
    _backdate_session(adb, sid, old_ts)
    from backend.routes.auth_routes import live_session_status
    assert live_session_status(adb.get_live_session(sid)) == "expired"


# Test 13 — Expired session excluded from active-session queries
def test_expired_session_excluded_from_active_queries(auth_client):
    client, adb = auth_client
    _seed(adb, 2)
    fresh = _login(client, "lo_0000", _pw(0)).get_json()["sessionId"]
    old = _login(client, "lo_0001", _pw(1)).get_json()["sessionId"]
    from datetime import datetime, timedelta
    old_ts = (datetime.utcnow() - timedelta(hours=1)).isoformat()
    _backdate_session(adb, old, old_ts)
    active_sids = {r["session_id"] for r in adb.list_active_sessions()}
    assert fresh in active_sids
    assert old not in active_sids


# Test 14 — Timeout configuration is respected
def test_timeout_configuration_respected(monkeypatch, tmp_path):
    """Set the timeout via env var and verify list_active_sessions
    honours it without any hard-coded number."""
    import importlib
    monkeypatch.setenv("LIVE_SESSION_TIMEOUT_SECONDS", "5")
    import backend.database.accounts_db as adb_real
    importlib.reload(adb_real)  # pick up the new env value
    monkeypatch.setattr(adb_real, "DB_PATH", str(tmp_path / "cfg.db"))
    if (tmp_path / "cfg.db").exists():
        (tmp_path / "cfg.db").unlink()
    adb_real.init_db()
    assert adb_real.LIVE_SESSION_TIMEOUT_SECONDS == 5

    # A fresh session is active
    row = adb_real.create_live_session("cfg-sid-fresh", "anyone")
    sid = row["session_id"]
    assert any(r["session_id"] == sid for r in adb_real.list_active_sessions())

    # A session backdated beyond the timeout is NOT active
    from datetime import datetime, timedelta
    old_row = adb_real.create_live_session("cfg-sid-old", "anyone")
    old_sid = old_row["session_id"]
    conn = sqlite3.connect(adb_real.DB_PATH)
    try:
        conn.execute(
            "UPDATE live_sessions SET last_seen = ? WHERE session_id = ?",
            ((datetime.utcnow() - timedelta(seconds=10)).isoformat(), old_sid),
        )
        conn.commit()
    finally:
        conn.close()
    active_sids = {r["session_id"] for r in adb_real.list_active_sessions()}
    assert old_sid not in active_sids


# Test 15 — Heartbeat cannot resurrect an expired session
def test_heartbeat_rejects_expired_session(auth_client):
    client, adb = auth_client
    _seed(adb, 1)
    sid = _login(client, "lo_0000", _pw(0)).get_json()["sessionId"]
    from datetime import datetime, timedelta
    old_ts = (datetime.utcnow() - timedelta(hours=1)).isoformat()
    _backdate_session(adb, sid, old_ts)
    res = _heartbeat(client, sid)
    assert res.status_code == 401
    assert res.get_json()["ok"] is False
    # Side-effect: expired session is now revoked (so it cannot drift
    # back into active state)
    row = adb.get_live_session(sid)
    assert row["status"] == adb.LIVE_SESSION_STATUS_REVOKED


# ============================================================
# N-user parametrised logout + expiration
# ============================================================

@pytest.mark.parametrize("n", [1, 10, 70, 100, 200])
def test_n_users_logout_and_active_filtering(auth_client, n):
    client, adb = auth_client
    usernames = _seed(adb, n)
    sids = []
    for i, u in enumerate(usernames):
        sids.append(_login(client, u, _pw(i)).get_json()["sessionId"])
    assert len(set(sids)) == n

    # Before logout: all sessions active
    assert len(adb.list_active_sessions()) == n

    # Log out every other session; the remaining ones must stay active
    revoked = []
    kept = []
    for i, sid in enumerate(sids):
        if i % 2 == 0:
            res = _logout(client, session_id=sid)
            assert res.status_code == 200
            assert res.get_json()["ok"] is True
            revoked.append(sid)
        else:
            kept.append(sid)

    active_sids = {r["session_id"] for r in adb.list_active_sessions()}
    # All revoked sessions are excluded
    assert not (active_sids & set(revoked))
    # All kept sessions are still active
    assert set(kept).issubset(active_sids)
    assert len(active_sids) == len(kept)


@pytest.mark.parametrize("n", [1, 10, 70, 100])
def test_n_users_expiration_excludes_old_sessions(auth_client, n):
    client, adb = auth_client
    usernames = _seed(adb, n)
    sids = []
    for i, u in enumerate(usernames):
        sids.append(_login(client, u, _pw(i)).get_json()["sessionId"])

    # Backdate the first half to be expired
    from datetime import datetime, timedelta
    old_ts = (datetime.utcnow() - timedelta(hours=1)).isoformat()
    expired_sids = sids[: n // 2]
    fresh_sids = sids[n // 2 :]
    for sid in expired_sids:
        _backdate_session(adb, sid, old_ts)

    active_sids = {r["session_id"] for r in adb.list_active_sessions()}
    assert not (active_sids & set(expired_sids))
    assert set(fresh_sids).issubset(active_sids)
    assert len(active_sids) == len(fresh_sids)