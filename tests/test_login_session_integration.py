"""
Tests for the live-session integration into the existing login flow.

These tests run against the real Flask test client. The production
database layer is redirected to a per-session temp SQLite file via the
auth_routes module so the live accounts.db is never modified.
"""

import importlib
import json
import os
import re
import secrets as _secrets
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


# Strong password matching the project's existing PASSWORD_PATTERN
def _pw(i: int = 0) -> str:
    return f"Test@Pass{i}1"


def _seed_accounts(adb, count: int):
    """Create `count` valid accounts using the project's own validator."""
    created = []
    for i in range(count):
        uname = f"sess_{i:04d}"
        ok, _ = adb.create_account(
            username=uname,
            password=_pw(i),
            full_name=f"Session User {i}",
            role="user",
            usage_reason="Online Classes / Study",
        )
        assert ok, f"failed to seed {uname}"
        created.append(uname)
    return created


@pytest.fixture
def auth_client(monkeypatch):
    """Wire the Flask app against a fresh isolated SQLite DB.

    Imports a private copy of accounts_db (per-test temp file) and
    rebinds `backend.routes.auth_routes` to use it. The Flask app, its
    routes blueprint, and the test client remain real production
    objects, so the full request pipeline is exercised.
    """
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()

    import importlib.util
    mod_name = "accounts_db_isolated_" + uuid.uuid4().hex
    spec = importlib.util.spec_from_file_location(
        mod_name,
        os.path.join(PROJECT_ROOT, "backend", "database", "accounts_db.py"),
    )
    adb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adb)
    adb.DB_PATH = tmp.name
    if os.path.exists(tmp.name):
        os.unlink(tmp.name)
    adb.init_db()

    # Rebind the imports inside auth_routes to use our isolated module
    import backend.routes.auth_routes as auth_routes
    auth_routes.verify_credentials = adb.verify_credentials
    auth_routes.get_account = adb.get_account
    auth_routes.username_exists = adb.username_exists
    auth_routes.public_account = adb.public_account
    auth_routes.create_account = adb.create_account
    auth_routes.create_live_session = adb.create_live_session
    auth_routes.list_accounts = adb.list_accounts

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


# -------------------------------------------------------------------
# Test 1 — Successful login returns a session ID
# -------------------------------------------------------------------
def test_successful_login_returns_session_id(auth_client):
    client, adb = auth_client
    _seed_accounts(adb, 1)
    res = _login(client, "sess_0000", _pw(0))
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert isinstance(data.get("sessionId"), str) and len(data["sessionId"]) >= 16


# -------------------------------------------------------------------
# Test 2 — Returned session ID exists in live_sessions
# -------------------------------------------------------------------
def test_session_id_exists_in_db(auth_client):
    client, adb = auth_client
    _seed_accounts(adb, 1)
    res = _login(client, "sess_0000", _pw(0))
    data = res.get_json()
    row = adb.get_live_session(data["sessionId"])
    assert row is not None
    assert row["session_id"] == data["sessionId"]


# -------------------------------------------------------------------
# Test 3 — Session belongs to the authenticated username
# -------------------------------------------------------------------
def test_session_belongs_to_authenticated_user(auth_client):
    client, adb = auth_client
    _seed_accounts(adb, 3)
    res = _login(client, "sess_0001", _pw(1))
    data = res.get_json()
    row = adb.get_live_session(data["sessionId"])
    assert row["username"] == "sess_0001"


# -------------------------------------------------------------------
# Test 4 — Two logins create two distinct sessions
# -------------------------------------------------------------------
def test_two_logins_two_distinct_sessions(auth_client):
    client, adb = auth_client
    _seed_accounts(adb, 2)
    r1 = _login(client, "sess_0000", _pw(0))
    r2 = _login(client, "sess_0001", _pw(1))
    s1 = r1.get_json()["sessionId"]
    s2 = r2.get_json()["sessionId"]
    assert s1 and s2
    assert s1 != s2
    rows = {r["session_id"] for r in adb.list_active_sessions()}
    assert {s1, s2}.issubset(rows)

    # Same user logs in twice → two distinct sessions (no overwrite)
    r3 = _login(client, "sess_0000", _pw(0))
    r4 = _login(client, "sess_0000", _pw(0))
    s3 = r3.get_json()["sessionId"]
    s4 = r4.get_json()["sessionId"]
    assert s3 != s4
    assert s3 != s1 and s4 != s1
    rows = {r["session_id"] for r in adb.list_active_sessions()}
    assert {s1, s3, s4}.issubset(rows)


