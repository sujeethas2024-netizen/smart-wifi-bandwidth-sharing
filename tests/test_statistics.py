import csv
import json
import os

import numpy as np
import pytest

from backend.experiments.statistics import (
    build_paired_groups,
    paired_t_test,
    wilcoxon_signed_rank_test,
    mann_whitney_u_test,
    cohens_d,
    confidence_interval,
    benjamini_hochberg_correction,
    paired_comparison,
    run_all_pairwise_comparisons,
    calculate_nash_statistics,
    save_statistical_results,
)


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def raw_results_with_nash():
    return [
        {"seed": 42, "number_of_users": 10, "strategy": "game_theory", "average_utility": 1.0, "jain_fairness_index": 0.9, "utilization_percentage": 80.0, "computational_time": 0.01, "convergence_iterations": 4, "converged": True, "is_nash_equilibrium": True},
        {"seed": 43, "number_of_users": 10, "strategy": "game_theory", "average_utility": 1.2, "jain_fairness_index": 0.85, "utilization_percentage": 85.0, "computational_time": 0.012, "convergence_iterations": 5, "converged": True, "is_nash_equilibrium": True},
        {"seed": 44, "number_of_users": 10, "strategy": "game_theory", "average_utility": 0.9, "jain_fairness_index": 0.88, "utilization_percentage": 75.0, "computational_time": 0.009, "convergence_iterations": 3, "converged": True, "is_nash_equilibrium": True},
        {"seed": 42, "number_of_users": 10, "strategy": "equal", "average_utility": -1.0, "jain_fairness_index": 1.0, "utilization_percentage": 100.0, "computational_time": 0.001},
        {"seed": 43, "number_of_users": 10, "strategy": "equal", "average_utility": -1.1, "jain_fairness_index": 1.0, "utilization_percentage": 100.0, "computational_time": 0.001},
        {"seed": 44, "number_of_users": 10, "strategy": "equal", "average_utility": -0.9, "jain_fairness_index": 1.0, "utilization_percentage": 100.0, "computational_time": 0.001},
        {"seed": 42, "number_of_users": 20, "strategy": "game_theory", "average_utility": 0.8, "jain_fairness_index": 0.95, "utilization_percentage": 90.0, "computational_time": 0.02, "convergence_iterations": 6, "converged": True, "is_nash_equilibrium": True},
        {"seed": 43, "number_of_users": 20, "strategy": "game_theory", "average_utility": 0.85, "jain_fairness_index": 0.92, "utilization_percentage": 92.0, "computational_time": 0.021, "convergence_iterations": 7, "converged": True, "is_nash_equilibrium": True},
        {"seed": 42, "number_of_users": 20, "strategy": "equal", "average_utility": -0.5, "jain_fairness_index": 1.0, "utilization_percentage": 100.0, "computational_time": 0.002},
        {"seed": 43, "number_of_users": 20, "strategy": "equal", "average_utility": -0.6, "jain_fairness_index": 1.0, "utilization_percentage": 100.0, "computational_time": 0.002},
    ]


# ============================================================
# PAIRING TESTS
# ============================================================

class TestBuildPairedGroups:
    def test_returns_equal_lengths(self, raw_results_with_nash):
        b, p, n = build_paired_groups(raw_results_with_nash, "average_utility", "equal", "game_theory")
        assert len(b) == len(p)
        assert n == len(b)

    def test_preserves_seed_and_user_count_pairing(self, raw_results_with_nash):
        b, p, n = build_paired_groups(raw_results_with_nash, "average_utility", "equal", "game_theory")
        assert n == 5  # 3 pairs for user_count=10, 2 pairs for user_count=20

    def test_skips_missing_pairs(self, raw_results_with_nash):
        b, p, n = build_paired_groups(raw_results_with_nash, "average_utility", "priority", "game_theory")
        assert n == 0

    def test_handles_missing_metric(self):
        data = [
            {"seed": 1, "number_of_users": 10, "strategy": "a", "average_utility": 1.0},
            {"seed": 1, "number_of_users": 10, "strategy": "b", "average_utility": 2.0},
        ]
        b, p, n = build_paired_groups(data, "jain_fairness_index", "a", "b")
        assert n == 0


