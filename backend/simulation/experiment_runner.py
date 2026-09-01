"""
Experiment Runner

Runs reproducible Wi-Fi bandwidth experiments comparing:

1. Equal Allocation
2. Proportional Allocation
3. Priority-Based Allocation
4. Game Theory Allocation (Nash Equilibrium)

Experiments vary the number of users and use controlled
random seeds for reproducibility.

Results are saved as CSV files in the data/ folder.

Data sources:
- Synthetic traffic scenarios (user_generator.py)
- Real dataset fallback (processed_users.csv) via allocation_service
"""

import csv
import json
import os
import random
from datetime import datetime

from backend.services.evaluation_service import (
    evaluate_all_strategies
)

from backend.simulation.traffic_generator import (
    generate_traffic_scenario
)


# ============================================================
# EXPERIMENT CONFIGURATION
# ============================================================

EXPERIMENT_CONFIG = {
    "user_counts": [5, 10, 20, 30, 50, 100, 200, 373],
    "total_bandwidth": 100.0,
    "seed": 42,
    "scenario": "medium",
    "repetitions": 1,
    "output_directory": "data",
    "output_file": "data/experiment_results.csv",
    "description": "Scalability experiment comparing allocation strategies",
}


def get_experiment_config():
    """Return a copy of the experiment configuration."""
    return dict(EXPERIMENT_CONFIG)


def set_experiment_config(**kwargs):
    """Update experiment configuration (validated keys only)."""
    allowed = {
        "user_counts", "total_bandwidth", "seed", "scenario",
        "repetitions", "output_directory", "output_file", "description",
    }
    for key, value in kwargs.items():
        if key in allowed:
            EXPERIMENT_CONFIG[key] = value


# ============================================================
# CREATE DATA DIRECTORY
# ============================================================

def create_data_directory():
    """
    Create the data directory if it does not exist.
    """
    os.makedirs(
        EXPERIMENT_CONFIG["output_directory"],
        exist_ok=True
    )


# ============================================================
# RUN SINGLE EXPERIMENT
# ============================================================

def run_single_experiment(
    number_of_users,
    total_bandwidth=None,
    seed=None,
    scenario=None,
):
    """
    Run one experiment for a specific number of users.

    Parameters
    ----------
    number_of_users : int
        Number of simulated Wi-Fi users.

    total_bandwidth : float or None
        Total available Wi-Fi bandwidth.

    seed : int or None
        Random seed for reproducibility.

    scenario : str or None
        Traffic scenario label.

    Returns
    -------
    list
        Results for all allocation strategies.
    """
    if total_bandwidth is None:
        total_bandwidth = EXPERIMENT_CONFIG["total_bandwidth"]
    if seed is None:
        seed = EXPERIMENT_CONFIG["seed"]
    if scenario is None:
        scenario = EXPERIMENT_CONFIG["scenario"]

    # --------------------------------------------------------
    # Generate synthetic users
    # --------------------------------------------------------

    sim = generate_traffic_scenario(

        scenario=scenario,

        num_users=number_of_users,

        total_bandwidth=total_bandwidth,

        seed=seed

    )

    users = sim["users"]

    # --------------------------------------------------------
    # Use simulated latency/jitter for QoS-aware evaluation
    # (These are deterministic based on seed for reproducibility)
    # --------------------------------------------------------

    rng = random.Random(seed)
    latency = round(rng.uniform(8.0, 22.0), 2)
    jitter = round(rng.uniform(1.0, 6.0), 2)

    # --------------------------------------------------------
    # Evaluate all strategies
    # --------------------------------------------------------

    results = evaluate_all_strategies(

        users,

        total_bandwidth,

        latency=latency,

        jitter=jitter

    )

    return results


# ============================================================
# CONVERT RESULTS INTO CSV ROWS
# ============================================================

def create_csv_rows(
    number_of_users,
    results,
    seed=None,
    latency=None,
    jitter=None,
):
    """
    Convert experiment results into CSV-friendly rows.
    """
    if seed is None:
        seed = EXPERIMENT_CONFIG["seed"]
    if latency is None:
        latency = 0.0
    if jitter is None:
        jitter = 0.0

    rows = []

    for result in results:

        metrics = result["metrics"]

        row = {

            "experiment_id": f"exp_{seed}_{number_of_users}",

            "timestamp": datetime.utcnow().isoformat(),

            "seed": seed,

            "number_of_users":
                number_of_users,

            "strategy":
                result["strategy"],

            "total_bandwidth":
                EXPERIMENT_CONFIG["total_bandwidth"],

            "total_allocated":
                metrics[
                    "total_allocated"
                ],

            "utilization_percentage":
                metrics[
                    "utilization"
                ],

            "jain_fairness_index":
                metrics[
                    "fairness"
                ],

            "average_utility":
                metrics[
                    "average_utility"
                ],

            "latency_ms": latency,

            "jitter_ms": jitter,

            "repetition": 1,

            "convergence_iterations":
                result.get(
                    "convergence_iterations"
                ) if result.get(
                    "strategy"
                ) == "Game Theory" else None,

            "converged":
                result.get(
                    "converged"
                ) if result.get(
                    "strategy"
                ) == "Game Theory" else None,

            "is_nash_equilibrium":
                result.get(
                    "is_nash_equilibrium"
                ) if result.get(
                    "strategy"
                ) == "Game Theory" else None,

        }

        rows.append(row)

    return rows


