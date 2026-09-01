"""
Multi-Seed Experiment Runner

Runs reproducible multi-seed experiments comparing allocation strategies.
Replaces the old single-seed experiment runner for rigorous statistical
comparison.
"""

import csv
import json
import os
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

import numpy as np
import pandas as pd

from backend.experiments.config_schema import ExperimentConfig
from backend.experiments.statistics import compare_strategies
from backend.services.evaluation_service import (
    evaluate_equal,
    evaluate_proportional,
    evaluate_priority,
    evaluate_max_min_fairness,
    evaluate_alpha_fair,
    evaluate_game_theory,
)
from backend.simulation.traffic_generator import generate_traffic_scenario
from backend.data_provenance import SIMULATION, CALCULATED_FROM_REAL_DATA


# ============================================================
# ALGORITHM DISPATCH
# ============================================================

ALGORITHM_EVALUATORS = {
    "equal": lambda users, bw, lat, jit, cfg: evaluate_equal(users, bw, lat, jit),
    "proportional": lambda users, bw, lat, jit, cfg: evaluate_proportional(users, bw, lat, jit),
    "priority": lambda users, bw, lat, jit, cfg: evaluate_priority(users, bw, lat, jit),
    "max_min_fairness": lambda users, bw, lat, jit, cfg: evaluate_max_min_fairness(users, bw, lat, jit),
    "alpha_fair": lambda users, bw, lat, jit, cfg: evaluate_alpha_fair(users, bw, lat, jit, alpha=cfg.alpha),
    "game_theory": lambda users, bw, lat, jit, cfg: evaluate_game_theory(users, bw, lat, jit),
}


# ============================================================
# CREATE DATA DIRECTORY
# ============================================================

def create_data_directory(output_directory: str):
    """
    Create the data directory if it does not exist.

    Parameters
    ----------
    output_directory : str
        Path to the output directory.
    """
    os.makedirs(output_directory, exist_ok=True)


# ============================================================
# RUN SINGLE REPETITION
# ============================================================

def run_single_repetition(
    number_of_users: int,
    algorithm: str,
    config: ExperimentConfig,
    seed: int,
    repetition: int,
) -> Dict[str, Any]:
    """
    Run a single experiment repetition for one (user_count, algorithm) pair.

    Parameters
    ----------
    number_of_users : int
        Number of simulated Wi-Fi users.
    algorithm : str
        Allocation algorithm name.
    config : ExperimentConfig
        Experiment configuration.
    seed : int
        Random seed for this repetition.
    repetition : int
        Repetition index (1-based).

    Returns
    -------
    dict
        Raw result row with metrics and provenance metadata.
    """
    start_time = time.perf_counter()

    sim = generate_traffic_scenario(
        scenario=config.scenario,
        num_users=number_of_users,
        total_bandwidth=config.total_bandwidth,
        seed=seed,
    )

    users = sim["users"]

    rng = __import__("random").Random(seed)
    latency = round(rng.uniform(8.0, 22.0), 2)
    jitter = round(rng.uniform(1.0, 6.0), 2)

    evaluator = ALGORITHM_EVALUATORS.get(algorithm)
    if evaluator is None:
        raise ValueError(f"Unknown algorithm: {algorithm}")

    result = evaluator(users, config.total_bandwidth, latency, jitter, config)

    end_time = time.perf_counter()
    computational_time = round(end_time - start_time, 4)

    metrics = result["metrics"]

    row = {
        "experiment_id": f"exp_{config.seed}_{number_of_users}_{algorithm}_{repetition}",
        "timestamp": datetime.utcnow().isoformat(),
        "seed": seed,
        "number_of_users": number_of_users,
        "strategy": algorithm,
        "total_bandwidth": config.total_bandwidth,
        "total_allocated": metrics.get("total_allocated", 0.0),
        "utilization_percentage": metrics.get("utilization", 0.0),
        "jain_fairness_index": metrics.get("fairness", 0.0),
        "average_utility": metrics.get("average_utility", 0.0),
        "latency_ms": latency,
        "jitter_ms": jitter,
        "repetition": repetition,
        "computational_time": computational_time,
        "convergence_iterations": result.get("convergence_iterations"),
        "converged": result.get("converged"),
        "is_nash_equilibrium": result.get("is_nash_equilibrium"),
        "data_source": SIMULATION,
    }

    return row


