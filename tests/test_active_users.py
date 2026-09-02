"""
Tests for GET /api/auth/active — the internal active-users endpoint.

Verifies:
* Successful response shape.
* Fresh active sessions appear.
* Expired / revoked sessions are excluded.
* Active counts are correct.
* Unique-user count works across multiple sessions.
* Session tokens / passwords / hashes are never exposed.
* ?username= cannot fabricate identity.
* N-user parametrised tests for N=1, 10, 70, 100, 200.
* Mixed active / expired / revoked sessions filtered correctly.
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
    return f"Ac@Pass{i:04d}1"


def _seed(adb, count: int):
    usernames = []
    for i in range(count):
        uname = f"ac_{i:04d}"
        ok, _ = adb.create_account(
            username=uname,
            password=_pw(i),
            full_name=f"AC User {i}",
            role="user",
            usage_reason="Online Classes / Study",
        )
        assert ok, f"failed to seed {uname}"
        usernames.append(uname)
    return usernames


@pytest.fixture
def auth_client(monkeypatch):
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
    auth_routes.list_active_sessions = adb.list_active_sessions
    auth_routes.public_live_session = adb.public_live_session
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


def _active(client, session_id=None, header_value=None,
             omit_auth=False, query_string=""):
    headers = {}
    if not omit_auth:
        if header_value is not None:
            headers["Authorization"] = header_value
        elif session_id is not None:
            headers["Authorization"] = f"Bearer {session_id}"
    return client.get(
        f"/api/auth/active{query_string}",
        headers=headers,
    )


def _backdate(adb, sid, iso_ts):
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
# Test 1 — Endpoint returns a successful response
# ============================================================
def test_active_endpoint_returns_success(auth_client):
    client, adb = auth_client
    _seed(adb, 1)
    sid = _login(client, "ac_0000", _pw(0)).get_json()["sessionId"]
    res = _active(client, session_id=sid)
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert "sessions" in data
    assert "activeSessionCount" in data
    assert "activeUserCount" in data
    assert "timeoutSeconds" in data


# ============================================================
# Test 2 — Fresh active session appears
# ============================================================
def test_fresh_session_appears(auth_client):
    client, adb = auth_client
    _seed(adb, 1)
    sid = _login(client, "ac_0000", _pw(0)).get_json()["sessionId"]
    res = _active(client, session_id=sid)
    data = res.get_json()
    assert data["activeSessionCount"] == 1
    assert data["activeUserCount"] == 1
    s = data["sessions"][0]
    assert s["username"] == "ac_0000"
    assert s["status"] == "active"


# ============================================================
# Test 3 — Expired session does not appear
# ============================================================
def test_expired_session_excluded(auth_client):
    client, adb = auth_client
    _seed(adb, 2)  # ac_0000, ac_0001
    sid = _login(client, "ac_0000", _pw(0)).get_json()["sessionId"]
    from datetime import datetime, timedelta
    _backdate(adb, sid, (datetime.utcnow() - timedelta(hours=1)).isoformat())
    res = _active(client, session_id=sid)
    # Caller's own session is expired -> 401
    assert res.status_code == 401
    # /active with a fresh caller: the expired one must not appear
    caller_sid = _login(client, "ac_0001", _pw(1)).get_json()["sessionId"]
    res2 = _active(client, session_id=caller_sid)
    data = res2.get_json()
    assert all(s["username"] != "ac_0000" for s in data["sessions"])
    # Only the fresh caller is active
    assert data["activeSessionCount"] == 1
    assert data["activeUserCount"] == 1


# ============================================================
# Test 4 — Revoked session does not appear
# ============================================================
def test_revoked_session_excluded(auth_client):
    client, adb = auth_client
    _seed(adb, 2)
    _login(client, "ac_0000", _pw(0))  # this user's session will be revoked
    caller = _login(client, "ac_0001", _pw(1)).get_json()["sessionId"]
    # Revoke any active session belonging to ac_0000
    target = None
    for row in adb.list_active_sessions():
        if row["username"] == "ac_0000":
            target = row["session_id"]
            break
    assert target is not None
    assert adb.revoke_live_session(target) is True
    res = _active(client, session_id=caller)
    data = res.get_json()
    assert all(s["username"] != "ac_0000" for s in data["sessions"])


# ============================================================
# Test 5 — Active count is correct
# ============================================================
@pytest.mark.parametrize("n", [1, 3, 5, 12])
def test_active_counts_correct(auth_client, n):
    client, adb = auth_client
    _seed(adb, n + 1)
    sids = []
    for i in range(n):
        sids.append(_login(client, f"ac_{i:04d}", _pw(i)).get_json()["sessionId"])
    # caller (ac_<n>) will not count toward the n reported
    caller = _login(client, f"ac_{n:04d}", _pw(n)).get_json()["sessionId"]
    res = _active(client, session_id=caller)
    data = res.get_json()
    assert data["activeSessionCount"] == n + 1
    assert data["activeUserCount"] == n + 1


# ============================================================
# Test 6 — Unique user count across multiple sessions
# ============================================================
def test_unique_user_count_with_multi_sessions(auth_client):
    client, adb = auth_client
    _seed(adb, 3)  # ac_0000, ac_0001, ac_0002
    # Alice -> A1, A2
    a1 = _login(client, "ac_0000", _pw(0)).get_json()["sessionId"]
    a2 = _login(client, "ac_0000", _pw(0)).get_json()["sessionId"]
    # Bob -> B1
    b1 = _login(client, "ac_0001", _pw(1)).get_json()["sessionId"]
    # Charlie (caller)
    caller = _login(client, "ac_0002", _pw(2)).get_json()["sessionId"]
    res = _active(client, session_id=caller)
    data = res.get_json()
    # 3 active sessions (A1, A2, B1) + caller = 4
    assert data["activeSessionCount"] == 4
    # Unique users: ac_0000, ac_0001, ac_0002 = 3
    assert data["activeUserCount"] == 3


# ============================================================
# Test 7 — Session IDs / tokens are NOT exposed in response
# ============================================================
def test_session_id_not_exposed(auth_client):
    client, adb = auth_client
    _seed(adb, 2)
    sid = _login(client, "ac_0000", _pw(0)).get_json()["sessionId"]
    other = _login(client, "ac_0001", _pw(1)).get_json()["sessionId"]
    res = _active(client, session_id=sid)
    body = res.get_data(as_text=True)
    data = res.get_json()
    # Neither the caller's token NOR any other session's bearer token
    # may appear anywhere in the body.
    assert sid not in body
    assert other not in body
    for s in data["sessions"]:
        for forbidden in ("session_id", "sessionId", "token", "password",
                          "password_hash", "salt", "passHash", "passwordHash"):
            assert forbidden not in s
        # Only safe keys are present
        assert set(s.keys()).issubset({
            "username", "createdAt", "lastSeen", "status", "id"
        })


# ============================================================
# Test 8 — Password / hash / salt NOT exposed
# ============================================================
def test_no_password_or_hash_in_response(auth_client):
    client, adb = auth_client
    _seed(adb, 2)
    sids = [
        _login(client, "ac_0000", _pw(0)).get_json()["sessionId"],
        _login(client, "ac_0001", _pw(1)).get_json()["sessionId"],
    ]
    res = _active(client, session_id=sids[0])
    body = res.get_data(as_text=True)
    for forbidden in ("password", "passHash", "passwordHash",
                      "password_hash", "salt",
                      _pw(0), _pw(1),
                      "Ac@Pass00001", "Ac@Pass00011"):
        assert forbidden not in body


# ============================================================
# Test 9 — ?username= cannot fabricate identity
# ============================================================
@pytest.mark.parametrize("qs", [
    "?username=admin",
    "?username=ac_0001&role=admin",
    "?role=admin",
])
def test_query_string_cannot_authenticate(auth_client, qs):
    client, adb = auth_client
    _seed(adb, 2)
    # Some random valid-looking session ID in the URL must NOT help
    res = _active(client, query_string=qs)
    assert res.status_code == 401
    assert res.get_json()["ok"] is False


# ============================================================
# Test 10 — N-user dynamic test
# ============================================================
@pytest.mark.parametrize("n", [1, 10, 70, 100, 200])
def test_n_users_active_counts(auth_client, n):
    client, adb = auth_client
    usernames = _seed(adb, n + 1)
    sids = []
    for i in range(n):
        sids.append(_login(client, usernames[i], _pw(i)).get_json()["sessionId"])
    caller = _login(client, usernames[n], _pw(n)).get_json()["sessionId"]
    res = _active(client, session_id=caller)
    data = res.get_json()
    assert data["activeSessionCount"] == n + 1
    assert data["activeUserCount"] == n + 1
    # Bearer tokens must NOT leak into the response
    body = res.get_data(as_text=True)
    for sid in sids + [caller]:
        assert sid not in body
    # Exactly n+1 session entries with unique ids
    ids = [s["id"] for s in data["sessions"]]
    assert len(ids) == n + 1
    assert len(set(ids)) == n + 1


# ============================================================
# Test 11 — Mixed active / expired / revoked filtered correctly
# ============================================================
def test_mixed_states_filtered(auth_client):
    client, adb = auth_client
    _seed(adb, 5)  # ac_0000 .. ac_0004
    active1 = _login(client, "ac_0000", _pw(0)).get_json()["sessionId"]
    active2 = _login(client, "ac_0001", _pw(1)).get_json()["sessionId"]
    revoked = _login(client, "ac_0002", _pw(2)).get_json()["sessionId"]
    expired = _login(client, "ac_0003", _pw(3)).get_json()["sessionId"]
    adb.revoke_live_session(revoked)
    from datetime import datetime, timedelta
    _backdate(adb, expired, (datetime.utcnow() - timedelta(hours=1)).isoformat())
    # ac_0004 = caller, not expired/revoked
    caller = _login(client, "ac_0004", _pw(4)).get_json()["sessionId"]
    res = _active(client, session_id=caller)
    data = res.get_json()
    # active1, active2, caller (ac_0000/1/4) = 3 sessions, 3 unique users
    assert data["activeSessionCount"] == 3
    assert data["activeUserCount"] == 3
    returned_usernames = {s["username"] for s in data["sessions"]}
    assert {"ac_0000", "ac_0001", "ac_0004"} == returned_usernames
    # Revoked / expired must be absent
    assert all(s["username"] not in ("ac_0002", "ac_0003")
               for s in data["sessions"])


# ============================================================
# Bonus — Missing / malformed Authorization rejected
# ============================================================
def test_missing_auth_rejected(auth_client):
    client, adb = auth_client
    res = _active(client, omit_auth=True)
    assert res.status_code == 401


@pytest.mark.parametrize("bad", ["", "Bearer", "Token abc", "abc"])
def test_malformed_auth_rejected(auth_client, bad):
    client, adb = auth_client
    res = _active(client, header_value=bad)
    assert res.status_code == 401


def test_unknown_session_rejected(auth_client):
    client, adb = auth_client
    res = _active(client, session_id=uuid.uuid4().hex)
    assert res.status_code == 401


# ============================================================
# Bonus — Caller's own revoked session is rejected
# ============================================================
def test_revoked_caller_rejected(auth_client):
    client, adb = auth_client
    _seed(adb, 1)
    sid = _login(client, "ac_0000", _pw(0)).get_json()["sessionId"]
    adb.revoke_live_session(sid)
    res = _active(client, session_id=sid)
    assert res.status_code == 401