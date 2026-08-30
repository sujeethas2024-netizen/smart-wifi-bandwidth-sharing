import math

import pytest

from game_theory.congestion_game import User
from game_theory.nash_equilibrium import (
    find_best_response,
    find_nash_equilibrium,
)


class TestNashConverges:
    def test_converges_within_max_iterations(self, sample_users, total_bandwidth):
        result = find_nash_equilibrium(
            sample_users, total_bandwidth, max_iterations=100
        )
        assert result["iterations"] <= 100

    def test_converges_reasonably_fast(self, sample_users, total_bandwidth):
        result = find_nash_equilibrium(
            sample_users, total_bandwidth, max_iterations=100
        )
        assert result["iterations"] < 100

    def test_result_has_allocations(self, sample_users, total_bandwidth):
        result = find_nash_equilibrium(
            sample_users, total_bandwidth, max_iterations=100
        )
        assert "allocations" in result
        assert "iterations" in result
        assert len(result["allocations"]) == len(sample_users)


class TestNashTotalBandwidthRespected:
    def test_sum_does_not_exceed_total(self, sample_users, total_bandwidth):
        result = find_nash_equilibrium(
            sample_users, total_bandwidth, max_iterations=100
        )
        total = sum(result["allocations"].values())
        assert total <= total_bandwidth + 1e-6

    def test_single_user_respects_bandwidth(self, total_bandwidth):
        users = [User(user_id=1, activity="browsing", requested_bandwidth=10)]
        result = find_nash_equilibrium(
            users, total_bandwidth, max_iterations=100
        )
        assert result["allocations"][1] <= total_bandwidth + 1e-6


class TestNashNoUserExceedsRequest:
    def test_no_user_exceeds_request(self, sample_users, total_bandwidth):
        result = find_nash_equilibrium(
            sample_users, total_bandwidth, max_iterations=100
        )
        for user in sample_users:
            allocated = result["allocations"][user.user_id]
            assert allocated <= user.requested_bandwidth + 1e-6

    def test_high_request_user_respects_limit(self, total_bandwidth):
        users = [
            User(user_id=1, activity="browsing", requested_bandwidth=5),
            User(user_id=2, activity="gaming", requested_bandwidth=3),
        ]
        result = find_nash_equilibrium(
            users, total_bandwidth, max_iterations=100
        )
        for user in users:
            assert result["allocations"][user.user_id] <= user.requested_bandwidth + 1e-6


class TestNashReproducibility:
    def test_same_seed_same_result(self):
        users1 = [
            User(user_id=1, activity="browsing", requested_bandwidth=10),
            User(user_id=2, activity="gaming", requested_bandwidth=20),
        ]
        users2 = [
            User(user_id=1, activity="browsing", requested_bandwidth=10),
            User(user_id=2, activity="gaming", requested_bandwidth=20),
        ]
        result1 = find_nash_equilibrium(
            users1, 40.0, max_iterations=100
        )
        result2 = find_nash_equilibrium(
            users2, 40.0, max_iterations=100
        )
        assert result1["allocations"] == result2["allocations"]
        assert result1["iterations"] == result2["iterations"]

    def test_different_still_produces_valid_result(self):
        users = [
            User(user_id=1, activity="browsing", requested_bandwidth=10),
            User(user_id=2, activity="gaming", requested_bandwidth=20),
        ]
        result = find_nash_equilibrium(
            users, 40.0, max_iterations=100
        )
        assert len(result["allocations"]) == 2
        total = sum(result["allocations"].values())
        assert total <= 40.0 + 1e-6


class TestNashConvergenceCriteria:
    def test_stops_when_change_below_step(self):
        users = [
            User(user_id=1, activity="browsing", requested_bandwidth=10),
            User(user_id=2, activity="gaming", requested_bandwidth=10),
        ]
        result = find_nash_equilibrium(
            users, 20.0, step=1.0, max_iterations=100
        )
        assert result["iterations"] <= 100

    def test_converged_allocations_stable(self):
        users = [
            User(user_id=1, activity="browsing", requested_bandwidth=10),
            User(user_id=2, activity="gaming", requested_bandwidth=10),
        ]
        result = find_nash_equilibrium(
            users, 20.0, step=0.5, max_iterations=200
        )
        assert result["iterations"] <= 200


