import math

import pytest

from game_theory.fairness import fairness_status, jains_fairness_index


class TestJainsFairnessPerfect:
    def test_equal_allocations_returns_one(self):
        allocations = {1: 10.0, 2: 10.0, 3: 10.0, 4: 10.0}
        assert jains_fairness_index(allocations) == 1.0

    def test_equal_allocations_three_users(self):
        allocations = {1: 5.0, 2: 5.0, 3: 5.0}
        assert jains_fairness_index(allocations) == 1.0

    def test_slightly_different_allocations(self):
        allocations = {1: 9.0, 2: 10.0, 3: 11.0}
        result = jains_fairness_index(allocations)
        assert 0.9 < result <= 1.0


class TestJainsFairnessSingleUser:
    def test_single_user_returns_one(self):
        allocations = {1: 10.0}
        assert jains_fairness_index(allocations) == 1.0


class TestJainsFairnessExtreme:
    def test_one_user_gets_all(self):
        allocations = {1: 40.0, 2: 0.0, 3: 0.0, 4: 0.0}
        result = jains_fairness_index(allocations)
        assert result == pytest.approx(0.25, abs=0.001)

    def test_two_users_get_all_rest_zero(self):
        allocations = {1: 20.0, 2: 20.0, 3: 0.0, 4: 0.0}
        result = jains_fairness_index(allocations)
        assert result == pytest.approx(0.5, abs=0.001)


class TestJainsFairnessZero:
    def test_all_zero_returns_zero(self):
        allocations = {1: 0.0, 2: 0.0, 3: 0.0}
        assert jains_fairness_index(allocations) == 0.0

    def test_empty_allocations_returns_zero(self):
        assert jains_fairness_index({}) == 0.0


class TestFairnessStatusThresholds:
    def test_excellent_threshold(self):
        assert fairness_status(0.95) == "Excellent"
        assert fairness_status(0.90) == "Excellent"

    def test_good_threshold(self):
        assert fairness_status(0.80) == "Good"
        assert fairness_status(0.75) == "Good"

    def test_moderate_threshold(self):
        assert fairness_status(0.60) == "Moderate"
        assert fairness_status(0.50) == "Moderate"

    def test_poor_threshold(self):
        assert fairness_status(0.40) == "Poor"
        assert fairness_status(0.0) == "Poor"

    def test_boundary_values(self):
        assert fairness_status(0.8999) == "Good"
        assert fairness_status(0.90) == "Excellent"
        assert fairness_status(0.7499) == "Moderate"
        assert fairness_status(0.75) == "Good"
        assert fairness_status(0.4999) == "Poor"
        assert fairness_status(0.50) == "Moderate"
