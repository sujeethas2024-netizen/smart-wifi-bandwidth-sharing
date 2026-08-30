import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)
BACKEND_PATH = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)

from game_theory.congestion_game import User
from game_theory.nash_equilibrium import find_nash_equilibrium
from game_theory.fairness import jains_fairness_index


TOTAL_BANDWIDTH = 40

USERS = [
    User(user_id=1, activity="browsing", requested_bandwidth=10),
    User(user_id=2, activity="online_class", requested_bandwidth=15),
    User(user_id=3, activity="gaming", requested_bandwidth=20),
    User(user_id=4, activity="downloading", requested_bandwidth=30),
]


class TestNashAllocation:
    def test_converges(self):
        result = find_nash_equilibrium(USERS, TOTAL_BANDWIDTH)
        assert result["iterations"] <= 100

    def test_allocations_respect_requests(self):
        result = find_nash_equilibrium(USERS, TOTAL_BANDWIDTH)
        for user in USERS:
            assert result["allocations"][user.user_id] <= user.requested_bandwidth + 1e-6

    def test_total_allocated_does_not_exceed_capacity(self):
        result = find_nash_equilibrium(USERS, TOTAL_BANDWIDTH)
        total = sum(result["allocations"].values())
        assert total <= TOTAL_BANDWIDTH + 1e-6

    def test_fairness_in_valid_range(self):
        result = find_nash_equilibrium(USERS, TOTAL_BANDWIDTH)
        fairness = jains_fairness_index(result["allocations"])
        assert 0.0 <= fairness <= 1.0

    def test_all_users_have_utilities(self):
        result = find_nash_equilibrium(USERS, TOTAL_BANDWIDTH)
        for user in USERS:
            assert user.allocated_bandwidth >= 0.0
            assert isinstance(user.utility, float)