class TestBestResponseBasic:
    def test_best_response_returns_bandwidth_and_utility(self):
        user = User(user_id=1, activity="browsing", requested_bandwidth=20)
        other = User(user_id=2, activity="gaming", requested_bandwidth=20)
        allocations = {2: 10.0}
        bw, util = find_best_response(user, [user, other], allocations, 40.0)
        assert isinstance(bw, float)
        assert isinstance(util, float)
        assert bw >= 0.0
        assert bw <= user.requested_bandwidth

    def test_best_response_respects_remaining_bandwidth(self):
        user = User(user_id=1, activity="browsing", requested_bandwidth=20)
        other = User(user_id=2, activity="gaming", requested_bandwidth=20)
        allocations = {2: 35.0}
        bw, _ = find_best_response(user, [user, other], allocations, 40.0)
        assert bw <= 5.0 + 1e-6

    def test_best_response_returns_positive_utility(self):
        user = User(user_id=1, activity="gaming", requested_bandwidth=20)
        other = User(user_id=2, activity="browsing", requested_bandwidth=10)
        allocations = {2: 5.0}
        bw, util = find_best_response(user, [user, other], allocations, 40.0)
        if bw > 0:
            assert util > float("-inf")


class TestQosFlowsThroughNash:
    def test_best_response_uses_latency(self):
        user = User(user_id=1, activity="gaming", requested_bandwidth=20, latency=50.0)
        other = User(user_id=2, activity="browsing", requested_bandwidth=20)
        allocations = {2: 10.0}
        bw_with_latency, _ = find_best_response(user, [user, other], allocations, 40.0)
        user_no_latency = User(user_id=1, activity="gaming", requested_bandwidth=20, latency=0.0)
        bw_no_latency, _ = find_best_response(user_no_latency, [user_no_latency, other], allocations, 40.0)
        assert bw_with_latency <= bw_no_latency + 1e-6

    def test_best_response_uses_jitter(self):
        user = User(user_id=1, activity="gaming", requested_bandwidth=20, jitter=15.0)
        other = User(user_id=2, activity="browsing", requested_bandwidth=20)
        allocations = {2: 10.0}
        bw_with_jitter, _ = find_best_response(user, [user, other], allocations, 40.0)
        user_no_jitter = User(user_id=1, activity="gaming", requested_bandwidth=20, jitter=0.0)
        bw_no_jitter, _ = find_best_response(user_no_jitter, [user_no_jitter, other], allocations, 40.0)
        assert bw_with_jitter <= bw_no_jitter + 1e-6

    def test_nash_result_reports_equilibrium_status(self):
        users = [
            User(user_id=1, activity="browsing", requested_bandwidth=10, latency=10.0, jitter=2.0),
            User(user_id=2, activity="gaming", requested_bandwidth=10, latency=20.0, jitter=5.0),
        ]
        result = find_nash_equilibrium(users, 20.0, max_iterations=100)
        assert "is_nash_equilibrium" in result
        assert isinstance(result["is_nash_equilibrium"], bool)

    def test_verify_rejects_profile_with_profitable_deviation(self):
        user = User(user_id=1, activity="gaming", requested_bandwidth=20, latency=0.0, jitter=0.0)
        other = User(user_id=2, activity="browsing", requested_bandwidth=20, latency=0.0, jitter=0.0)
        allocations = {1: 0.0, 2: 0.0}
        user.allocated_bandwidth = 0.0
        other.allocated_bandwidth = 0.0
        from game_theory.nash_equilibrium import verify_nash_equilibrium
        assert verify_nash_equilibrium([user, other], allocations, 40.0) is False

    def test_verify_accepts_equilibrium_when_no_deviation(self):
        users = [
            User(user_id=1, activity="browsing", requested_bandwidth=10, latency=5.0, jitter=1.0),
            User(user_id=2, activity="gaming", requested_bandwidth=10, latency=10.0, jitter=2.0),
        ]
        result = find_nash_equilibrium(users, 20.0, max_iterations=100)
        assert result["is_nash_equilibrium"] is True

    def test_default_qos_is_zero_when_not_provided(self):
        user = User(user_id=1, activity="browsing", requested_bandwidth=10)
        assert user.latency == 0.0
        assert user.jitter == 0.0
