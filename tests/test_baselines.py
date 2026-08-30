import pytest

from services.evaluation_service import (
    equal_allocation,
    proportional_allocation,
    priority_allocation,
)


class TestEqualAllocationBasic:
    def test_equal_split(self):
        users = [
            {"user_id": 1, "requested_bandwidth": 10},
            {"user_id": 2, "requested_bandwidth": 10},
            {"user_id": 3, "requested_bandwidth": 10},
        ]
        result = equal_allocation(users, 30.0)
        assert result == {1: 10.0, 2: 10.0, 3: 10.0}

    def test_equal_split_unequal_requests(self):
        users = [
            {"user_id": 1, "requested_bandwidth": 5},
            {"user_id": 2, "requested_bandwidth": 20},
        ]
        result = equal_allocation(users, 10.0)
        assert result[1] == 5.0
        assert result[2] == 5.0

    def test_sum_does_not_exceed_total(self):
        users = [
            {"user_id": i, "requested_bandwidth": 100.0}
            for i in range(1, 6)
        ]
        result = equal_allocation(users, 40.0)
        total = sum(result.values())
        assert total <= 40.0


class TestEqualAllocationRespectsDemand:
    def test_no_user_gets_more_than_requested(self):
        users = [
            {"user_id": 1, "requested_bandwidth": 5},
            {"user_id": 2, "requested_bandwidth": 8},
            {"user_id": 3, "requested_bandwidth": 3},
        ]
        result = equal_allocation(users, 100.0)
        for uid, allocation in result.items():
            req = next(u["requested_bandwidth"] for u in users if u["user_id"] == uid)
            assert allocation <= req

    def test_zero_request_gets_zero_allocation(self):
        users = [
            {"user_id": 1, "requested_bandwidth": 0},
            {"user_id": 2, "requested_bandwidth": 10},
        ]
        result = equal_allocation(users, 10.0)
        assert result[1] == 0.0
        assert result[2] == 5.0


class TestProportionalAllocationBasic:
    def test_proportional_split(self):
        users = [
            {"user_id": 1, "requested_bandwidth": 10},
            {"user_id": 2, "requested_bandwidth": 20},
            {"user_id": 3, "requested_bandwidth": 30},
        ]
        result = proportional_allocation(users, 60.0)
        assert result[1] == 10.0
        assert result[2] == 20.0
        assert result[3] == 30.0

    def test_proportional_split_sum_equals_capacity(self):
        users = [
            {"user_id": 1, "requested_bandwidth": 10},
            {"user_id": 2, "requested_bandwidth": 20},
            {"user_id": 3, "requested_bandwidth": 30},
        ]
        result = proportional_allocation(users, 30.0)
        total = sum(result.values())
        assert abs(total - 30.0) < 0.01


class TestProportionalAllocationUnderDemand:
    def test_all_get_requested_when_under_demand(self):
        users = [
            {"user_id": 1, "requested_bandwidth": 10},
            {"user_id": 2, "requested_bandwidth": 15},
        ]
        result = proportional_allocation(users, 100.0)
        assert result[1] == 10.0
        assert result[2] == 15.0


class TestProportionalAllocationOverDemand:
    def test_scaled_down_when_over_demand(self):
        users = [
            {"user_id": 1, "requested_bandwidth": 30},
            {"user_id": 2, "requested_bandwidth": 30},
        ]
        result = proportional_allocation(users, 30.0)
        assert result[1] == 15.0
        assert result[2] == 15.0

    def test_no_user_exceeds_request_when_over_demand(self):
        users = [
            {"user_id": 1, "requested_bandwidth": 10},
            {"user_id": 2, "requested_bandwidth": 20},
            {"user_id": 3, "requested_bandwidth": 30},
        ]
        result = proportional_allocation(users, 20.0)
        for uid, allocation in result.items():
            req = next(u["requested_bandwidth"] for u in users if u["user_id"] == uid)
            assert allocation <= req


class TestPriorityAllocationBasic:
    def test_higher_priority_gets_more(self):
        users = [
            {"user_id": 1, "activity": "browsing", "requested_bandwidth": 10},
            {"user_id": 2, "activity": "gaming", "requested_bandwidth": 10},
        ]
        result = priority_allocation(users, 10.0)
        assert result[2] > result[1]

    def test_gaming_priority_over_browsing(self):
        users = [
            {"user_id": 1, "activity": "browsing", "requested_bandwidth": 5},
            {"user_id": 2, "activity": "gaming", "requested_bandwidth": 5},
        ]
        result = priority_allocation(users, 10.0)
        assert result[2] > result[1]

    def test_respects_demand(self):
        users = [
            {"user_id": 1, "activity": "gaming", "requested_bandwidth": 5},
            {"user_id": 2, "activity": "browsing", "requested_bandwidth": 3},
        ]
        result = priority_allocation(users, 5.0)
        assert result[1] <= 5.0 + 1e-6
        assert result[2] <= 3.0 + 1e-6

    def test_returns_empty_for_empty_input(self):
        assert priority_allocation([], 10.0) == {}


class TestPriorityAllocationZeroUsers:
    def test_zero_users_returns_empty(self):
        assert priority_allocation([], 100.0) == {}

    def test_zero_users_various_bandwidths(self):
        assert priority_allocation([], 0.0) == {}
        assert priority_allocation([], 1000.0) == {}
