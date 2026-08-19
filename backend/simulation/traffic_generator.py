"""
Traffic Generator

Generates synthetic Wi-Fi traffic scenarios for the
Smart Wi-Fi Bandwidth Sharing project.

No external APIs or real network data are used.

Supported predefined scenarios:

    low       -> 5 users
    medium    -> 10 users
    high      -> 20 users
    extreme   -> 50 users

The generator also supports custom numbers of users,
which is useful for experiments.
"""

import random

from .user_generator import (
    generate_users
)


# ============================================================
# TRAFFIC SCENARIOS
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
    seed=None,
    num_users=None,
    total_bandwidth=None
):
    """
    Generate a complete synthetic Wi-Fi network scenario.

    Parameters
    ----------
    scenario : str
        Predefined scenario:

            low
            medium
            high
            extreme

        If num_users is supplied, the scenario name is
        still used as a label but the custom user count
        is used.

    seed : int or None
        Random seed for reproducible experiments.

    num_users : int or None
        Optional custom number of users.

        Example:

            num_users=15

        This is useful for experiments.

    total_bandwidth : float or None
        Optional custom network bandwidth.

        Example:

            total_bandwidth=100

    Returns
    -------
    dict
        Complete synthetic network scenario.
    """

    # --------------------------------------------------------
    # CHECK SCENARIO
    # --------------------------------------------------------

    if scenario not in SCENARIOS:

        raise ValueError(

            f"Unknown scenario: {scenario}. "

            f"Available scenarios: "
            f"{list(SCENARIOS.keys())}"

        )


    # --------------------------------------------------------
    # SET RANDOM SEED
    # --------------------------------------------------------

    if seed is not None:

        random.seed(seed)


    # --------------------------------------------------------
    # GET DEFAULT CONFIGURATION
    # --------------------------------------------------------

    config = SCENARIOS[
        scenario
    ]


    # --------------------------------------------------------
    # DETERMINE NUMBER OF USERS
    # --------------------------------------------------------

    if num_users is None:

        number_of_users = config[
            "users"
        ]

    else:

        if num_users <= 0:

            raise ValueError(
                "Number of users must be greater than zero."
            )

        number_of_users = int(
            num_users
        )


    # --------------------------------------------------------
    # DETERMINE TOTAL BANDWIDTH
    # --------------------------------------------------------

    if total_bandwidth is None:

        network_bandwidth = float(
            config["bandwidth"]
        )

    else:

        if total_bandwidth <= 0:

            raise ValueError(
                "Total bandwidth must be greater than zero."
            )

        network_bandwidth = float(
            total_bandwidth
        )


    # --------------------------------------------------------
    # GENERATE USERS
    # --------------------------------------------------------

    users = generate_users(

        number_of_users=
            number_of_users,

        seed=seed

    )


    # --------------------------------------------------------
    # CALCULATE TOTAL REQUESTED BANDWIDTH
    # --------------------------------------------------------

    total_requested = sum(

        user[
            "requested_bandwidth"
        ]

        for user in users

    )


    # --------------------------------------------------------
    # CALCULATE DEMAND RATIO
    # --------------------------------------------------------

    demand_ratio = (

        total_requested
        / network_bandwidth

    )


    # --------------------------------------------------------
    # DETERMINE CONGESTION LEVEL
    # --------------------------------------------------------

    congestion_level = (

        determine_congestion_level(

            demand_ratio

        )

    )


    # --------------------------------------------------------
    # DESCRIPTION
    # --------------------------------------------------------

    if num_users is not None:

        description = (
            f"Custom scenario with "
            f"{number_of_users} users"
        )

    else:

        description = config[
            "description"
        ]


    # --------------------------------------------------------
    # RETURN COMPLETE SCENARIO
    # --------------------------------------------------------

    return {

        "scenario":
            scenario,

        "description":
            description,

        "total_bandwidth":
            network_bandwidth,

        "number_of_users":
            number_of_users,

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

    Demand ratio:

        < 0.50  -> LOW
        < 1.00  -> MODERATE
        < 1.50  -> HIGH
        >= 1.50 -> EXTREME
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

    print(
        "             WI-FI TRAFFIC SIMULATION"
    )

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
        f"{scenario['total_bandwidth']:.2f} Mbps"

    )


    print(

        f"Number of Users       : "
        f"{scenario['number_of_users']}"

    )


    print(

        f"Total Requested       : "
        f"{scenario['total_requested_bandwidth']:.2f} Mbps"

    )


    print(

        f"Demand Ratio          : "
        f"{scenario['demand_ratio']:.2f}"

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
# TEST ALL PREDEFINED SCENARIOS
# ============================================================

def test_all_scenarios():
    """
    Test low, medium, high and extreme scenarios.
    """

    print()

    print("=" * 75)

    print(
        "             TESTING TRAFFIC SCENARIOS"
    )

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
# TEST CUSTOM USER COUNTS
# ============================================================

def test_custom_scenarios():
    """
    Test custom user counts.

    These are useful for the experimental dataset.
    """

    print()

    print("=" * 75)

    print(
        "             TESTING CUSTOM SCENARIOS"
    )

    print("=" * 75)


    custom_user_counts = [

        5,
        10,
        20,
        30,
        50

    ]


    for number_of_users in custom_user_counts:

        scenario = (

            generate_traffic_scenario(

                scenario="medium",

                num_users=
                    number_of_users,

                total_bandwidth=100,

                seed=42

            )

        )


        print()

        print(

            f"Users: "
            f"{scenario['number_of_users']:<3}"

            f" | Requested: "
            f"{scenario['total_requested_bandwidth']:<8.2f} Mbps"

            f" | Demand Ratio: "
            f"{scenario['demand_ratio']:<5.2f}"

            f" | Congestion: "
            f"{scenario['congestion_level']}"

        )


# ============================================================
# MAIN TEST
# ============================================================

if __name__ == "__main__":

    # --------------------------------------------------------
    # Test medium scenario
    # --------------------------------------------------------

    scenario = (

        generate_traffic_scenario(

            scenario="medium",

            seed=42

        )

    )


    display_traffic_scenario(

        scenario

    )


    # --------------------------------------------------------
    # Test predefined scenarios
    # --------------------------------------------------------

    test_all_scenarios()


    # --------------------------------------------------------
    # Test custom scenarios
    # --------------------------------------------------------

    test_custom_scenarios()