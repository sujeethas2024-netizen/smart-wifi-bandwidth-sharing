"""
Tests for the authenticated live-session heartbeat endpoint.

POST /api/auth/heartbeat
Authorization: Bearer <sessionId>

Verifies:
* Valid Bearer + valid session → success, last_seen updated.
* Missing / malformed Authorization → 401.
* Invalid session ID → 401.
* Revoked session → 401.
* Session ID is NOT echoed back.
* Multiple sessions for the same user are updated independently.
* N-user parametrised heartbeat works dynamically.
"""

import importlib.util
import json
import os
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
    return f"Hb@Pass{i:04d}1"


def _seed(adb, count: int):
    usernames = []
    for i in range(count):
        uname = f"hb_{i:04d}"
        ok, _ = adb.create_account(
            username=uname,
            password=_pw(i),
            full_name=f"HB User {i}",
            role="user",
            usage_reason="Online Classes / Study",
        )
        assert ok, f"failed to seed {uname}"
        usernames.append(uname)
    return usernames


@pytest.fixture
def auth_client(monkeypatch):
    """Wire the Flask app against an isolated SQLite DB.

    Reuses the same pattern as test_login_session_integration.py:
    import a private copy of accounts_db against a temp file, then
    rebind the auth_routes module to use those helpers.
    """
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
    auth_routes.LIVE_SESSION_STATUS_ACTIVE = adb.LIVE_SESSION_STATUS_ACTIVE
    auth_routes.LIVE_SESSION_STATUS_REVOKED = adb.LIVE_SESSION_STATUS_REVOKED

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


def _heartbeat(client, session_id=None, header_value=None, omit_auth=False):
    headers = {}
    if not omit_auth:
        if header_value is not None:
            headers["Authorization"] = header_value
        elif session_id is not None:
            headers["Authorization"] = f"Bearer {session_id}"
    return client.post(
        "/api/auth/heartbeat",
        data=json.dumps({}),
        content_type="application/json",
        headers=headers,
    )


# -------------------------------------------------------------------
# Test 1 — Valid Bearer + valid session → success
# -------------------------------------------------------------------
def test_valid_heartbeat_succeeds(auth_client):
    client, adb = auth_client
    _seed(adb, 1)
    login_res = _login(client, "hb_0000", _pw(0))
    sid = login_res.get_json()["sessionId"]
    res = _heartbeat(client, session_id=sid)
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert data["status"] == "online"
    assert "lastSeen" in data and data["lastSeen"]


# -------------------------------------------------------------------
# Test 2 — last_seen is updated
# -------------------------------------------------------------------
def test_heartbeat_updates_last_seen(auth_client):
    client, adb = auth_client
    _seed(adb, 1)
    login_res = _login(client, "hb_0000", _pw(0))
    sid = login_res.get_json()["sessionId"]
    before_row = adb.get_live_session(sid)
    before = before_row["last_seen"]
    time.sleep(0.02)
    res = _heartbeat(client, session_id=sid)
    assert res.status_code == 200
    after_row = adb.get_live_session(sid)
    assert after_row["last_seen"] > before
    # Response lastSeen must reflect the freshly-touched value
    assert res.get_json()["lastSeen"] == after_row["last_seen"]


# -------------------------------------------------------------------
# Test 3 — Missing Authorization → rejected
# -------------------------------------------------------------------
def test_missing_authorization_rejected(auth_client):
    client, adb = auth_client
    _seed(adb, 1)
    res = _heartbeat(client, omit_auth=True)
    assert res.status_code == 401
    assert res.get_json()["ok"] is False


# -------------------------------------------------------------------
# Test 4 — Malformed Authorization → rejected
# -------------------------------------------------------------------
@pytest.mark.parametrize("bad_header", [
    "",                       # empty
    "Bearer",                 # missing token
    "Bearer ",                # blank token
    "Token abc",              # wrong scheme
    "abc",                    # no scheme at all
    "Basic abc",              # non-Bearer
])
def test_malformed_authorization_rejected(auth_client, bad_header):
    client, adb = auth_client
    _seed(adb, 1)
    res = _heartbeat(client, header_value=bad_header)
    assert res.status_code == 401
    assert res.get_json()["ok"] is False


# -------------------------------------------------------------------
# Test 5 — Invalid session ID → rejected
# -------------------------------------------------------------------
def test_invalid_session_id_rejected(auth_client):
    client, adb = auth_client
    _seed(adb, 1)
    fake_sid = uuid.uuid4().hex
    res = _heartbeat(client, session_id=fake_sid)
    assert res.status_code == 401
    assert res.get_json()["ok"] is False
    # No row created as a side-effect
    assert adb.get_live_session(fake_sid) is None


