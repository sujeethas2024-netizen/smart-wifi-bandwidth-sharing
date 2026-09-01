import os
import sys

import pytest


PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)
BACKEND_PATH = os.path.join(PROJECT_ROOT, "backend")

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)


@pytest.fixture
def sample_users():
    from game_theory.congestion_game import User
    return [
        User(user_id=1, activity="browsing", requested_bandwidth=10),
        User(user_id=2, activity="online_class", requested_bandwidth=15),
        User(user_id=3, activity="gaming", requested_bandwidth=20),
        User(user_id=4, activity="downloading", requested_bandwidth=30),
    ]


@pytest.fixture
def sample_user_dicts():
    return [
        {"user_id": 1, "activity": "browsing", "requested_bandwidth": 10},
        {"user_id": 2, "activity": "online_class", "requested_bandwidth": 15},
        {"user_id": 3, "activity": "gaming", "requested_bandwidth": 20},
        {"user_id": 4, "activity": "downloading", "requested_bandwidth": 30},
    ]


@pytest.fixture
def total_bandwidth():
    return 40.0


@pytest.fixture
def game_config():
    return {
        "total_bandwidth": 40.0,
        "congestion_penalty": 0.5,
        "step": 0.5,
        "max_iterations": 100,
    }


@pytest.fixture
def flask_client():
    from backend.app import app
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client
