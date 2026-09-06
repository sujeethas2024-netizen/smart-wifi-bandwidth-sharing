"""
End-to-end dynamic N-user allocation tests.

These tests verify that the live allocation endpoint:
  * accepts any number of live users (no hardcoded limit)
  * returns a valid Nash-equilibrium result
  * computes a Jain fairness index
  * propagates the population into the Game Theory engine
"""

import os
import secrets
import sys
import tempfile

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


@pytest.fixture
def flask_client(monkeypatch):
    from backend.database import accounts_db as adb
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.unlink(path)
    monkeypatch.setattr(adb, "DB_PATH", path)
    adb.init_db()
    from backend.app import app
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def _register(adb, username: str) -> None:
    ok, _ = adb.create_account(
        username=username,
        password="Passw0rd!",
        full_name=username.title(),
        role="user",
        usage_reason="General Browsing",
        device_count=1,
    )
    assert ok


def _session(adb, username: str) -> str:
    sid = secrets.token_urlsafe(24)
    adb.create_live_session(
        session_id=sid,
        username=username,
        ip_address="127.0.0.1",
        user_agent="pytest",
    )
    return sid


@pytest.fixture
def admin_session(flask_client):
    from backend.database import accounts_db as adb
    # Seed a default admin (init_db already did this with our isolated
    # path, but we re-fetch its session id to be safe).
    sid = _session(adb, "admin")
    return sid


@pytest.mark.parametrize("count", [1, 10, 70, 100, 200, 373])
def test_dynamic_n_users_allocation(flask_client, admin_session, count):
    from backend.database import accounts_db as adb
    # Populate the live_sessions table with `count` distinct users.
    user_requests = {"admin": 5.0}
    for i in range(count):
        uname = f"pop_{i}"
        _register(adb, uname)
        _session(adb, uname)
        user_requests[uname] = 5.0
    res = flask_client.post(
        "/api/allocate",
        json={"total_bandwidth": 200.0, "use_live_users": True, "user_requests": user_requests},
        headers={"Authorization": f"Bearer {admin_session}"},
    )
    assert res.status_code == 200, res.get_data(as_text=True)
    body = res.get_json()
    assert body["status"] == "success"
    # The admin session is also live, so the count is +1 (admin + N users)
    assert body["number_of_users"] == count + 1
    result = body["result"]
    # Result integrity
    assert result["jain_fairness_index"] >= 0
    assert result["jain_fairness_index"] <= 1
    assert result["utilization_percentage"] >= 0
    assert result["utilization_percentage"] <= 100
    assert result["converged"] is True
    assert len(result["users"]) == count + 1
    assert all(u["allocated_bandwidth"] >= 0 for u in result["users"])


def test_logout_removes_user_from_population(flask_client, admin_session):
    from backend.database import accounts_db as adb
    for i in range(5):
        uname = f"leaver_{i}"
        _register(adb, uname)
        _session(adb, uname)

    user_requests = {"admin": 5.0}
    for i in range(5):
        user_requests[f"leaver_{i}"] = 5.0

    # First allocation: 5 + admin = 6 users.
    res = flask_client.post(
        "/api/allocate",
        json={"total_bandwidth": 100.0, "use_live_users": True, "user_requests": user_requests},
        headers={"Authorization": f"Bearer {admin_session}"},
    )
    assert res.status_code == 200
    first = res.get_json()["number_of_users"]
    assert first == 6

    # Revoke one session.
    sessions = adb.list_active_sessions()
    target = next(s for s in sessions if s["username"] == "leaver_0")
    adb.revoke_live_session(target["session_id"])

    del user_requests["leaver_0"]

    res = flask_client.post(
        "/api/allocate",
        json={"total_bandwidth": 100.0, "use_live_users": True, "user_requests": user_requests},
        headers={"Authorization": f"Bearer {admin_session}"},
    )
    assert res.status_code == 200
    second = res.get_json()["number_of_users"]
    assert second == 5
