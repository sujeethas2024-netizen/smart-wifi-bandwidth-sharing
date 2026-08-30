"""
Ablation Study Framework

Investigates the contribution of each term in the utility model by
removing individual components and re-running multi-seed experiments.

Utility model components ablated:
    - throughput_benefit  (ln(1 + B))
    - congestion_penalty
    - latency_penalty
    - jitter_penalty
    - qos_violation_penalty

The full model uses ``backend.game_theory.utility.calculate_utility``.
For each ablation variant the same function is called with the relevant
penalty term disabled, so the comparison isolates each component's effect.
"""

import csv
import json
import os
import time
from datetime import datetime
from typing import Dict, Any, List, Set

import numpy as np
import pandas as pd

from backend.experiments.config_schema import ExperimentConfig
from backend.experiments.runner import ALGORITHM_EVALUATORS, create_data_directory
from backend.simulation.traffic_generator import generate_traffic_scenario
from backend.game_theory.utility import calculate_utility
from backend.game_theory.fairness import jains_fairness_index
from backend.data_provenance import SIMULATION, CALCULATED_FROM_REAL_DATA


# ============================================================
# COMPONENTS TO ABLATE
# ============================================================

ABLATION_COMPONENTS = [
    "throughput_benefit",
    "congestion_penalty",
    "latency_penalty",
    "jitter_penalty",
    "qos_violation_penalty",
]


# ============================================================
# UTILITY WITH COMPONENTS REMOVED
# ============================================================

def ablated_utility(
    bandwidth: float,
    total_usage: float,
    total_bandwidth: float,
    activity_weight: float,
    congestion_penalty: float,
    latency: float,
    jitter: float,
    activity: str,
    disabled: Set[str],
) -> float:
    """
    Compute utility with one or more model components disabled.

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
    congestion_penalty : float
        Congestion penalty coefficient.
    latency : float
        Latency (ms).
    jitter : float
        Jitter (ms).
    activity : str
        Activity name (for QoS sensitivity weights).
    disabled : set
        Set of component names to disable.

    Returns
    -------
    float
        Utility with the specified components removed.
    """
    aw = 0.0 if "throughput_benefit" in disabled else activity_weight
    cp = 0.0 if "congestion_penalty" in disabled else congestion_penalty

    # qos_violation_penalty removes both latency and jitter penalties.
    if "qos_violation_penalty" in disabled:
        lat = 0.0
        jit = 0.0
    else:
        lat = 0.0 if "latency_penalty" in disabled else latency
        jit = 0.0 if "jitter_penalty" in disabled else jitter

    return calculate_utility(
        bandwidth=bandwidth,
        total_usage=total_usage,
        total_bandwidth=total_bandwidth,
        activity_weight=aw,
        congestion_penalty=cp,
        latency=lat,
        jitter=jit,
        activity=activity,
    )


# ============================================================
# COMPUTE METRICS FOR A VARIANT
# ============================================================

