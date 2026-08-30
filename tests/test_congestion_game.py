import pytest

from game_theory.congestion_game import CongestionGame, User


class TestUserCreation:
    def test_user_created_with_correct_id(self):
        user = User(user_id=1, activity="browsing", requested_bandwidth=10)
        assert user.user_id == 1

    def test_user_has_correct_activity(self):
        user = User(user_id=1, activity="gaming", requested_bandwidth=10)
        assert user.activity == "gaming"

    def test_user_has_correct_requested_bandwidth(self):
        user = User(user_id=1, activity="browsing", requested_bandwidth=15.5)
        assert user.requested_bandwidth == 15.5

    def test_user_initial_allocated_bandwidth_is_zero(self):
        user = User(user_id=1, activity="browsing", requested_bandwidth=10)
        assert user.allocated_bandwidth == 0.0

    def test_user_initial_utility_is_zero(self):
        user = User(user_id=1, activity="browsing", requested_bandwidth=10)
        assert user.utility == 0.0

    def test_user_has_weight(self):
        user = User(user_id=1, activity="gaming", requested_bandwidth=10)
        assert user.weight == 1.3

    def test_user_unknown_activity_default_weight(self):
        user = User(user_id=1, activity="unknown", requested_bandwidth=10)
        assert user.weight == 1.0


class TestUserCalculateUtility:
    def test_calculate_utility_updates_utility(self):
        user = User(user_id=1, activity="browsing", requested_bandwidth=10)
        user.allocated_bandwidth = 8.0
        util = user.calculate_utility(
            total_usage=8.0, total_bandwidth=40.0, congestion_penalty=0.5
        )
        assert user.utility == util
        assert isinstance(util, float)

    def test_calculate_utility_zero_allocation(self):
        user = User(user_id=1, activity="browsing", requested_bandwidth=10)
        user.allocated_bandwidth = 0.0
        util = user.calculate_utility(
            total_usage=0.0, total_bandwidth=40.0, congestion_penalty=0.5
        )
        assert util == 0.0

    def test_calculate_utility_with_congestion(self):
        user = User(user_id=1, activity="gaming", requested_bandwidth=20)
        user.allocated_bandwidth = 15.0
        util_low = user.calculate_utility(
            total_usage=15.0, total_bandwidth=40.0, congestion_penalty=0.5
        )
        util_high = user.calculate_utility(
            total_usage=35.0, total_bandwidth=40.0, congestion_penalty=0.5
        )
        assert util_high < util_low


class TestGameTotalUsage:
    def test_total_usage_single_user(self):
        user = User(user_id=1, activity="browsing", requested_bandwidth=10)
        user.allocated_bandwidth = 8.0
        game = CongestionGame(total_bandwidth=40.0, users=[user])
        assert game.total_usage() == 8.0

    def test_total_usage_multiple_users(self):
        users = [
            User(user_id=1, activity="browsing", requested_bandwidth=10),
            User(user_id=2, activity="gaming", requested_bandwidth=20),
        ]
        users[0].allocated_bandwidth = 10.0
        users[1].allocated_bandwidth = 15.0
        game = CongestionGame(total_bandwidth=40.0, users=users)
        assert game.total_usage() == 25.0

    def test_total_usage_zero_allocation(self):
        users = [
            User(user_id=1, activity="browsing", requested_bandwidth=10),
            User(user_id=2, activity="gaming", requested_bandwidth=20),
        ]
        game = CongestionGame(total_bandwidth=40.0, users=users)
        assert game.total_usage() == 0.0


class TestGameCalculateUtilities:
    def test_all_users_get_utilities(self):
        users = [
            User(user_id=1, activity="browsing", requested_bandwidth=10),
            User(user_id=2, activity="gaming", requested_bandwidth=20),
        ]
        users[0].allocated_bandwidth = 10.0
        users[1].allocated_bandwidth = 15.0
        game = CongestionGame(total_bandwidth=40.0, users=users)
        game.calculate_utilities()
        assert isinstance(users[0].utility, float)
        assert isinstance(users[1].utility, float)

    def test_calculate_utilities_modifies_user_objects(self):
        users = [
            User(user_id=1, activity="browsing", requested_bandwidth=10),
        ]
        users[0].allocated_bandwidth = 5.0
        game = CongestionGame(total_bandwidth=40.0, users=users)
        game.calculate_utilities()
        assert users[0].utility != 0.0

    def test_game_get_state(self):
        users = [
            User(user_id=1, activity="browsing", requested_bandwidth=10),
            User(user_id=2, activity="gaming", requested_bandwidth=20),
        ]
        users[0].allocated_bandwidth = 8.0
        users[1].allocated_bandwidth = 12.0
        game = CongestionGame(total_bandwidth=40.0, users=users)
        state = game.get_state()
        assert state == {1: 8.0, 2: 12.0}

    def test_game_get_utilities(self):
        users = [
            User(user_id=1, activity="browsing", requested_bandwidth=10),
        ]
        users[0].allocated_bandwidth = 5.0
        game = CongestionGame(total_bandwidth=40.0, users=users)
        game.calculate_utilities()
        utils = game.get_utilities()
        assert 1 in utils
        assert isinstance(utils[1], float)