# ============================================================
# SAVE RESULTS TO CSV
# ============================================================

def save_results_to_csv(
    rows,
    filename=None
):
    """
    Save experiment results to a CSV file.
    """
    if filename is None:
        filename = EXPERIMENT_CONFIG["output_file"]

    create_data_directory()

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
        "convergence_iterations",
        "converged",
        "is_nash_equilibrium",

    ]


    with open(
        filename,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(

            file,

            fieldnames=fieldnames

        )

        writer.writeheader()

        writer.writerows(rows)


# ============================================================
# DISPLAY EXPERIMENT PROGRESS
# ============================================================

def display_experiment_result(
    number_of_users,
    results
):
    """
    Display results for one experiment.
    """

    print()

    print(
        f"Users: {number_of_users}"
    )

    print("-" * 80)

    print(

        f"{'Strategy':<25}"

        f"{'Allocated':>15}"

        f"{'Utilization':>15}"

        f"{'Fairness':>12}"

        f"{'Avg Utility':>15}"

    )

    print("-" * 80)


    for result in results:

        metrics = result["metrics"]

        print(

            f"{result['strategy']:<25}"

            f"{metrics['total_allocated']:>12.2f} Mbps"

            f"{metrics['utilization']:>12.2f}%"

            f"{metrics['fairness']:>12.4f}"

            f"{metrics['average_utility']:>14.4f}"

        )


    print("-" * 80)


# ============================================================
# RUN COMPLETE EXPERIMENT
# ============================================================

def run_experiment():

    """
    Run experiments for all configured user counts.

    Results are saved into data/experiment_results.csv.
    """

    print()

    print("=" * 90)

    print(
        "       SMART WI-FI BANDWIDTH EXPERIMENT"
    )

    print("=" * 90)

    print()

    print(
        f"Total Bandwidth : "
        f"{EXPERIMENT_CONFIG['total_bandwidth']:.2f} Mbps"
    )

    print(
        f"User Scenarios  : "
        f"{EXPERIMENT_CONFIG['user_counts']}"
    )

    print(
        f"Random Seed     : "
        f"{EXPERIMENT_CONFIG['seed']}"
    )

    print(
        f"Scenario        : "
        f"{EXPERIMENT_CONFIG['scenario']}"
    )

    print(
        f"Description     : "
        f"{EXPERIMENT_CONFIG['description']}"
    )

    print()


    all_rows = []


    # --------------------------------------------------------
    # Run every user scenario
    # --------------------------------------------------------

    for number_of_users in EXPERIMENT_CONFIG["user_counts"]:

        print(
            f"Running experiment "
            f"for {number_of_users} users..."
        )


        results = run_single_experiment(

            number_of_users=
                number_of_users,

            total_bandwidth=
                EXPERIMENT_CONFIG["total_bandwidth"],

            seed=EXPERIMENT_CONFIG["seed"],

            scenario=EXPERIMENT_CONFIG["scenario"]

        )


        # Display results

        display_experiment_result(

            number_of_users,

            results

        )


        # Convert to CSV rows

        rows = create_csv_rows(

            number_of_users,

            results,

            seed=EXPERIMENT_CONFIG["seed"]

        )


        all_rows.extend(rows)


    # --------------------------------------------------------
    # Save everything
    # --------------------------------------------------------

    save_results_to_csv(

        all_rows

    )


    print()

    print("=" * 90)

    print(
        "EXPERIMENT COMPLETED SUCCESSFULLY"
    )

    print("=" * 90)

    print()

    print(
        f"Results saved to:"
    )

    print(
        f"  {EXPERIMENT_CONFIG['output_file']}"
    )

    print()

    print(
        f"Total experiment rows: "
        f"{len(all_rows)}"
    )

    print()


# ============================================================
# RUN EXPERIMENT AS JSON (for API)
# ============================================================

def run_experiment_json(user_counts=None):
    """
    Run experiment and return results as a JSON-serializable dict.
    """
    config = get_experiment_config()
    if user_counts:
        config["user_counts"] = list(user_counts)

    all_rows = []

    for number_of_users in config["user_counts"]:
        results = run_single_experiment(
            number_of_users=number_of_users,
            total_bandwidth=config["total_bandwidth"],
            seed=config["seed"],
            scenario=config["scenario"],
        )
        rows = create_csv_rows(
            number_of_users,
            results,
            seed=config["seed"],
        )
        all_rows.extend(rows)

    return {
        "config": config,
        "results": all_rows,
        "total_rows": len(all_rows),
    }


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    run_experiment()