# ============================================================
# STATISTICAL TEST TESTS
# ============================================================

class TestPairedTTest:
    def test_significant_difference(self):
        a = [1.0, 2.0, 3.0]
        b = [4.0, 5.0, 6.0]
        result = paired_t_test(a, b)
        assert result["t_statistic"] is not None
        assert result["p_value"] < 0.05

    def test_no_difference(self):
        a = [1.0, 2.0, 3.0]
        b = [1.0, 2.0, 3.0]
        result = paired_t_test(a, b)
        p = result["p_value"]
        assert p is None or (isinstance(p, float) and (p > 0.05 or np.isnan(p)))

    def test_small_sample_warning(self):
        result = paired_t_test([1.0], [2.0])
        assert result["warning"] is not None

    def test_mismatched_length_warning(self):
        result = paired_t_test([1.0, 2.0], [3.0])
        assert result["warning"] is not None


class TestWilcoxonSignedRank:
    def test_significant_difference(self):
        a = [1.0, 2.0, 3.0, 4.0, 5.0]
        b = [2.0, 3.0, 4.0, 5.0, 6.0]
        result = wilcoxon_signed_rank_test(a, b)
        assert result["w_statistic"] is not None
        assert result["p_value"] is not None

    def test_small_sample_warning(self):
        result = wilcoxon_signed_rank_test([1.0], [2.0])
        assert result["warning"] is not None


class TestMannWhitneyU:
    def test_runs_without_error(self):
        a = [1.0, 2.0, 3.0]
        b = [4.0, 5.0, 6.0]
        result = mann_whitney_u_test(a, b)
        assert result["u_statistic"] is not None


class TestCohensD:
    def test_large_effect(self):
        a = [1.0, 2.0, 3.0]
        b = [10.0, 11.0, 12.0]
        result = cohens_d(a, b)
        assert result["cohens_d"] is not None
        assert abs(result["cohens_d"]) > 0.8

    def test_small_effect(self):
        a = [1.0, 2.0, 3.0]
        b = [1.1, 2.1, 3.1]
        result = cohens_d(a, b)
        assert result["cohens_d"] is not None
        assert abs(result["cohens_d"]) < 0.5


class TestConfidenceInterval:
    def test_ci_contains_true_difference(self):
        a = [1.0, 2.0, 3.0, 4.0, 5.0]
        b = [1.5, 2.5, 3.5, 4.5, 5.5]
        result = confidence_interval(a, b)
        assert result["ci_lower"] is not None
        assert result["ci_upper"] is not None
        assert result["mean_difference"] == pytest.approx(-0.5)

    def test_small_sample_warning(self):
        result = confidence_interval([1.0], [2.0])
        assert result["warning"] is not None


# ============================================================
# MULTIPLE COMPARISON TESTS
# ============================================================

class TestBenjaminiHochberg:
    def test_basic_correction(self):
        p = [0.01, 0.05, 0.10, 0.50]
        adjusted = benjamini_hochberg_correction(p)
        assert len(adjusted) == 4
        assert all(0.0 <= p <= 1.0 for p in adjusted)

    def test_monotonicity(self):
        p = [0.01, 0.02, 0.03, 0.04]
        adjusted = benjamini_hochberg_correction(p)
        for i in range(len(adjusted) - 1):
            assert adjusted[i] <= adjusted[i + 1] + 1e-9

    def test_empty_input(self):
        assert benjamini_hochberg_correction([]) == []


# ============================================================
# PAIRED COMPARISON TESTS
# ============================================================

class TestPairedComparison:
    def test_returns_expected_keys(self, raw_results_with_nash):
        result = paired_comparison(raw_results_with_nash, "average_utility", "equal", "game_theory")
        assert "baseline" in result
        assert "proposed" in result
        assert "metric" in result
        assert "sample_size" in result
        assert "paired_t_test" in result
        assert "wilcoxon_signed_rank" in result
        assert "cohens_d" in result
        assert "confidence_interval" in result

    def test_correct_pairing(self, raw_results_with_nash):
        result = paired_comparison(raw_results_with_nash, "average_utility", "equal", "game_theory")
        assert result["sample_size"] == 5  # 3 for n=10, 2 for n=20

    def test_mean_difference_sign(self, raw_results_with_nash):
        result = paired_comparison(raw_results_with_nash, "average_utility", "equal", "game_theory")
        assert result["mean_difference"] < 0  # equal has lower utility


