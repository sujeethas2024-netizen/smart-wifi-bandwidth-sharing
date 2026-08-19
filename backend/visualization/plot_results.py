"""
Visualization Module

Creates graphs from the synthetic experimental results.

Input:
    data/experiment_results.csv

Output:
    data/fairness_vs_users.png
    data/utilization_vs_users.png
    data/utility_vs_users.png

No external APIs are used.
"""

import csv
import os

import matplotlib.pyplot as plt


# ============================================================
# FILE PATHS
# ============================================================

INPUT_FILE = "data/experiment_results.csv"

OUTPUT_DIRECTORY = "data"


# ============================================================
# LOAD RESULTS
# ============================================================

def load_results(filename=INPUT_FILE):
    """
    Load experiment results from CSV.
    """

    if not os.path.exists(filename):

        raise FileNotFoundError(
            f"Could not find: {filename}"
        )

    with open(
        filename,
        "r",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        results = list(reader)


    # Convert numeric values

    for row in results:

        row["number_of_users"] = int(
            row["number_of_users"]
        )

        row["utilization_percentage"] = float(
            row["utilization_percentage"]
        )

        row["jain_fairness_index"] = float(
            row["jain_fairness_index"]
        )

        row["average_utility"] = float(
            row["average_utility"]
        )


    return results


# ============================================================
# GROUP RESULTS BY STRATEGY
# ============================================================

def group_by_strategy(results):
    """
    Organize results according to allocation strategy.
    """

    strategies = {}

    for row in results:

        strategy = row["strategy"]

        if strategy not in strategies:

            strategies[strategy] = []

        strategies[strategy].append(row)


    # Sort each strategy according to user count

    for strategy in strategies:

        strategies[strategy].sort(
            key=lambda row: row["number_of_users"]
        )


    return strategies


# ============================================================
# CREATE OUTPUT DIRECTORY
# ============================================================

def create_output_directory():
    """
    Create the output directory if it doesn't exist.
    """

    os.makedirs(
        OUTPUT_DIRECTORY,
        exist_ok=True
    )


# ============================================================
# FAIRNESS GRAPH
# ============================================================

def plot_fairness(results):
    """
    Create Jain Fairness Index vs Number of Users graph.
    """

    strategies = group_by_strategy(
        results
    )

    plt.figure(figsize=(10, 6))

    for strategy, rows in strategies.items():

        users = [
            row["number_of_users"]
            for row in rows
        ]

        fairness = [
            row["jain_fairness_index"]
            for row in rows
        ]

        plt.plot(
            users,
            fairness,
            marker="o",
            label=strategy
        )


    plt.title(
        "Jain Fairness Index vs Number of Users"
    )

    plt.xlabel(
        "Number of Users"
    )

    plt.ylabel(
        "Jain Fairness Index"
    )

    plt.ylim(
        0,
        1.05
    )

    plt.grid(
        True,
        alpha=0.3
    )

    plt.legend()

    plt.tight_layout()


    output_file = os.path.join(
        OUTPUT_DIRECTORY,
        "fairness_vs_users.png"
    )

    plt.savefig(
        output_file,
        dpi=300
    )

    plt.close()


    print(
        f"Created: {output_file}"
    )


# ============================================================
# UTILIZATION GRAPH
# ============================================================

def plot_utilization(results):
    """
    Create bandwidth utilization vs number of users graph.
    """

    strategies = group_by_strategy(
        results
    )

    plt.figure(figsize=(10, 6))

    for strategy, rows in strategies.items():

        users = [
            row["number_of_users"]
            for row in rows
        ]

        utilization = [
            row["utilization_percentage"]
            for row in rows
        ]

        plt.plot(
            users,
            utilization,
            marker="o",
            label=strategy
        )


    plt.title(
        "Bandwidth Utilization vs Number of Users"
    )

    plt.xlabel(
        "Number of Users"
    )

    plt.ylabel(
        "Bandwidth Utilization (%)"
    )

    plt.ylim(
        0,
        105
    )

    plt.grid(
        True,
        alpha=0.3
    )

    plt.legend()

    plt.tight_layout()


    output_file = os.path.join(
        OUTPUT_DIRECTORY,
        "utilization_vs_users.png"
    )

    plt.savefig(
        output_file,
        dpi=300
    )

    plt.close()


    print(
        f"Created: {output_file}"
    )


# ============================================================
# UTILITY GRAPH
# ============================================================

def plot_utility(results):
    """
    Create average utility vs number of users graph.
    """

    strategies = group_by_strategy(
        results
    )

    plt.figure(figsize=(10, 6))

    for strategy, rows in strategies.items():

        users = [
            row["number_of_users"]
            for row in rows
        ]

        utilities = [
            row["average_utility"]
            for row in rows
        ]

        plt.plot(
            users,
            utilities,
            marker="o",
            label=strategy
        )


    plt.title(
        "Average User Utility vs Number of Users"
    )

    plt.xlabel(
        "Number of Users"
    )

    plt.ylabel(
        "Average Utility"
    )

    plt.grid(
        True,
        alpha=0.3
    )

    plt.legend()

    plt.tight_layout()


    output_file = os.path.join(
        OUTPUT_DIRECTORY,
        "utility_vs_users.png"
    )

    plt.savefig(
        output_file,
        dpi=300
    )

    plt.close()


    print(
        f"Created: {output_file}"
    )


# ============================================================
# GENERATE ALL GRAPHS
# ============================================================

def generate_all_graphs():
    """
    Generate all project graphs.
    """

    print()

    print("=" * 80)

    print(
        "       SMART WI-FI BANDWIDTH VISUALIZATION"
    )

    print("=" * 80)

    print()


    # Make sure output folder exists

    create_output_directory()


    # Load experimental data

    results = load_results()


    print(
        f"Loaded {len(results)} experiment rows."
    )

    print()


    # Generate graphs

    plot_fairness(
        results
    )

    plot_utilization(
        results
    )

    plot_utility(
        results
    )


    print()

    print("=" * 80)

    print(
        "       ALL GRAPHS GENERATED SUCCESSFULLY"
    )

    print("=" * 80)

    print()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    generate_all_graphs()