# ============================================================
# CALCULATE AGGREGATED STATISTICS
# ============================================================

def calculate_aggregated_statistics(raw_results: list) -> list:
    """
    Calculate aggregated statistics for each (user_count, algorithm) group.

    Parameters
    ----------
    raw_results : list
        List of raw result dictionaries.

    Returns
    -------
    list
        List of aggregated result dictionaries.
    """
    if not raw_results:
        return []

    df = pd.DataFrame(raw_results)

    metrics = [
        "total_allocated",
        "utilization_percentage",
        "jain_fairness_index",
        "average_utility",
        "computational_time",
        "convergence_iterations",
    ]

    grouped = df.groupby(["number_of_users", "strategy"])

    aggregated = []

    for (user_count, strategy), group in grouped:
        row = {
            "number_of_users": user_count,
            "strategy": strategy,
            "n": len(group),
        }

        for metric in metrics:
            values = group[metric].dropna().astype(float)

            if len(values) == 0:
                row[f"{metric}_mean"] = None
                row[f"{metric}_median"] = None
                row[f"{metric}_std_dev"] = None
                row[f"{metric}_min"] = None
                row[f"{metric}_max"] = None
                row[f"{metric}_ci_95_lower"] = None
                row[f"{metric}_ci_95_upper"] = None
                continue

            row[f"{metric}_mean"] = round(float(values.mean()), 6)
            row[f"{metric}_median"] = round(float(values.median()), 6)
            row[f"{metric}_std_dev"] = round(float(values.std(ddof=1)), 6) if len(values) > 1 else 0.0
            row[f"{metric}_min"] = round(float(values.min()), 6)
            row[f"{metric}_max"] = round(float(values.max()), 6)

            if len(values) > 1:
                ci_lower, ci_upper = calculate_confidence_interval(values)
                row[f"{metric}_ci_95_lower"] = round(ci_lower, 6)
                row[f"{metric}_ci_95_upper"] = round(ci_upper, 6)
            else:
                row[f"{metric}_ci_95_lower"] = None
                row[f"{metric}_ci_95_upper"] = None

        aggregated.append(row)

    return aggregated


def calculate_confidence_interval(values, confidence: float = 0.95):
    """
    Calculate the confidence interval for a sample.

    Parameters
    ----------
    values : array-like
        Sample values.
    confidence : float
        Confidence level (default 0.95).

    Returns
    -------
    tuple
        (lower_bound, upper_bound)
    """
    from scipy import stats as scipy_stats

    arr = np.array(values, dtype=float)
    n = len(arr)
    mean = float(np.mean(arr))
    sem = scipy_stats.sem(arr)
    if sem == 0:
        return mean, mean

    interval = scipy_stats.t.interval(confidence, n - 1, loc=mean, scale=sem)
    return float(interval[0]), float(interval[1])


# ============================================================
# RUN MULTI-SEED EXPERIMENT
# ============================================================

