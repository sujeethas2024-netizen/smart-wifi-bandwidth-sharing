"""
End-to-end authentication tests for /api/allocate.

The live /api/allocate HTTP boundary must require a valid active
session. Research callers that bypass HTTP (call
``allocate_bandwidth`` directly) are not affected — auth belongs
at the HTTP boundary only.
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


@pytest.fixture
def fresh_account(flask_client):
    from backend.database import accounts_db as adb
    ok, _ = adb.create_account(
        username="alloc_user",
        password="Passw0rd!",
        full_name="Alloc User",
        role="user",
        usage_reason="General Browsing",
        device_count=1,
    )
    assert ok
    return adb


def _active_session(adb, username: str = "alloc_user") -> str:
    sid = secrets.token_urlsafe(24)
    row = adb.create_live_session(
        session_id=sid,
        username=username,
        ip_address="127.0.0.1",
        user_agent="pytest",
    )
    assert row is not None
    return sid


def _body():
    return {
        "total_bandwidth": 40.0,
        "users": [
            {"user_id": "alloc_user", "activity": "browsing", "requested_bandwidth": 5.0},
        ],
    }


class TestAllocateAuthentication:
    def test_missing_authorization_header_rejected(self, flask_client):
        res = flask_client.post("/api/allocate", json=_body())
        assert res.status_code == 401
        body = res.get_json()
        assert body["status"] == "error"
        assert "Authorization" in body["message"]

    def test_malformed_authorization_header_rejected(self, flask_client):
        res = flask_client.post(
            "/api/allocate",
            json=_body(),
            headers={"Authorization": "NotBearer foo"},
        )
        assert res.status_code == 401

    def test_empty_token_rejected(self, flask_client):
        res = flask_client.post(
            "/api/allocate",
            json=_body(),
            headers={"Authorization": "Bearer "},
        )
        assert res.status_code == 401

    def test_invalid_session_rejected(self, flask_client):
        res = flask_client.post(
            "/api/allocate",
            json=_body(),
            headers={"Authorization": "Bearer not-a-real-token"},
        )
        assert res.status_code == 401
        assert "Invalid" in res.get_json()["message"]

    def test_revoked_session_rejected(self, flask_client, fresh_account):
        adb = fresh_account
        sid = _active_session(adb)
        adb.revoke_live_session(sid)
        res = flask_client.post(
            "/api/allocate",
            json=_body(),
            headers={"Authorization": f"Bearer {sid}"},
        )
        assert res.status_code == 401
        assert "not active" in res.get_json()["message"].lower() or "revoked" in res.get_json()["message"].lower()

    def test_active_session_accepted(self, flask_client, fresh_account):
        adb = fresh_account
        sid = _active_session(adb)
        res = flask_client.post(
            "/api/allocate",
            json=_body(),
            headers={"Authorization": f"Bearer {sid}"},
        )
        assert res.status_code == 200
        body = res.get_json()
        assert body["status"] == "success"
        assert body["result"]["users"][0]["user_id"] == "alloc_user"

    def test_live_users_flag_uses_server_population(self, flask_client, fresh_account):
        adb = fresh_account
        sid = _active_session(adb)
        res = flask_client.post(
            "/api/allocate",
            json={"total_bandwidth": 40.0, "use_live_users": True, "user_requests": {"alloc_user": 5.0}},
            headers={"Authorization": f"Bearer {sid}"},
        )
        assert res.status_code == 200
        body = res.get_json()
        assert body["live_source"]["unique_user_count"] == 1
        assert body["number_of_users"] == 1
        assert body["result"]["is_nash_equilibrium"] in (True, False)

    def test_live_users_ignores_forged_users(self, flask_client, fresh_account):
        adb = fresh_account
        sid = _active_session(adb)
        res = flask_client.post(
            "/api/allocate",
            json={
                "total_bandwidth": 40.0,
                "use_live_users": True,
                "user_requests": {"alloc_user": 5.0},
                "users": [
                    {
                        "user_id": "fake_attacker",
                        "activity": "gaming",
                        "requested_bandwidth": 999,
                    }
                ],
            },
            headers={"Authorization": f"Bearer {sid}"},
        )
        assert res.status_code == 200
        body = res.get_json()
        assert body["number_of_users"] == 1
        assert body["result"]["users"][0]["user_id"] == "alloc_user"
        assert "fake_attacker" not in [
            u["user_id"] for u in body["result"]["users"]
        ]

    def test_live_users_forged_count_cannot_inject_users(self, flask_client, fresh_account):
        adb = fresh_account
        sid = _active_session(adb)
        fake_users = [
            {"user_id": f"fake_{i}", "activity": "gaming", "requested_bandwidth": 999}
            for i in range(5)
        ]
        res = flask_client.post(
            "/api/allocate",
            json={
                "total_bandwidth": 40.0,
                "use_live_users": True,
                "user_requests": {"alloc_user": 5.0},
                "users": fake_users,
            },
            headers={"Authorization": f"Bearer {sid}"},
        )
        assert res.status_code == 200
        body = res.get_json()
        assert body["number_of_users"] == 1
        assert body["live_source"]["unique_user_count"] == 1

    def test_live_users_client_cannot_override_activity_or_bandwidth(self, flask_client, fresh_account):
        adb = fresh_account
        sid = _active_session(adb)
        res = flask_client.post(
            "/api/allocate",
            json={
                "total_bandwidth": 40.0,
                "use_live_users": True,
                "user_requests": {"alloc_user": 5.0},
                "users": [
                    {
                        "user_id": "alloc_user",
                        "activity": "gaming",
                        "requested_bandwidth": 999,
                    }
                ],
            },
            headers={"Authorization": f"Bearer {sid}"},
        )
        assert res.status_code == 200
        body = res.get_json()
        user_result = next(u for u in body["result"]["users"] if u["user_id"] == "alloc_user")
        assert user_result["activity"] == "browsing"
        assert user_result["requested_bandwidth"] == 5.0
        assert user_result["requested_bandwidth"] != 999


class TestLiveUserRequestValidation:
    def test_positive_int_accepted(self, flask_client, fresh_account):
        adb = fresh_account
        sid = _active_session(adb)
        res = flask_client.post(
            "/api/allocate",
            json={"total_bandwidth": 40.0, "use_live_users": True, "user_requests": {"alloc_user": 5}},
            headers={"Authorization": f"Bearer {sid}"},
        )
        assert res.status_code == 200

    def test_positive_float_accepted(self, flask_client, fresh_account):
        adb = fresh_account
        sid = _active_session(adb)
        res = flask_client.post(
            "/api/allocate",
            json={"total_bandwidth": 40.0, "use_live_users": True, "user_requests": {"alloc_user": 5.5}},
            headers={"Authorization": f"Bearer {sid}"},
        )
        assert res.status_code == 200

    def test_large_positive_accepted(self, flask_client, fresh_account):
        adb = fresh_account
        sid = _active_session(adb)
        res = flask_client.post(
            "/api/allocate",
            json={"total_bandwidth": 40.0, "use_live_users": True, "user_requests": {"alloc_user": 1000.0}},
            headers={"Authorization": f"Bearer {sid}"},
        )
        assert res.status_code == 200

    def test_zero_rejected(self, flask_client, fresh_account):
        adb = fresh_account
        sid = _active_session(adb)
        res = flask_client.post(
            "/api/allocate",
            json={"total_bandwidth": 40.0, "use_live_users": True, "user_requests": {"alloc_user": 0.0}},
            headers={"Authorization": f"Bearer {sid}"},
        )
        assert res.status_code == 400

    def test_negative_rejected(self, flask_client, fresh_account):
        adb = fresh_account
        sid = _active_session(adb)
        res = flask_client.post(
            "/api/allocate",
            json={"total_bandwidth": 40.0, "use_live_users": True, "user_requests": {"alloc_user": -1.0}},
            headers={"Authorization": f"Bearer {sid}"},
        )
        assert res.status_code == 400

    def test_non_numeric_string_rejected(self, flask_client, fresh_account):
        adb = fresh_account
        sid = _active_session(adb)
        res = flask_client.post(
            "/api/allocate",
            json={"total_bandwidth": 40.0, "use_live_users": True, "user_requests": {"alloc_user": "abc"}},
            headers={"Authorization": f"Bearer {sid}"},
        )
        assert res.status_code == 400

    def test_null_rejected(self, flask_client, fresh_account):
        adb = fresh_account
        sid = _active_session(adb)
        res = flask_client.post(
            "/api/allocate",
            json={"total_bandwidth": 40.0, "use_live_users": True, "user_requests": {"alloc_user": None}},
            headers={"Authorization": f"Bearer {sid}"},
        )
        assert res.status_code == 400

    def test_nan_rejected(self, flask_client, fresh_account):
        adb = fresh_account
        sid = _active_session(adb)
        res = flask_client.post(
            "/api/allocate",
            json={"total_bandwidth": 40.0, "use_live_users": True, "user_requests": {"alloc_user": float("nan")}},
            headers={"Authorization": f"Bearer {sid}"},
        )
        assert res.status_code == 400

    def test_positive_infinity_rejected(self, flask_client, fresh_account):
        adb = fresh_account
        sid = _active_session(adb)
        res = flask_client.post(
            "/api/allocate",
            json={"total_bandwidth": 40.0, "use_live_users": True, "user_requests": {"alloc_user": float("inf")}},
            headers={"Authorization": f"Bearer {sid}"},
        )
        assert res.status_code == 400

    def test_negative_infinity_rejected(self, flask_client, fresh_account):
        adb = fresh_account
        sid = _active_session(adb)
        res = flask_client.post(
            "/api/allocate",
            json={"total_bandwidth": 40.0, "use_live_users": True, "user_requests": {"alloc_user": float("-inf")}},
            headers={"Authorization": f"Bearer {sid}"},
        )
        assert res.status_code == 400

    def test_missing_user_request_skips_user(self, flask_client, fresh_account):
        adb = fresh_account
        sid = _active_session(adb)
        res = flask_client.post(
            "/api/allocate",
            json={"total_bandwidth": 40.0, "use_live_users": True, "user_requests": {}},
            headers={"Authorization": f"Bearer {sid}"},
        )
        assert res.status_code == 400
        body = res.get_json()
        assert "No active live users with a bandwidth request" in body["message"]

    def test_valid_asymmetric_requests_reach_engine(self, flask_client, fresh_account):
        adb = fresh_account
        sid = _active_session(adb)
        res = flask_client.post(
            "/api/allocate",
            json={
                "total_bandwidth": 40.0,
                "use_live_users": True,
                "user_requests": {"alloc_user": 5.0, "other_user": 15.0},
            },
            headers={"Authorization": f"Bearer {sid}"},
        )
        assert res.status_code == 200
        body = res.get_json()
        assert body["result"]["total_allocated_bandwidth"] <= 40.0 + 1e-6
        assert body["result"]["is_nash_equilibrium"] is True


class TestAllocateValidation:
    def test_empty_body_rejected(self, flask_client, fresh_account):
        adb = fresh_account
        sid = _active_session(adb)
        res = flask_client.post(
            "/api/allocate",
            json={},
            headers={"Authorization": f"Bearer {sid}"},
        )
        # 400 (validation) or 401 (no users) is acceptable
        assert res.status_code in (400, 401)

    def test_zero_total_bandwidth_rejected(self, flask_client, fresh_account):
        adb = fresh_account
        sid = _active_session(adb)
        res = flask_client.post(
            "/api/allocate",
            json={"total_bandwidth": 0, "users": _body()["users"]},
            headers={"Authorization": f"Bearer {sid}"},
        )
        assert res.status_code == 400
