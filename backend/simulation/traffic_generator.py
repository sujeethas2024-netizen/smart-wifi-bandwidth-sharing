import random

from .user_generator import (
    generate_users
)


# ============================================================
# TRAFFIC SCENARIOS
# ============================================================
#
# These scenarios allow us to test the Game Theory algorithm
# under different network conditions.
# ============================================================

SCENARIOS = {

    "low": {

        "description":
            "Low network demand",

        "users":
            5,

        "bandwidth":
            100

    },

    "medium": {

        "description":
            "Moderate network demand",

        "users":
            10,

        "bandwidth":
            100

    },

    "high": {

        "description":
            "High network demand",

        "users":
            20,

        "bandwidth":
            100

    },

    "extreme": {

        "description":
            "Extreme network congestion",

        "users":
            50,

        "bandwidth":
            100
    }
}


# ============================================================
# GENERATE TRAFFIC SCENARIO
# ============================================================

def generate_traffic_scenario(
    scenario="medium",
    seed=None
):
    """
    Generate a complete simulated network scenario.

    Parameters
    ----------
    scenario : str
        low / medium / high / extreme

    seed : int or None
        Random seed for reproducible experiments.

    Returns
    -------
    dict
        Complete network scenario.
    """

    # Check scenario
    if scenario not in SCENARIOS:

        raise ValueError(

            f"Unknown scenario: {scenario}. "

            f"Available scenarios: "
            f"{list(SCENARIOS.keys())}"

        )

    # Set seed
    if seed is not None:

        random.seed(seed)

    # Get scenario configuration
    config = SCENARIOS[
        scenario
    ]

    # Generate users
    users = generate_users(

        number_of_users=
            config["users"],

        seed=seed

    )

    # Calculate total requested bandwidth
    total_requested = sum(

        user[
            "requested_bandwidth"
        ]

        for user in users

    )

    # Calculate demand ratio
    demand_ratio = (

        total_requested
        / config["bandwidth"]

    )

    # Determine congestion level
    congestion_level = (
        determine_congestion_level(
            demand_ratio
        )
    )

    # Return complete scenario
    return {

        "scenario":
            scenario,

        "description":
            config["description"],

        "total_bandwidth":
            config["bandwidth"],

        "number_of_users":
            config["users"],

        "total_requested_bandwidth":
            round(
                total_requested,
                2
            ),

        "demand_ratio":
            round(
                demand_ratio,
                2
            ),

        "congestion_level":
            congestion_level,

        "users":
            users
    }


# ============================================================
# DETERMINE CONGESTION LEVEL
# ============================================================

def determine_congestion_level(
    demand_ratio
):
    """
    Determine network congestion based on total demand.

    demand_ratio:

        < 0.50 → LOW
        < 1.00 → MODERATE
        < 1.50 → HIGH
        >=1.50 → EXTREME
    """

    if demand_ratio < 0.50:

        return "LOW"

    elif demand_ratio < 1.00:

        return "MODERATE"

    elif demand_ratio < 1.50:

        return "HIGH"

    else:

        return "EXTREME"


# ============================================================
# DISPLAY TRAFFIC SCENARIO
# ============================================================

def display_traffic_scenario(
    scenario
):
    """
    Display a generated traffic scenario.
    """

    print()
    print("=" * 75)
    print("             WI-FI TRAFFIC SIMULATION")
    print("=" * 75)

    print(
        f"Scenario              : "
        f"{scenario['scenario'].upper()}"
    )

    print(
        f"Description           : "
        f"{scenario['description']}"
    )

    print(
        f"Total Bandwidth       : "
        f"{scenario['total_bandwidth']} Mbps"
    )

    print(
        f"Number of Users       : "
        f"{scenario['number_of_users']}"
    )

    print(
        f"Total Requested       : "
        f"{scenario['total_requested_bandwidth']} Mbps"
    )

    print(
        f"Demand Ratio          : "
        f"{scenario['demand_ratio']}"
    )

    print(
        f"Congestion Level      : "
        f"{scenario['congestion_level']}"
    )

    print("-" * 75)

    print(
        f"{'User':<10}"
        f"{'Activity':<20}"
        f"{'Requested':<20}"
    )

    print("-" * 75)

    for user in scenario["users"]:

        print(

            f"{user['user_id']:<10}"

            f"{user['activity']:<20}"

            f"{user['requested_bandwidth']:>8.2f} Mbps"

        )

    print("=" * 75)


# ============================================================
# TEST ALL SCENARIOS
# ============================================================

def test_all_scenarios():

    print()
    print("=" * 75)
    print("             TESTING TRAFFIC SCENARIOS")
    print("=" * 75)

    for scenario_name in SCENARIOS:

        scenario = (
            generate_traffic_scenario(
                scenario=scenario_name,
                seed=42
            )
        )

        print()

        print(
            f"{scenario_name.upper():<10}"
            f"| Users: "
            f"{scenario['number_of_users']:<3}"
            f"| Requested: "
            f"{scenario['total_requested_bandwidth']:<8}"
            f"| Congestion: "
            f"{scenario['congestion_level']}"
        )


# ============================================================
# TESTING DIRECTLY
# ============================================================

if __name__ == "__main__":

    # Generate one medium scenario
    scenario = (
        generate_traffic_scenario(
            scenario="medium",
            seed=42
        )
    )

    display_traffic_scenario(
        scenario
    )

    # Test all scenarios
    test_all_scenarios()