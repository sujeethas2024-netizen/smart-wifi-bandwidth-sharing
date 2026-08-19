"""
Experiment Runner

Runs multiple synthetic Wi-Fi bandwidth experiments
with different numbers of users.

Strategies compared:

1. Equal Allocation
2. Proportional Allocation
3. Game Theory Allocation

Results are saved as CSV files in the data/ folder.

No external APIs are used.
"""

import csv
import os

from backend.services.evaluation_service import (
    evaluate_all_strategies
)

from backend.simulation.traffic_generator import (
    generate_traffic_scenario
)


# ============================================================
# EXPERIMENT CONFIGURATION
# ============================================================

USER_COUNTS = [
    5,
    10,
    20,
    30,
    50
]

TOTAL_BANDWIDTH = 100.0

OUTPUT_DIRECTORY = "data"

OUTPUT_FILE = (
    "data/experiment_results.csv"
)


# ============================================================
# CREATE DATA DIRECTORY
# ============================================================

def create_data_directory():
    """
    Create the data directory if it does not exist.
    """

    os.makedirs(
        OUTPUT_DIRECTORY,
        exist_ok=True
    )


# ============================================================
# RUN SINGLE EXPERIMENT
# ============================================================

def run_single_experiment(
    number_of_users,
    total_bandwidth=TOTAL_BANDWIDTH,
    seed=42
):
    """
    Run one experiment for a specific number of users.

    Parameters
    ----------
    number_of_users : int
        Number of simulated Wi-Fi users.

    total_bandwidth : float
        Total available Wi-Fi bandwidth.

    seed : int
        Random seed for reproducibility.

    Returns
    -------
    list
        Results for all allocation strategies.
    """

    # --------------------------------------------------------
    # Generate synthetic users
    # --------------------------------------------------------

    scenario = generate_traffic_scenario(

        scenario="medium",

        num_users=number_of_users,

        total_bandwidth=total_bandwidth,

        seed=seed

    )


    users = scenario["users"]


    # --------------------------------------------------------
    # Evaluate all strategies
    # --------------------------------------------------------

    results = evaluate_all_strategies(

        users,

        total_bandwidth

    )


    return results


# ============================================================
# CONVERT RESULTS INTO CSV ROWS
# ============================================================

def create_csv_rows(
    number_of_users,
    results
):
    """
    Convert experiment results into CSV-friendly rows.
    """

    rows = []

    for result in results:

        metrics = result["metrics"]

        row = {

            "number_of_users":
                number_of_users,

            "strategy":
                result["strategy"],

            "total_bandwidth":
                TOTAL_BANDWIDTH,

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
                ]

        }

        rows.append(row)

    return rows


# ============================================================
# SAVE RESULTS TO CSV
# ============================================================

def save_results_to_csv(
    rows,
    filename=OUTPUT_FILE
):
    """
    Save experiment results to a CSV file.
    """

    create_data_directory()

    fieldnames = [

        "number_of_users",

        "strategy",

        "total_bandwidth",

        "total_allocated",

        "utilization_percentage",

        "jain_fairness_index",

        "average_utility"

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
        f"{TOTAL_BANDWIDTH:.2f} Mbps"
    )

    print(
        f"User Scenarios  : "
        f"{USER_COUNTS}"
    )

    print()


    all_rows = []


    # --------------------------------------------------------
    # Run every user scenario
    # --------------------------------------------------------

    for number_of_users in USER_COUNTS:

        print(
            f"Running experiment "
            f"for {number_of_users} users..."
        )


        results = run_single_experiment(

            number_of_users=
                number_of_users,

            total_bandwidth=
                TOTAL_BANDWIDTH,

            seed=42

        )


        # Display results

        display_experiment_result(

            number_of_users,

            results

        )


        # Convert to CSV rows

        rows = create_csv_rows(

            number_of_users,

            results

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
        f"  {OUTPUT_FILE}"
    )

    print()

    print(
        f"Total experiment rows: "
        f"{len(all_rows)}"
    )

    print()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    run_experiment()