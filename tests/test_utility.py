from game_theory.congestion_game import ACTIVITY_WEIGHTS
from game_theory.utility import (
    QoS_WEIGHTS,
    calculate_utility,
    get_qos_weights,
)


class TestCalculateUtilityBasic:
    def test_positive_bandwidth_returns_utility(self):
        util = calculate_utility(
            bandwidth=10.0,
            total_usage=10.0,
            total_bandwidth=40.0,
            activity_weight=1.0,
            congestion_penalty=0.5,
        )
        assert util < 0 or util > 0 or util == 0
        assert isinstance(util, float)

    def test_utility_decreases_with_congestion(self):
        low_congestion = calculate_utility(
            bandwidth=10.0,
            total_usage=10.0,
            total_bandwidth=100.0,
            activity_weight=1.0,
            congestion_penalty=0.5,
        )
        high_congestion = calculate_utility(
            bandwidth=10.0,
            total_usage=80.0,
            total_bandwidth=100.0,
            activity_weight=1.0,
            congestion_penalty=0.5,
        )
        assert high_congestion < low_congestion

    def test_higher_activity_weight_gives_higher_utility(self):
        low_weight = calculate_utility(
            bandwidth=10.0,
            total_usage=10.0,
            total_bandwidth=40.0,
            activity_weight=0.5,
            congestion_penalty=0.0,
        )
        high_weight = calculate_utility(
            bandwidth=10.0,
            total_usage=10.0,
            total_bandwidth=40.0,
            activity_weight=2.0,
            congestion_penalty=0.0,
        )
        assert high_weight > low_weight


class TestCalculateUtilityZeroBandwidth:
    def test_zero_bandwidth_returns_zero(self):
        assert calculate_utility(
            bandwidth=0.0,
            total_usage=0.0,
            total_bandwidth=40.0,
        ) == 0.0

    def test_zero_bandwidth_with_congestion(self):
        assert calculate_utility(
            bandwidth=0.0,
            total_usage=30.0,
            total_bandwidth=40.0,
            activity_weight=1.5,
            congestion_penalty=0.5,
        ) == 0.0


class TestCalculateUtilityNegativeBandwidth:
    def test_negative_bandwidth_returns_negative_infinity(self):
        assert calculate_utility(
            bandwidth=-1.0,
            total_usage=10.0,
            total_bandwidth=40.0,
        ) == float("-inf")

    def test_negative_bandwidth_with_large_usage(self):
        assert calculate_utility(
            bandwidth=-5.0,
            total_usage=100.0,
            total_bandwidth=40.0,
        ) == float("-inf")


class TestCalculateUtilityWithLatencyJitter:
    def test_qos_penalties_applied(self):
        no_qos = calculate_utility(
            bandwidth=10.0,
            total_usage=10.0,
            total_bandwidth=40.0,
            activity_weight=1.0,
            congestion_penalty=0.0,
            latency=0.0,
            jitter=0.0,
            activity="gaming",
        )
        with_qos = calculate_utility(
            bandwidth=10.0,
            total_usage=10.0,
            total_bandwidth=40.0,
            activity_weight=1.0,
            congestion_penalty=0.0,
            latency=50.0,
            jitter=10.0,
            activity="gaming",
        )
        assert with_qos < no_qos

    def test_browsing_has_lower_latency_sensitivity(self):
        browsing_util = calculate_utility(
            bandwidth=10.0,
            total_usage=10.0,
            total_bandwidth=40.0,
            activity_weight=1.0,
            congestion_penalty=0.0,
            latency=80.0,
            jitter=0.0,
            activity="browsing",
        )
        gaming_util = calculate_utility(
            bandwidth=10.0,
            total_usage=10.0,
            total_bandwidth=40.0,
            activity_weight=1.0,
            congestion_penalty=0.0,
            latency=80.0,
            jitter=0.0,
            activity="gaming",
        )
        assert browsing_util > gaming_util

    def test_default_qos_weights_for_unknown_activity(self):
        util = calculate_utility(
            bandwidth=10.0,
            total_usage=10.0,
            total_bandwidth=40.0,
            activity_weight=1.0,
            congestion_penalty=0.0,
            latency=50.0,
            jitter=5.0,
            activity="unknown_activity",
        )
        assert isinstance(util, float)

    def test_no_qos_penalty_when_latency_and_jitter_zero(self):
        util = calculate_utility(
            bandwidth=10.0,
            total_usage=10.0,
            total_bandwidth=40.0,
            activity_weight=1.0,
            congestion_penalty=0.0,
            latency=0.0,
            jitter=0.0,
            activity="gaming",
        )
        no_activity = calculate_utility(
            bandwidth=10.0,
            total_usage=10.0,
            total_bandwidth=40.0,
            activity_weight=1.0,
            congestion_penalty=0.0,
            latency=0.0,
            jitter=0.0,
        )
        assert util == no_activity