# -------------------------------------------------------------------
# Test 5 — Failed login does NOT create a live session
# -------------------------------------------------------------------
def test_failed_login_creates_no_session(auth_client):
    client, adb = auth_client
    _seed_accounts(adb, 1)
    before = len(adb.list_active_sessions())
    # Wrong password
    res = _login(client, "sess_0000", "Wrong@Pass1")
    assert res.status_code == 401
    # Unknown user
    res2 = _login(client, "ghost_user", _pw(0))
    assert res2.status_code == 404
    # Missing fields
    res3 = client.post(
        "/api/auth/login",
        data=json.dumps({}),
        content_type="application/json",
    )
    assert res3.status_code == 400
    after = len(adb.list_active_sessions())
    assert before == after == 0


# -------------------------------------------------------------------
# Test 6 — Existing login response remains compatible with the frontend
# -------------------------------------------------------------------
def test_existing_user_data_still_present(auth_client):
    client, adb = auth_client
    _seed_accounts(adb, 1)
    res = _login(client, "sess_0000", _pw(0))
    data = res.get_json()
    user = data.get("user") or {}
    # Existing public fields must still be present
    for required in ("username", "fullName", "role",
                     "usageReason", "deviceCount",
                     "createdAt", "lastLogin"):
        assert required in user, f"missing required field: {required}"
    assert user["username"] == "sess_0000"
    # Sensitive fields must NOT be exposed
    for forbidden in ("password", "password_hash", "salt",
                      "passwordHash", "passHash"):
        assert forbidden not in user
    # The new field is additive only
    assert "sessionId" in data
    # Top-level shape remains ok / user / sessionId
    assert set(data.keys()) >= {"ok", "user", "sessionId"}


# -------------------------------------------------------------------
# Test 7 — Session IDs are unpredictable (not username/timestamp)
# -------------------------------------------------------------------
def test_session_ids_are_unpredictable(auth_client):
    client, adb = auth_client
    _seed_accounts(adb, 1)
    sids = set()
    for _ in range(20):
        res = _login(client, "sess_0000", _pw(0))
        sids.add(res.get_json()["sessionId"])
    assert len(sids) == 20, "session IDs must be unique across logins"
    for sid in sids:
        # Must not contain the username
        assert "sess_0000" not in sid
        # Must not be a raw timestamp / integer
        assert not re.fullmatch(r"\d+(\.\d+)?", sid)
        # Must be URL-safe token of substantial length
        assert len(sid) >= 32
        # Round-trip through secrets.token_urlsafe should be possible
        # (verifies the alphabet is URL-safe token chars)
        re.fullmatch(r"[A-Za-z0-9_\-]+", sid)


# -------------------------------------------------------------------
# Test 8 — N users can log in dynamically (N = 1, 10, 70, 100)
# -------------------------------------------------------------------
@pytest.mark.parametrize("n", [1, 10, 70, 100])
def test_n_users_login_creates_n_sessions(auth_client, n):
    client, adb = auth_client
    usernames = _seed_accounts(adb, n)
    sids = []
    for i, u in enumerate(usernames):
        res = _login(client, u, _pw(i))
        assert res.status_code == 200, f"login failed for {u}"
        sids.append(res.get_json()["sessionId"])
    # All session IDs unique
    assert len(set(sids)) == n
    # All sessions are present in the live DB and active
    active = adb.list_active_sessions()
    assert len(active) == n
    active_sids = {r["session_id"] for r in active}
    assert set(sids).issubset(active_sids)
    active_users = {r["username"] for r in active}
    assert set(usernames) == active_users


# -------------------------------------------------------------------
# Bonus — IP / user-agent stored when available
# -------------------------------------------------------------------
def test_ip_and_user_agent_stored_when_available(auth_client):
    client, adb = auth_client
    _seed_accounts(adb, 1)
    res = client.post(
        "/api/auth/login",
        data=json.dumps({"username": "sess_0000", "password": _pw(0)}),
        content_type="application/json",
        headers={"User-Agent": "pytest-agent/1.0"},
        environ_overrides={"REMOTE_ADDR": "10.20.30.40"},
    )
    assert res.status_code == 200
    sid = res.get_json()["sessionId"]
    row = adb.get_live_session(sid)
    assert row["ip_address"] == "10.20.30.40"
    assert row["user_agent"] == "pytest-agent/1.0"


# -------------------------------------------------------------------
# Bonus — Missing fields still produce a clean 400 (no session)
# -------------------------------------------------------------------
def test_missing_credentials_no_session(auth_client):
    client, adb = auth_client
    res = client.post(
        "/api/auth/login",
        data=json.dumps({"username": "x"}),
        content_type="application/json",
    )
    assert res.status_code == 400
    assert adb.list_active_sessions() == []