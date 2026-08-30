import math

import pytest

from game_theory.congestion_game import CongestionGame, User
from game_theory.fairness import fairness_status, jains_fairness_index
from game_theory.nash_equilibrium import find_nash_equilibrium
from game_theory.utility import calculate_utility
from services.allocation_service import allocate_bandwidth
from services.evaluation_service import (
    equal_allocation,
    proportional_allocation,
    priority_allocation,
)
from simulation.experiment_runner import run_single_experiment


class TestZeroUsers:
    def test_zero_users_equal_allocation(self):
        result = equal_allocation([], 100.0)
        assert result == {}

    def test_zero_users_proportional_allocation(self):
        result = proportional_allocation([], 100.0)
        assert result == {}

    def test_zero_users_priority_allocation(self):
        result = priority_allocation([], 100.0)
        assert result == {}

    def test_zero_users_nash_equilibrium_raises(self):
        with pytest.raises(ValueError):
            allocate_bandwidth([], 100.0)

    def test_zero_users_jain_fairness(self):
        assert jains_fairness_index({}) == 0.0


class TestSingleUser:
    def test_single_user_gets_all_bandwidth_up_to_request(self):
        users = [
            {"user_id": 1, "activity": "browsing", "requested_bandwidth": 10}
        ]
        result = equal_allocation(users, 100.0)
        assert result[1] == 10.0

    def test_single_user_proportional(self):
        users = [
            {"user_id": 1, "activity": "browsing", "requested_bandwidth": 15}
        ]
        result = proportional_allocation(users, 100.0)
        assert result[1] == 15.0

    def test_single_user_priority(self):
        users = [
            {"user_id": 1, "activity": "gaming", "requested_bandwidth": 10}
        ]
        result = priority_allocation(users, 50.0)
        assert result[1] == 50.0

    def test_single_user_game_theory(self):
        simulated_users = [
            {"user_id": 1, "activity": "browsing", "requested_bandwidth": 10}
        ]
        result = allocate_bandwidth(simulated_users, 100.0)
        assert len(result["users"]) == 1
        assert result["users"][0]["allocated_bandwidth"] <= 10.0

    def test_single_user_nash_equilibrium(self):
        users = [User(user_id=1, activity="gaming", requested_bandwidth=20)]
        result = find_nash_equilibrium(users, 40.0, max_iterations=100)
        assert result["allocations"][1] <= 20.0 + 1e-6
        total = sum(result["allocations"].values())
        assert total <= 40.0 + 1e-6


class TestExtremeUserCount:
    def test_large_user_count_runs(self):
        results = run_single_experiment(
            number_of_users=373,
            total_bandwidth=100.0,
            seed=42,
            scenario="medium",
        )
        assert len(results) == 6
        for result in results:
            assert "allocations" in result
            assert "metrics" in result

    def test_large_user_count_metrics_valid(self):
        results = run_single_experiment(
            number_of_users=373,
            total_bandwidth=100.0,
            seed=42,
            scenario="medium",
        )
        for result in results:
            metrics = result["metrics"]
            assert metrics["total_allocated"] >= 0
            assert metrics["utilization"] >= 0
            assert 0 <= metrics["fairness"] <= 1.0


class TestVerySmallBandwidth:
    def test_small_bandwidth_nash(self):
        users = [
            User(user_id=1, activity="browsing", requested_bandwidth=5),
            User(user_id=2, activity="gaming", requested_bandwidth=5),
        ]
        result = find_nash_equilibrium(users, 0.1, max_iterations=100)
        total = sum(result["allocations"].values())
        assert total <= 0.1 + 1e-6

    def test_small_bandwidth_utility(self):
        util = calculate_utility(
            bandwidth=0.05,
            total_usage=0.05,
            total_bandwidth=0.1,
            activity_weight=1.0,
            congestion_penalty=0.5,
        )
        assert isinstance(util, float)

    def test_small_bandwidth_fairness(self):
        allocations = {1: 0.05, 2: 0.05}
        result = jains_fairness_index(allocations)
        assert result == 1.0


class TestVeryLargeBandwidth:
    def test_large_bandwidth_nash(self):
        users = [
            User(user_id=1, activity="browsing", requested_bandwidth=100),
            User(user_id=2, activity="gaming", requested_bandwidth=100),
        ]
        result = find_nash_equilibrium(users, 10000.0, max_iterations=100)
        total = sum(result["allocations"].values())
        assert total <= 10000.0 + 1e-6

    def test_large_bandwidth_utility(self):
        util = calculate_utility(
            bandwidth=1000.0,
            total_usage=1000.0,
            total_bandwidth=10000.0,
            activity_weight=1.0,
            congestion_penalty=0.5,
        )
        assert isinstance(util, float)
        assert util < float("inf")

    def test_large_bandwidth_fairness(self):
        allocations = {1: 5000.0, 2: 5000.0}
        result = jains_fairness_index(allocations)
        assert result == 1.0
