"""
Sensitivity Analysis

Varies a single utility weight across a range of values and re-runs
multi-seed experiments to record how fairness, utility, and utilization
respond.

Supported weight parameters:
    - w_throughput
    - w_latency
    - w_jitter
    - w_congestion
    - w_qos

The weighted utility recomputes per-user utility with the supplied
weights so that the effect of each parameter is isolated.
"""

import csv
import math
import os
import time
from datetime import datetime
from typing import Dict, Any, List

import numpy as np
import pandas as pd

from backend.experiments.config_schema import ExperimentConfig
from backend.experiments.runner import ALGORITHM_EVALUATORS, create_data_directory
from backend.simulation.traffic_generator import generate_traffic_scenario
from backend.game_theory.utility import get_qos_weights
from backend.game_theory.fairness import jains_fairness_index
from backend.data_provenance import SIMULATION, CALCULATED_FROM_REAL_DATA


# ============================================================
# SUPPORTED PARAMETERS
# ============================================================

SENSITIVITY_PARAMETERS = [
    "w_throughput",
    "w_latency",
    "w_jitter",
    "w_congestion",
    "w_qos",
]


# ============================================================
# WEIGHTED UTILITY
# ============================================================

def weighted_utility(
    bandwidth: float,
    total_usage: float,
    total_bandwidth: float,
    activity_weight: float,
    latency: float,
    jitter: float,
    activity: str,
    weights: Dict[str, float],
) -> float:
    """
    Compute utility with explicit per-term weights.

    Parameters
    ----------
    bandwidth : float
        Allocated bandwidth for the user.
    total_usage : float
        Total bandwidth used by all users.
    total_bandwidth : float
        Total network bandwidth.
    activity_weight : float
        Activity weight for the benefit term.
    latency : float
        Latency (ms).
    jitter : float
        Jitter (ms).
    activity : str
        Activity name (for QoS sensitivity weights).
    weights : dict
        Weight mapping with keys w_throughput, w_latency, w_jitter,
        w_congestion, w_qos.

    Returns
    -------
    float
        Weighted utility.
    """
    if bandwidth < 0:
        return float("-inf")
    if total_bandwidth <= 0:
        return float("-inf")
    if bandwidth == 0:
        return 0.0

    benefit = activity_weight * math.log(1 + bandwidth)

    congestion_ratio = total_usage / total_bandwidth
    congestion_cost = bandwidth * congestion_ratio

    lat_pen = 0.0
    jit_pen = 0.0
    if latency > 0 or jitter > 0:
        lat_w, jit_w = get_qos_weights(activity) if activity else (0.5, 0.5)
        lat_norm = min(latency / 100.0, 1.0)
        jit_norm = min(jitter / 20.0, 1.0)
        lat_pen = lat_w * lat_norm * 0.5 * bandwidth
        jit_pen = jit_w * jit_norm * 0.3 * bandwidth

    qos_violation = lat_pen + jit_pen

    utility = (
        weights["w_throughput"] * benefit
        - weights["w_congestion"] * congestion_cost
        - weights["w_latency"] * lat_pen
        - weights["w_jitter"] * jit_pen
        - weights["w_qos"] * qos_violation
    )

    return utility


# ============================================================
# COMPUTE WEIGHTED METRICS
# ============================================================

def compute_weighted_metrics(
    allocations: dict,
    users: list,
    total_bandwidth: float,
    latency: float,
    jitter: float,
    weights: Dict[str, float],
) -> Dict[str, float]:
    """
    Compute performance metrics under a given weight configuration.

    Parameters
    ----------
    allocations : dict
        Mapping of user_id -> allocated bandwidth.
    users : list
        List of user dictionaries.
    total_bandwidth : float
        Total network bandwidth.
    latency : float
        Latency (ms).
    jitter : float
        Jitter (ms).
    weights : dict
        Weight mapping.

    Returns
    -------
    dict
        Metrics: total_allocated, utilization, fairness, average_utility.
    """
    total_allocated = float(sum(allocations.values()))

    if total_bandwidth > 0:
        utilization = (total_allocated / total_bandwidth) * 100
    else:
        utilization = 0.0

    fairness = jains_fairness_index(allocations)

    utilities = []
    for user in users:
        allocated = allocations.get(user["user_id"], 0.0)
        activity_weight = user.get("activity_weight", 1.0)
        utilities.append(
            weighted_utility(
                bandwidth=allocated,
                total_usage=total_allocated,
                total_bandwidth=total_bandwidth,
                activity_weight=activity_weight,
                latency=latency,
                jitter=jitter,
                activity=user.get("activity"),
                weights=weights,
            )
        )

    average_utility = float(np.mean(utilities)) if utilities else 0.0

    return {
        "total_allocated": round(total_allocated, 4),
        "utilization_percentage": round(utilization, 4),
        "jain_fairness_index": round(fairness, 6),
        "average_utility": round(average_utility, 6),
    }


# ============================================================
# RUN SENSITIVITY ANALYSIS
# ============================================================

