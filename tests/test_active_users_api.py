"""
Tests for GET /api/auth/active-users — the server-authoritative
active-logged-in-users endpoint.

Verifies:
* Missing Authorization → 401.
* One active user is returned correctly.
* Multiple active users are returned.
* N-user parametrised tests for N=1, 10, 70, 100, 200.
* Expired sessions are excluded.
* Revoked sessions are excluded.
* Response does not expose session_id.
* Response does not expose passwords / hashes / salts.
* ?username= cannot fabricate identity or authenticate.
* Duplicate sessions for the same user are deduplicated.
* No hardcoded 70-user logic.
"""

import importlib.util
import json
import os
import sqlite3
import sys
import tempfile
import uuid

import pytest


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_PATH = os.path.join(PROJECT_ROOT, "backend")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)


def _pw(i: int = 0) -> str:
    return f"Au@Pass{i:04d}1"


def _seed(adb, count: int):
    usernames = []
    for i in range(count):
        uname = f"au_{i:04d}"
        ok, _ = adb.create_account(
            username=uname,
            password=_pw(i),
            full_name=f"AU User {i}",
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


def _active_users(client, session_id=None, header_value=None, omit_auth=False,
                  query_string=""):
    headers = {}
    if not omit_auth:
        if header_value is not None:
            headers["Authorization"] = header_value
        elif session_id is not None:
            headers["Authorization"] = f"Bearer {session_id}"
    return client.get(
        f"/api/auth/active-users{query_string}",
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
# Test 1 — Zero active users (unauthenticated) → 401
# ============================================================
def test_no_auth_rejected(auth_client):
    """Without a valid session token the endpoint must reject access."""
    client, adb = auth_client
    res = _active_users(client, omit_auth=True)
    assert res.status_code == 401
    assert res.get_json()["ok"] is False


# ============================================================
# Test 2 — One active user
# ============================================================
def test_one_active_user(auth_client):
    client, adb = auth_client
    _seed(adb, 1)
    sid = _login(client, "au_0000", _pw(0)).get_json()["sessionId"]
    res = _active_users(client, session_id=sid)
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert data["count"] == 1
    assert len(data["users"]) == 1
    u = data["users"][0]
    assert u["username"] == "au_0000"
    assert u["fullName"] == "AU User 0"
    assert u["role"] == "user"
    assert "lastSeen" in u and u["lastSeen"]


# ============================================================
# Test 3 — Multiple active users
# ============================================================
def test_multiple_active_users(auth_client):
    client, adb = auth_client
    _seed(adb, 3)
    sids = [
        _login(client, f"au_{i:04d}", _pw(i)).get_json()["sessionId"]
        for i in range(3)
    ]
    res = _active_users(client, session_id=sids[0])
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert data["count"] == 3
    usernames = {u["username"] for u in data["users"]}
    assert usernames == {"au_0000", "au_0001", "au_0002"}
    for u in data["users"]:
        assert "fullName" in u
        assert "role" in u
        assert "lastSeen" in u


# ============================================================
# Test 4–7 — N-user parametrised (N=1, 10, 70, 100, 200)
# ============================================================
@pytest.mark.parametrize("n", [1, 10, 70, 100, 200])
def test_n_users_active_count(auth_client, n):
    client, adb = auth_client
    usernames = _seed(adb, n)
    sids = [
        _login(client, u, _pw(i)).get_json()["sessionId"]
        for i, u in enumerate(usernames)
    ]
    assert len(set(sids)) == n

    res = _active_users(client, session_id=sids[0])
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert data["count"] == n
    assert len(data["users"]) == n
    returned = {u["username"] for u in data["users"]}
    assert returned == set(usernames)


# ============================================================
# Test 8 — Expired sessions are excluded
# ============================================================
def test_expired_session_excluded(auth_client):
    client, adb = auth_client
    _seed(adb, 2)
    # User 0 logs in and then "expires"
    sid0 = _login(client, "au_0000", _pw(0)).get_json()["sessionId"]
    from datetime import datetime, timedelta
    old_ts = (datetime.utcnow() - timedelta(hours=1)).isoformat()
    _backdate(adb, sid0, old_ts)
    # User 1 logs in fresh and calls the endpoint
    sid1 = _login(client, "au_0001", _pw(1)).get_json()["sessionId"]
    res = _active_users(client, session_id=sid1)
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert data["count"] == 1  # only au_0001 is active
    assert data["users"][0]["username"] == "au_0001"


# ============================================================
# Test 9 — Revoked sessions are excluded
# ============================================================
def test_revoked_session_excluded(auth_client):
    client, adb = auth_client
    _seed(adb, 2)
    sid0 = _login(client, "au_0000", _pw(0)).get_json()["sessionId"]
    assert adb.revoke_live_session(sid0) is True
    sid1 = _login(client, "au_0001", _pw(1)).get_json()["sessionId"]
    res = _active_users(client, session_id=sid1)
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert data["count"] == 1  # only au_0001 is active
    assert data["users"][0]["username"] == "au_0001"


# ============================================================
# Test 10 — Response does not expose session_id
# ============================================================
def test_response_does_not_expose_session_id(auth_client):
    client, adb = auth_client
    _seed(adb, 2)
    sids = [
        _login(client, f"au_{i:04d}", _pw(i)).get_json()["sessionId"]
        for i in range(2)
    ]
    res = _active_users(client, session_id=sids[0])
    body = res.get_data(as_text=True)
    data = res.get_json()
    for forbidden in ("sessionId", "session_id", "token", "session_token"):
        assert forbidden not in body, (
            f"response body leaked key '{forbidden}'"
        )
    assert set(data.keys()).issubset({"ok", "count", "users"})
    for u in data["users"]:
        assert set(u.keys()).issubset(
            {"username", "fullName", "role", "lastSeen"}
        )


# ============================================================
# Test 11 — Response does not expose passwords / hashes / salts
# ============================================================
def test_response_does_not_expose_secrets(auth_client):
    client, adb = auth_client
    _seed(adb, 1)
    sid = _login(client, "au_0000", _pw(0)).get_json()["sessionId"]
    res = _active_users(client, session_id=sid)
    body = res.get_data(as_text=True)
    for forbidden in (
        "password", "passHash", "password_hash", "salt",
        "passwordHash", _pw(0),
    ):
        assert forbidden.lower() not in body.lower(), (
            f"response body leaked secret '{forbidden}'"
        )
    data = res.get_json()
    assert "password" not in str(data).lower().replace("usageReason", "")


# ============================================================
# Test 12 — ?username= cannot authenticate
# ============================================================
@pytest.mark.parametrize("qs", [
    "?username=admin",
    "?username=au_0000&role=admin",
    "?role=admin",
])
def test_query_string_cannot_authenticate(auth_client, qs):
    client, adb = auth_client
    _seed(adb, 1)
    res = _active_users(client, query_string=qs)
    assert res.status_code == 401
    assert res.get_json()["ok"] is False


# ============================================================
# Test 13 — Duplicate sessions for same user are deduplicated
# ============================================================
def test_duplicate_sessions_deduplicated(auth_client):
    client, adb = auth_client
    _seed(adb, 2)
    # User 0 logs in twice → two distinct sessions
    s1 = _login(client, "au_0000", _pw(0)).get_json()["sessionId"]
    s2 = _login(client, "au_0000", _pw(0)).get_json()["sessionId"]
    assert s1 != s2
    # User 1 logs in → one session
    s3 = _login(client, "au_0001", _pw(1)).get_json()["sessionId"]

    res = _active_users(client, session_id=s3)
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    # Two unique users, even though au_0000 has two sessions
    assert data["count"] == 2
    usernames = {u["username"] for u in data["users"]}
    assert usernames == {"au_0000", "au_0001"}


# ============================================================
# Bonus — Expired caller is rejected
# ============================================================
def test_expired_caller_rejected(auth_client):
    client, adb = auth_client
    _seed(adb, 1)
    sid = _login(client, "au_0000", _pw(0)).get_json()["sessionId"]
    from datetime import datetime, timedelta
    old_ts = (datetime.utcnow() - timedelta(hours=1)).isoformat()
    _backdate(adb, sid, old_ts)
    res = _active_users(client, session_id=sid)
    assert res.status_code == 401
    assert res.get_json()["ok"] is False


# ============================================================
# Bonus — Revoked caller is rejected
# ============================================================
def test_revoked_caller_rejected(auth_client):
    client, adb = auth_client
    _seed(adb, 1)
    sid = _login(client, "au_0000", _pw(0)).get_json()["sessionId"]
    adb.revoke_live_session(sid)
    res = _active_users(client, session_id=sid)
    assert res.status_code == 401
    assert res.get_json()["ok"] is False
