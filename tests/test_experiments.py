import os

import pytest

from simulation.experiment_runner import (
    create_csv_rows,
    get_experiment_config,
    run_single_experiment,
    save_results_to_csv,
    set_experiment_config,
)


class TestSingleExperimentRuns:
    def test_runs_without_error(self):
        results = run_single_experiment(
            number_of_users=3,
            total_bandwidth=40.0,
            seed=42,
            scenario="medium",
        )
        assert results is not None
        assert len(results) == 6

    def test_returns_list_of_results(self):
        results = run_single_experiment(
            number_of_users=5,
            total_bandwidth=50.0,
            seed=42,
            scenario="low",
        )
        assert isinstance(results, list)

    def test_custom_user_count(self):
        results = run_single_experiment(
            number_of_users=7,
            total_bandwidth=50.0,
            seed=42,
            scenario="medium",
        )
        assert len(results) == 6


class TestExperimentResultsStructure:
    def test_results_have_expected_keys(self):
        results = run_single_experiment(
            number_of_users=3,
            total_bandwidth=40.0,
            seed=42,
            scenario="medium",
        )
        for result in results:
            assert "strategy" in result
            assert "allocations" in result
            assert "metrics" in result

    def test_metrics_have_expected_keys(self):
        results = run_single_experiment(
            number_of_users=3,
            total_bandwidth=40.0,
            seed=42,
            scenario="medium",
        )
        for result in results:
            metrics = result["metrics"]
            assert "total_allocated" in metrics
            assert "utilization" in metrics
            assert "fairness" in metrics
            assert "average_utility" in metrics

    def test_allocations_is_dict(self):
        results = run_single_experiment(
            number_of_users=3,
            total_bandwidth=40.0,
            seed=42,
            scenario="medium",
        )
        for result in results:
            assert isinstance(result["allocations"], dict)

    def test_strategy_names(self):
        results = run_single_experiment(
            number_of_users=3,
            total_bandwidth=40.0,
            seed=42,
            scenario="medium",
        )
        strategy_names = [r["strategy"] for r in results]
        assert "Equal Allocation" in strategy_names
        assert "Proportional Allocation" in strategy_names
        assert "Priority Allocation" in strategy_names
        assert "Game Theory" in strategy_names


class TestCsvOutputCreated:
    def test_csv_file_created(self, tmp_path):
        results = run_single_experiment(
            number_of_users=3,
            total_bandwidth=40.0,
            seed=42,
            scenario="medium",
        )
        rows = create_csv_rows(3, results, seed=42)
        output_file = tmp_path / "test_output.csv"
        save_results_to_csv(rows, filename=str(output_file))
        assert output_file.exists()

    def test_csv_has_header(self, tmp_path):
        results = run_single_experiment(
            number_of_users=3,
            total_bandwidth=40.0,
            seed=42,
            scenario="medium",
        )
        rows = create_csv_rows(3, results, seed=42)
        output_file = tmp_path / "test_output.csv"
        save_results_to_csv(rows, filename=str(output_file))
        with open(output_file, "r", encoding="utf-8") as f:
            header = f.readline()
        assert "strategy" in header
        assert "number_of_users" in header


class TestMultiSeedReproducibility:
    def test_same_seed_same_results(self):
        results1 = run_single_experiment(
            number_of_users=5,
            total_bandwidth=40.0,
            seed=42,
            scenario="medium",
        )
        results2 = run_single_experiment(
            number_of_users=5,
            total_bandwidth=40.0,
            seed=42,
            scenario="medium",
        )
        for r1, r2 in zip(results1, results2):
            assert r1["strategy"] == r2["strategy"]
            assert r1["allocations"] == r2["allocations"]

    def test_different_seeds_may_differ(self):
        results1 = run_single_experiment(
            number_of_users=10,
            total_bandwidth=40.0,
            seed=1,
            scenario="medium",
        )
        results2 = run_single_experiment(
            number_of_users=10,
            total_bandwidth=40.0,
            seed=2,
            scenario="medium",
        )
        assert len(results1) == len(results2)


class TestNashMetricsInExperimentOutput:
    def test_game_theory_has_convergence_iterations(self):
        results = run_single_experiment(
            number_of_users=5,
            total_bandwidth=40.0,
            seed=42,
            scenario="medium",
        )
        gt = [r for r in results if r["strategy"] == "Game Theory"][0]
        assert "convergence_iterations" in gt
        assert isinstance(gt["convergence_iterations"], int)
        assert gt["convergence_iterations"] > 0

    def test_game_theory_has_converged_flag(self):
        results = run_single_experiment(
            number_of_users=5,
            total_bandwidth=40.0,
            seed=42,
            scenario="medium",
        )
        gt = [r for r in results if r["strategy"] == "Game Theory"][0]
        assert "converged" in gt
        assert isinstance(gt["converged"], bool)

    def test_game_theory_has_nash_verification(self):
        results = run_single_experiment(
            number_of_users=5,
            total_bandwidth=40.0,
            seed=42,
            scenario="medium",
        )
        gt = [r for r in results if r["strategy"] == "Game Theory"][0]
        assert "is_nash_equilibrium" in gt
        assert isinstance(gt["is_nash_equilibrium"], bool)

    def test_non_game_theory_rows_have_no_fabricated_nash_metrics(self):
        results = run_single_experiment(
            number_of_users=5,
            total_bandwidth=40.0,
            seed=42,
            scenario="medium",
        )
        non_gt = [r for r in results if r["strategy"] != "Game Theory"]
        for r in non_gt:
            assert r.get("convergence_iterations") is None
            assert r.get("converged") is None
            assert r.get("is_nash_equilibrium") is None

    def test_existing_metrics_unchanged(self):
        results = run_single_experiment(
            number_of_users=5,
            total_bandwidth=40.0,
            seed=42,
            scenario="medium",
        )
        for r in results:
            metrics = r["metrics"]
            assert "total_allocated" in metrics
            assert "utilization" in metrics
            assert "fairness" in metrics
            assert "average_utility" in metrics

    def test_csv_rows_include_nash_fields_for_game_theory(self):
        results = run_single_experiment(
            number_of_users=5,
            total_bandwidth=40.0,
            seed=42,
            scenario="medium",
        )
        rows = create_csv_rows(5, results, seed=42)
        gt_rows = [r for r in rows if r["strategy"] == "Game Theory"]
        assert len(gt_rows) == 1
        gt_row = gt_rows[0]
        assert "convergence_iterations" in gt_row
        assert "converged" in gt_row
        assert "is_nash_equilibrium" in gt_row

    def test_csv_rows_have_null_nash_fields_for_baselines(self):
        results = run_single_experiment(
            number_of_users=5,
            total_bandwidth=40.0,
            seed=42,
            scenario="medium",
        )
        rows = create_csv_rows(5, results, seed=42)
        baseline_rows = [r for r in rows if r["strategy"] != "Game Theory"]
        for r in baseline_rows:
            assert r.get("convergence_iterations") is None
            assert r.get("converged") is None
            assert r.get("is_nash_equilibrium") is None