def run_sensitivity_analysis(
    base_config: ExperimentConfig,
    parameter: str,
    values: List[float],
    algorithms: List[str] = None,
) -> Dict[str, Any]:
    """
    Run a sensitivity analysis for one utility weight parameter.

    Parameters
    ----------
    base_config : ExperimentConfig
        Base experiment configuration.
    parameter : str
        Weight parameter to vary (must be in SENSITIVITY_PARAMETERS).
    values : list
        List of weight values to test.
    algorithms : list or None
        Algorithms to evaluate. Defaults to base_config.algorithms.

    Returns
    -------
    dict
        Structured sensitivity results with per-value metrics.
    """
    if parameter not in SENSITIVITY_PARAMETERS:
        raise ValueError(
            f"Unknown parameter: {parameter}. "
            f"Must be one of {SENSITIVITY_PARAMETERS}"
        )

    create_data_directory(base_config.output_directory)

    algo_list = algorithms if algorithms else base_config.algorithms
    seeds = base_config.get_seeds()

    raw_rows = []

    for value in values:
        weights = dict(base_config.utility_weights)
        weights[parameter] = float(value)

        for number_of_users in base_config.user_counts:
            for algorithm in algo_list:
                for seed in seeds:
                    sim = generate_traffic_scenario(
                        scenario=base_config.scenario,
                        num_users=number_of_users,
                        total_bandwidth=base_config.total_bandwidth,
                        seed=seed,
                    )
                    users = sim["users"]

                    rng = __import__("random").Random(seed)
                    latency = round(rng.uniform(8.0, 22.0), 2)
                    jitter = round(rng.uniform(1.0, 6.0), 2)

                    evaluator = ALGORITHM_EVALUATORS.get(algorithm)
                    if evaluator is None:
                        raise ValueError(f"Unknown algorithm: {algorithm}")

                    result = evaluator(
                        users,
                        base_config.total_bandwidth,
                        latency,
                        jitter,
                        base_config,
                    )
                    allocations = result["allocations"]

                    start_time = time.perf_counter()
                    metrics = compute_weighted_metrics(
                        allocations,
                        users,
                        base_config.total_bandwidth,
                        latency,
                        jitter,
                        weights,
                    )
                    end_time = time.perf_counter()
                    computational_time = round(end_time - start_time, 6)

                    row = {
                        "experiment_id": (
                            f"sensitivity_{base_config.seed}_{number_of_users}_"
                            f"{algorithm}_{parameter}_{value}_{seed}"
                        ),
                        "timestamp": datetime.utcnow().isoformat(),
                        "seed": seed,
                        "parameter": parameter,
                        "parameter_value": float(value),
                        "number_of_users": number_of_users,
                        "strategy": algorithm,
                        "total_bandwidth": base_config.total_bandwidth,
                        "total_allocated": metrics["total_allocated"],
                        "utilization_percentage": metrics["utilization_percentage"],
                        "jain_fairness_index": metrics["jain_fairness_index"],
                        "average_utility": metrics["average_utility"],
                        "latency_ms": latency,
                        "jitter_ms": jitter,
                        "computational_time": computational_time,
                        "data_source": SIMULATION,
                    }
                    raw_rows.append(row)

    aggregated = _aggregate_sensitivity(raw_rows, parameter)

    save_sensitivity_results(raw_rows, base_config.output_directory)

    return {
        "status": "success",
        "config": base_config.to_dict(),
        "parameter": parameter,
        "values": [float(v) for v in values],
        "raw_rows": raw_rows,
        "aggregated": aggregated,
        "provenance": {
            "user_demand": SIMULATION,
            "allocation": CALCULATED_FROM_REAL_DATA,
            "metrics": CALCULATED_FROM_REAL_DATA,
            "note": (
                "Sensitivity analysis varies a single utility weight and "
                "recomputes utility to record metric responses."
            ),
        },
    }


# ============================================================
# AGGREGATE SENSITIVITY
# ============================================================

def _aggregate_sensitivity(rows: list, parameter: str) -> list:
    """
    Aggregate sensitivity raw rows by parameter value and strategy.

    Parameters
    ----------
    rows : list
        Raw sensitivity rows.
    parameter : str
        Varied parameter name.

    Returns
    -------
    list
        Aggregated rows with mean fairness, utility, utilization.
    """
    if not rows:
        return []

    df = pd.DataFrame(rows)
    grouped = df.groupby(["parameter_value", "strategy"])

    aggregated = []
    for (value, strategy), group in grouped:
        aggregated.append({
            "parameter": parameter,
            "parameter_value": float(value),
            "strategy": strategy,
            "n": len(group),
            "fairness_mean": round(float(group["jain_fairness_index"].mean()), 6),
            "utility_mean": round(float(group["average_utility"].mean()), 6),
            "utilization_mean": round(float(group["utilization_percentage"].mean()), 6),
        })

    return aggregated


# ============================================================
# SAVE SENSITIVITY RESULTS
# ============================================================

def save_sensitivity_results(raw_rows: list, output_directory: str):
    """
    Save sensitivity results to data/sensitivity_results.csv.

    Parameters
    ----------
    raw_rows : list
        Raw sensitivity rows.
    output_directory : str
        Directory to save files.
    """
    create_data_directory(output_directory)

    fieldnames = [
        "experiment_id",
        "timestamp",
        "seed",
        "parameter",
        "parameter_value",
        "number_of_users",
        "strategy",
        "total_bandwidth",
        "total_allocated",
        "utilization_percentage",
        "jain_fairness_index",
        "average_utility",
        "latency_ms",
        "jitter_ms",
        "computational_time",
        "data_source",
    ]

    filepath = os.path.join(output_directory, "sensitivity_results.csv")

    file_exists = os.path.exists(filepath)
    with open(filepath, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        if not file_exists:
            writer.writeheader()
        writer.writerows(raw_rows)