def run_multi_seed_experiment(config: ExperimentConfig) -> Dict[str, Any]:
    """
    Run a full multi-seed reproducible experiment.

    Parameters
    ----------
    config : ExperimentConfig
        Experiment configuration.

    Returns
    -------
    dict
        Experiment results including raw_results, aggregated_results,
        config, and provenance metadata.
    """
    create_data_directory(config.output_directory)

    raw_results = []

    seeds = config.get_seeds()

    total_runs = len(config.user_counts) * len(config.algorithms) * len(seeds)
    completed = 0

    for number_of_users in config.user_counts:
        for algorithm in config.algorithms:
            for rep_idx, seed in enumerate(seeds, start=1):
                row = run_single_repetition(
                    number_of_users=number_of_users,
                    algorithm=algorithm,
                    config=config,
                    seed=seed,
                    repetition=rep_idx,
                )
                raw_results.append(row)
                completed += 1

    aggregated = calculate_aggregated_statistics(raw_results)

    save_raw_results(raw_results, config.output_directory)
    save_aggregated_results(aggregated, config.output_directory)
    save_experiment_config(config, config.output_directory)

    from backend.experiments.statistics import (
        run_all_pairwise_comparisons,
        calculate_nash_statistics,
        save_statistical_results,
    )

    comparisons = run_all_pairwise_comparisons(raw_results)
    nash_stats = calculate_nash_statistics(raw_results)
    stat_paths = save_statistical_results(comparisons, nash_stats, config.output_directory)

    return {
        "status": "success",
        "config": config.to_dict(),
        "raw_results": raw_results,
        "aggregated_results": aggregated,
        "total_raw_rows": len(raw_results),
        "total_aggregated_rows": len(aggregated),
        "statistical_results": comparisons,
        "nash_statistics": nash_stats,
        "statistical_output_files": stat_paths,
        "provenance": {
            "user_demand": SIMULATION,
            "allocation": CALCULATED_FROM_REAL_DATA,
            "metrics": CALCULATED_FROM_REAL_DATA,
            "fairness": CALCULATED_FROM_REAL_DATA,
        },
    }


# ============================================================
# SAVE RESULTS
# ============================================================

def compare_algorithms(
    raw_results: list,
    baseline: str,
    proposed: str,
    metric: str = "average_utility",
) -> Dict[str, Any]:
    """
    Compare two algorithms using statistical tests.

    Thin wrapper around ``backend.experiments.statistics.compare_strategies``
    that operates on the raw result rows produced by this runner.

    Parameters
    ----------
    raw_results : list
        List of raw result dictionaries (one per repetition).
    baseline : str
        Name of the baseline algorithm (e.g. ``"equal"``).
    proposed : str
        Name of the proposed algorithm (e.g. ``"game_theory"``).
    metric : str
        Metric to compare.

    Returns
    -------
    dict
        Statistical comparison results.
    """
    return compare_strategies(
        raw_results,
        metric=metric,
        baseline=baseline,
        proposed=proposed,
    )


# ============================================================
# SAVE RESULTS
# ============================================================

def save_raw_results(raw_results: list, output_directory: str):
    """
    Save raw results to data/raw_results.csv.

    Parameters
    ----------
    raw_results : list
        List of raw result dictionaries.
    output_directory : str
        Directory to save files.
    """
    create_data_directory(output_directory)

    fieldnames = [
        "experiment_id",
        "timestamp",
        "seed",
        "number_of_users",
        "strategy",
        "total_bandwidth",
        "total_allocated",
        "utilization_percentage",
        "jain_fairness_index",
        "average_utility",
        "latency_ms",
        "jitter_ms",
        "repetition",
        "computational_time",
        "convergence_iterations",
        "converged",
        "is_nash_equilibrium",
        "data_source",
    ]

    filepath = os.path.join(output_directory, "raw_results.csv")

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(raw_results)


def save_aggregated_results(aggregated: list, output_directory: str):
    """
    Save aggregated results to data/aggregated_results.csv.

    Parameters
    ----------
    aggregated : list
        List of aggregated result dictionaries.
    output_directory : str
        Directory to save files.
    """
    create_data_directory(output_directory)

    if not aggregated:
        return

    fieldnames = list(aggregated[0].keys())
    filepath = os.path.join(output_directory, "aggregated_results.csv")

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(aggregated)


def save_experiment_config(config: ExperimentConfig, output_directory: str):
    """
    Save experiment configuration to data/experiment_config.json.

    Parameters
    ----------
    config : ExperimentConfig
        Experiment configuration.
    output_directory : str
        Directory to save files.
    """
    create_data_directory(output_directory)

    filepath = os.path.join(output_directory, "experiment_config.json")

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(config.to_dict(), f, indent=2)