# ============================================================
# FULL PAIRWISE COMPARISON TESTS
# ============================================================

class TestRunAllPairwiseComparisons:
    def test_returns_list(self, raw_results_with_nash):
        results = run_all_pairwise_comparisons(raw_results_with_nash)
        assert isinstance(results, list)

    def test_comparison_count(self, raw_results_with_nash):
        results = run_all_pairwise_comparisons(raw_results_with_nash)
        expected = 5 * 4  # 5 baselines x 4 metrics
        assert len(results) == expected

    def test_all_have_adjusted_p_value(self, raw_results_with_nash):
        results = run_all_pairwise_comparisons(raw_results_with_nash)
        for r in results:
            assert "adjusted_p_value" in r
            assert 0.0 <= r["adjusted_p_value"] <= 1.0


# ============================================================
# NASH STATISTICS TESTS
# ============================================================

class TestCalculateNashStatistics:
    def test_basic_stats(self, raw_results_with_nash):
        stats = calculate_nash_statistics(raw_results_with_nash)
        assert stats["total_runs"] == 5
        assert stats["convergence_rate"] == 1.0
        assert stats["nash_verification_rate"] == 1.0
        assert stats["mean_iterations"] is not None
        assert stats["min_iterations"] is not None
        assert stats["max_iterations"] is not None

    def test_by_user_count_breakdown(self, raw_results_with_nash):
        stats = calculate_nash_statistics(raw_results_with_nash)
        assert 10 in stats["by_user_count"]
        assert 20 in stats["by_user_count"]
        assert stats["by_user_count"][10]["total"] == 3
        assert stats["by_user_count"][20]["total"] == 2

    def test_empty_when_no_game_theory(self):
        data = [
            {"seed": 1, "number_of_users": 10, "strategy": "equal", "average_utility": 1.0},
        ]
        stats = calculate_nash_statistics(data)
        assert stats["total_runs"] == 0
        assert stats["convergence_rate"] is None

    def test_missing_nash_fields_skipped(self):
        data = [
            {"seed": 1, "number_of_users": 10, "strategy": "game_theory", "average_utility": 1.0},
        ]
        stats = calculate_nash_statistics(data)
        assert stats["total_runs"] == 0


# ============================================================
# OUTPUT GENERATION TESTS
# ============================================================

class TestSaveStatisticalResults:
    def test_creates_csv_and_json(self, tmp_path, raw_results_with_nash):
        comparisons = run_all_pairwise_comparisons(raw_results_with_nash)
        nash_stats = calculate_nash_statistics(raw_results_with_nash)
        paths = save_statistical_results(comparisons, nash_stats, output_directory=str(tmp_path))
        assert os.path.exists(paths["csv"])
        assert os.path.exists(paths["json"])

    def test_csv_has_correct_headers(self, tmp_path, raw_results_with_nash):
        comparisons = run_all_pairwise_comparisons(raw_results_with_nash)
        nash_stats = calculate_nash_statistics(raw_results_with_nash)
        paths = save_statistical_results(comparisons, nash_stats, output_directory=str(tmp_path))
        with open(paths["csv"], "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
        assert "metric" in fieldnames
        assert "algorithm_a" in fieldnames
        assert "algorithm_b" in fieldnames
        assert "p_value" in fieldnames
        assert "adjusted_p_value" in fieldnames

    def test_json_contains_nash_statistics(self, tmp_path, raw_results_with_nash):
        comparisons = run_all_pairwise_comparisons(raw_results_with_nash)
        nash_stats = calculate_nash_statistics(raw_results_with_nash)
        paths = save_statistical_results(comparisons, nash_stats, output_directory=str(tmp_path))
        with open(paths["json"], "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "nash_statistics" in data
        assert data["nash_statistics"]["total_runs"] == 5