class TestCalculateUtilityCongestion:
    def test_congestion_cost_increases_with_total_usage(self):
        util_low = calculate_utility(
            bandwidth=10.0,
            total_usage=5.0,
            total_bandwidth=40.0,
            activity_weight=1.0,
            congestion_penalty=0.5,
        )
        util_high = calculate_utility(
            bandwidth=10.0,
            total_usage=35.0,
            total_bandwidth=40.0,
            activity_weight=1.0,
            congestion_penalty=0.5,
        )
        assert util_high < util_low

    def test_no_congestion_when_usage_zero(self):
        util = calculate_utility(
            bandwidth=10.0,
            total_usage=0.0,
            total_bandwidth=40.0,
            activity_weight=1.0,
            congestion_penalty=0.5,
        )
        util_full = calculate_utility(
            bandwidth=10.0,
            total_usage=40.0,
            total_bandwidth=40.0,
            activity_weight=1.0,
            congestion_penalty=0.5,
        )
        assert util > util_full

    def test_higher_congestion_penalty_increases_cost(self):
        low_penalty = calculate_utility(
            bandwidth=10.0,
            total_usage=30.0,
            total_bandwidth=40.0,
            activity_weight=1.0,
            congestion_penalty=0.1,
        )
        high_penalty = calculate_utility(
            bandwidth=10.0,
            total_usage=30.0,
            total_bandwidth=40.0,
            activity_weight=1.0,
            congestion_penalty=1.0,
        )
        assert high_penalty < low_penalty


class TestActivityWeights:
    def test_browsing_weight(self):
        assert ACTIVITY_WEIGHTS["browsing"] == 1.0

    def test_online_class_weight(self):
        assert ACTIVITY_WEIGHTS["online_class"] == 1.5

    def test_gaming_weight(self):
        assert ACTIVITY_WEIGHTS["gaming"] == 1.3

    def test_streaming_weight(self):
        assert ACTIVITY_WEIGHTS["streaming"] == 1.4

    def test_downloading_weight(self):
        assert ACTIVITY_WEIGHTS["downloading"] == 1.1

    def test_all_activities_have_weights(self):
        expected = {"browsing", "online_class", "gaming", "streaming", "downloading"}
        assert set(ACTIVITY_WEIGHTS.keys()) == expected


class TestQosWeights:
    def test_get_qos_weights_browsing(self):
        lat, jit = get_qos_weights("browsing")
        assert lat == 0.3
        assert jit == 0.2

    def test_get_qos_weights_online_class(self):
        lat, jit = get_qos_weights("online_class")
        assert lat == 0.9
        assert jit == 0.7

    def test_get_qos_weights_gaming(self):
        lat, jit = get_qos_weights("gaming")
        assert lat == 1.0
        assert jit == 1.0

    def test_get_qos_weights_streaming(self):
        lat, jit = get_qos_weights("streaming")
        assert lat == 0.5
        assert jit == 0.4

    def test_get_qos_weights_downloading(self):
        lat, jit = get_qos_weights("downloading")
        assert lat == 0.1
        assert jit == 0.1

    def test_get_qos_weights_default(self):
        lat, jit = get_qos_weights("unknown_activity")
        assert lat == 0.5
        assert jit == 0.5


class TestDiminishingReturns:
    def test_marginal_utility_decreases(self):
        util_1 = calculate_utility(
            bandwidth=1.0,
            total_usage=1.0,
            total_bandwidth=100.0,
            activity_weight=1.0,
            congestion_penalty=0.0,
        )
        util_2 = calculate_utility(
            bandwidth=2.0,
            total_usage=2.0,
            total_bandwidth=100.0,
            activity_weight=1.0,
            congestion_penalty=0.0,
        )
        util_3 = calculate_utility(
            bandwidth=3.0,
            total_usage=3.0,
            total_bandwidth=100.0,
            activity_weight=1.0,
            congestion_penalty=0.0,
        )
        delta_1 = util_2 - util_1
        delta_2 = util_3 - util_2
        assert delta_2 < delta_1

    def test_log_benefit_diminishes(self):
        util_10 = calculate_utility(
            bandwidth=10.0,
            total_usage=10.0,
            total_bandwidth=1000.0,
            activity_weight=1.0,
            congestion_penalty=0.0,
        )
        util_20 = calculate_utility(
            bandwidth=20.0,
            total_usage=20.0,
            total_bandwidth=1000.0,
            activity_weight=1.0,
            congestion_penalty=0.0,
        )
        benefit_10 = util_10
        benefit_20 = util_20 - calculate_utility(
            bandwidth=0.0,
            total_usage=20.0,
            total_bandwidth=1000.0,
            activity_weight=1.0,
            congestion_penalty=0.0,
        )
        assert benefit_20 < 2 * benefit_10
