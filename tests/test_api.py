import json

import pytest

from backend.app import app


@pytest.fixture
def flask_client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestHealthEndpoint:
    def test_health_endpoint_returns_200(self, flask_client):
        response = flask_client.get("/api/health")
        assert response.status_code == 200

    def test_health_endpoint_json(self, flask_client):
        response = flask_client.get("/api/health")
        data = response.get_json()
        assert data["status"] == "healthy"
        assert data["service"] == "smart-wifi-bandwidth-sharing"

    def test_health_endpoint_content_type(self, flask_client):
        response = flask_client.get("/api/health")
        assert response.content_type == "application/json"


class TestAllocateEndpoint:
    def test_allocate_endpoint_returns_allocation(self, flask_client):
        payload = {
            "total_bandwidth": 40.0,
            "users": [
                {"user_id": 1, "activity": "browsing", "requested_bandwidth": 10},
                {"user_id": 2, "activity": "gaming", "requested_bandwidth": 20},
            ],
        }
        response = flask_client.post(
            "/api/allocate",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert "result" in data
        assert "users" in data["result"]

    def test_allocate_endpoint_returns_user_count(self, flask_client):
        payload = {
            "total_bandwidth": 40.0,
            "users": [
                {"user_id": 1, "activity": "browsing", "requested_bandwidth": 10},
            ],
        }
        response = flask_client.post(
            "/api/allocate",
            data=json.dumps(payload),
            content_type="application/json",
        )
        data = response.get_json()
        assert len(data["result"]["users"]) == 1

    def test_allocate_endpoint_validation_missing_body(self, flask_client):
        response = flask_client.post(
            "/api/allocate",
            data="not json",
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_allocate_endpoint_validation_no_users(self, flask_client):
        payload = {"total_bandwidth": 40.0}
        response = flask_client.post(
            "/api/allocate",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"

    def test_allocate_endpoint_validation_negative_bandwidth(self, flask_client):
        payload = {
            "total_bandwidth": -10.0,
            "users": [
                {"user_id": 1, "activity": "browsing", "requested_bandwidth": 10},
            ],
        }
        response = flask_client.post(
            "/api/allocate",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_allocate_endpoint_validation_missing_fields(self, flask_client):
        payload = {
            "total_bandwidth": 40.0,
            "users": [
                {"user_id": 1},
            ],
        }
        response = flask_client.post(
            "/api/allocate",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_allocate_endpoint_users_not_list(self, flask_client):
        payload = {
            "total_bandwidth": 40.0,
            "users": "not a list",
        }
        response = flask_client.post(
            "/api/allocate",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 400


class TestExperimentRunEndpoint:
    def test_experiment_run_endpoint_returns_results(self, flask_client):
        payload = {"user_counts": [3], "total_bandwidth": 40.0, "seed": 42}
        response = flask_client.post(
            "/api/experiment/run",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert "results" in data
        assert "config" in data
        assert isinstance(data["results"], list)

    def test_experiment_run_endpoint_default_config(self, flask_client):
        payload = {}
        response = flask_client.post(
            "/api/experiment/run",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert len(data["results"]) > 0

    def test_experiment_run_endpoint_invalid_user_counts(self, flask_client):
        payload = {"user_counts": "not a list"}
        response = flask_client.post(
            "/api/experiment/run",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_experiment_run_endpoint_empty_user_counts(self, flask_client):
        payload = {"user_counts": []}
        response = flask_client.post(
            "/api/experiment/run",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_experiment_run_endpoint_negative_bandwidth(self, flask_client):
        payload = {"total_bandwidth": -10.0}
        response = flask_client.post(
            "/api/experiment/run",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 400