def compute_ablated_metrics(
    allocations: dict,
    users: list,
    total_bandwidth: float,
    latency: float,
    jitter: float,
    disabled: Set[str],
) -> Dict[str, float]:
    """
    Compute performance metrics for one ablation variant.

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
    disabled : set
        Set of component names to disable.

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
            ablated_utility(
                bandwidth=allocated,
                total_usage=total_allocated,
                total_bandwidth=total_bandwidth,
                activity_weight=activity_weight,
                congestion_penalty=0.5,
                latency=latency,
                jitter=jitter,
                activity=user.get("activity"),
                disabled=disabled,
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
# RUN ABLATION STUDY
# ============================================================

def run_ablation(config: ExperimentConfig) -> Dict[str, Any]:
    """
    Run an ablation study across all utility model components.

    For each component, the full utility model is re-evaluated with that
    component removed over multiple seeds, and the aggregate impact of
    removing the component is computed relative to the full model.

    Parameters
    ----------
    config : ExperimentConfig
        Experiment configuration.

    Returns
    -------
    dict
        Structured ablation results including per-variant raw rows,
        aggregated statistics, and component impact deltas.
    """
    create_data_directory(config.output_directory)

    seeds = config.get_seeds()

    variant_rows: Dict[str, list] = {variant: [] for variant in ["full"] + ABLATION_COMPONENTS}

    for number_of_users in config.user_counts:
        for algorithm in config.algorithms:
            for seed in seeds:
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

                result = evaluator(
                    users,
                    config.total_bandwidth,
                    latency,
                    jitter,
                    config,
                )
                allocations = result["allocations"]

                for variant, disabled in [("full", set())] + [
                    (c, {c}) for c in ABLATION_COMPONENTS
                ]:
                    start_time = time.perf_counter()
                    metrics = compute_ablated_metrics(
                        allocations,
                        users,
                        config.total_bandwidth,
                        latency,
                        jitter,
                        disabled,
                    )
                    end_time = time.perf_counter()
                    computational_time = round(end_time - start_time, 6)

                    row = {
                        "experiment_id": (
                            f"ablation_{config.seed}_{number_of_users}_"
                            f"{algorithm}_{variant}_{seed}"
                        ),
                        "timestamp": datetime.utcnow().isoformat(),
                        "seed": seed,
                        "variant": variant,
                        "number_of_users": number_of_users,
                        "strategy": algorithm,
                        "total_bandwidth": config.total_bandwidth,
                        "total_allocated": metrics["total_allocated"],
                        "utilization_percentage": metrics["utilization_percentage"],
                        "jain_fairness_index": metrics["jain_fairness_index"],
                        "average_utility": metrics["average_utility"],
                        "latency_ms": latency,
                        "jitter_ms": jitter,
                        "computational_time": computational_time,
                        "data_source": SIMULATION,
                    }
                    variant_rows[variant].append(row)

    aggregated = {
        variant: _aggregate_ablation(variant_rows[variant])
        for variant in variant_rows
    }

    impact = _compute_impact(aggregated)

    save_ablation_results(variant_rows, config.output_directory)
    save_ablation_config(
        {
            "components": ABLATION_COMPONENTS,
            "impact": impact,
            "config": config.to_dict(),
        },
        config.output_directory,
    )

    return {
        "status": "success",
        "config": config.to_dict(),
        "components": ABLATION_COMPONENTS,
        "variant_raw_rows": variant_rows,
        "aggregated": aggregated,
        "impact": impact,
        "provenance": {
            "user_demand": SIMULATION,
            "allocation": CALCULATED_FROM_REAL_DATA,
            "metrics": CALCULATED_FROM_REAL_DATA,
            "note": (
                "Ablation study removes individual utility model components "
                "and re-evaluates the same allocations to isolate each term's effect."
            ),
        },
    }


# ============================================================
# AGGREGATE ABLATION VARIANT
# ============================================================

def _aggregate_ablation(rows: list) -> list:
    """
    Aggregate a single ablation variant's raw rows.

    Parameters
    ----------
    rows : list
        Raw result rows for one variant.

    Returns
    -------
    list
        Aggregated rows (mean per user_count/strategy group).
    """
    if not rows:
        return []

    df = pd.DataFrame(rows)
    metrics = [
        "total_allocated",
        "utilization_percentage",
        "jain_fairness_index",
        "average_utility",
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
            row[f"{metric}_mean"] = (
                round(float(values.mean()), 6) if len(values) else None
            )
        aggregated.append(row)

    return aggregated


# ============================================================
# COMPUTE COMPONENT IMPACT
# ============================================================

def _compute_impact(aggregated: Dict[str, list]) -> Dict[str, Any]:
    """
    Compute the impact of removing each component relative to the full model.

    Parameters
    ----------
    aggregated : dict
        Aggregated rows keyed by variant name.

    Returns
    -------
    dict
        Mean metric deltas (full - ablated) per component.
    """
    full_df = pd.DataFrame(aggregated.get("full", []))
    if full_df.empty:
        return {}

    metric_cols = [
        "total_allocated_mean",
        "utilization_percentage_mean",
        "jain_fairness_index_mean",
        "average_utility_mean",
    ]

    impact: Dict[str, Any] = {}
    for component in ABLATION_COMPONENTS:
        comp_df = pd.DataFrame(aggregated.get(component, []))
        if comp_df.empty:
            continue

        merged = full_df.merge(
            comp_df,
            on=["number_of_users", "strategy"],
            suffixes=("_full", "_ablated"),
        )

        component_impact = {}
        for col in metric_cols:
            full_vals = merged[f"{col}_full"].astype(float)
            ablated_vals = merged[f"{col}_ablated"].astype(float)
            delta = float((full_vals - ablated_vals).mean())
            component_impact[col] = round(delta, 6)
        impact[component] = component_impact

    return impact


# ============================================================
# SAVE ABLATION RESULTS
# ============================================================

def save_ablation_results(variant_rows: Dict[str, list], output_directory: str):
    """
    Save ablation results to data/ablation_results.csv.

    Parameters
    ----------
    variant_rows : dict
        Raw rows keyed by variant name.
    output_directory : str
        Directory to save files.
    """
    create_data_directory(output_directory)

    fieldnames = [
        "experiment_id",
        "timestamp",
        "seed",
        "variant",
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

    filepath = os.path.join(output_directory, "ablation_results.csv")

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for variant in ["full"] + ABLATION_COMPONENTS:
            writer.writerows(variant_rows.get(variant, []))


def save_ablation_config(payload: dict, output_directory: str):
    """
    Save ablation study summary to data/ablation_results.json.

    Parameters
    ----------
    payload : dict
        Ablation summary (components, impact, config).
    output_directory : str
        Directory to save files.
    """
    create_data_directory(output_directory)

    filepath = os.path.join(output_directory, "ablation_results.json")

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