# -------------------------------------------------------------------
# Test 6 — Revoked session → rejected
# -------------------------------------------------------------------
def test_revoked_session_rejected(auth_client):
    client, adb = auth_client
    _seed(adb, 1)
    sid = _login(client, "hb_0000", _pw(0)).get_json()["sessionId"]
    assert adb.revoke_live_session(sid) is True
    res = _heartbeat(client, session_id=sid)
    assert res.status_code == 401
    assert res.get_json()["ok"] is False


# -------------------------------------------------------------------
# Test 7 — Session ID is NOT returned by heartbeat
# -------------------------------------------------------------------
def test_heartbeat_does_not_expose_session_id(auth_client):
    client, adb = auth_client
    _seed(adb, 1)
    sid = _login(client, "hb_0000", _pw(0)).get_json()["sessionId"]
    res = _heartbeat(client, session_id=sid)
    body = res.get_data(as_text=True)
    data = res.get_json()
    # The token itself must never appear in the body
    assert sid not in body
    # And no key commonly used to hold it
    for forbidden in ("sessionId", "session_id", "token"):
        assert forbidden not in data
    # Only ok / status / lastSeen should be present
    assert set(data.keys()).issubset({"ok", "status", "lastSeen"})


# -------------------------------------------------------------------
# Test 8 — Multiple sessions for one user remain independent
# -------------------------------------------------------------------
def test_multiple_sessions_updated_independently(auth_client):
    client, adb = auth_client
    _seed(adb, 1)
    # Same user logs in twice → two distinct sessions
    s1 = _login(client, "hb_0000", _pw(0)).get_json()["sessionId"]
    s2 = _login(client, "hb_0000", _pw(0)).get_json()["sessionId"]
    assert s1 != s2

    before1 = adb.get_live_session(s1)["last_seen"]
    before2 = adb.get_live_session(s2)["last_seen"]

    time.sleep(0.02)
    # Heartbeat only session 1
    res = _heartbeat(client, session_id=s1)
    assert res.status_code == 200

    after1 = adb.get_live_session(s1)["last_seen"]
    after2 = adb.get_live_session(s2)["last_seen"]
    assert after1 > before1, "A1 must be updated"
    assert after2 == before2, "A2 must be untouched"


# -------------------------------------------------------------------
# Test 9 — N-user parametrised heartbeat (N=1,10,70,100,200)
# -------------------------------------------------------------------
@pytest.mark.parametrize("n", [1, 10, 70, 100, 200])
def test_n_users_heartbeat_updates_each_session(auth_client, n):
    client, adb = auth_client
    usernames = _seed(adb, n)
    sids = []
    for i, u in enumerate(usernames):
        sids.append(_login(client, u, _pw(i)).get_json()["sessionId"])
    assert len(set(sids)) == n

    # Capture before
    before = {sid: adb.get_live_session(sid)["last_seen"] for sid in sids}
    time.sleep(0.05)

    # Heartbeat every session
    statuses = []
    for sid in sids:
        res = _heartbeat(client, session_id=sid)
        statuses.append(res.status_code)
        assert res.status_code == 200
        data = res.get_json()
        assert data["ok"] is True
        assert data["status"] == "online"

    assert all(s == 200 for s in statuses)

    # After: every session's last_seen must have advanced
    for sid in sids:
        after = adb.get_live_session(sid)["last_seen"]
        assert after > before[sid], f"session {sid[:8]} was not updated"


# -------------------------------------------------------------------
# Bonus — ?token= query string is NEVER accepted
# -------------------------------------------------------------------
def test_query_string_token_is_rejected(auth_client):
    client, adb = auth_client
    _seed(adb, 1)
    sid = _login(client, "hb_0000", _pw(0)).get_json()["sessionId"]
    res = client.post(
        f"/api/auth/heartbeat?token={sid}",
        data=json.dumps({}),
        content_type="application/json",
        headers={"Authorization": ""},  # explicitly no header
    )
    # Either the header is missing (401) or, at minimum, the endpoint
    # does not validate via query string. The session ID must NOT be
    # considered authenticated by URL alone.
    assert res.status_code in (401, 400)
    assert res.get_json()["ok"] is False


# -------------------------------------------------------------------
# Bonus — Two heartbeats in succession update last_seen monotonically
# -------------------------------------------------------------------
def test_repeated_heartbeats_advance_last_seen(auth_client):
    client, adb = auth_client
    _seed(adb, 1)
    sid = _login(client, "hb_0000", _pw(0)).get_json()["sessionId"]
    timestamps = []
    for _ in range(3):
        time.sleep(0.01)
        res = _heartbeat(client, session_id=sid)
        timestamps.append(res.get_json()["lastSeen"])
    # Monotonic non-decreasing
    assert timestamps == sorted(timestamps)
    assert len(set(timestamps)) >= 2  # at least 2 distinct values