"""
Evaluation Service

Compares three bandwidth allocation strategies:

1. Equal Allocation
2. Proportional Allocation
3. Game Theory Allocation

Metrics:
- Total allocated bandwidth
- Bandwidth utilization
- Jain's fairness index
- Average utility

No external APIs are used.
All data is generated locally.
"""

from backend.game_theory.utility import calculate_utility

from backend.game_theory.fairness import (
    jains_fairness_index
)

from backend.services.allocation_service import (
    allocate_bandwidth
)

from backend.simulation.traffic_generator import (
    generate_traffic_scenario
)


# ============================================================
# 1. EQUAL ALLOCATION
# ============================================================

def equal_allocation(users, total_bandwidth):
    """
    Divide available bandwidth equally among users.

    A user cannot receive more bandwidth than requested.
    """

    number_of_users = len(users)

    if number_of_users == 0:
        return {}

    equal_share = (
        total_bandwidth / number_of_users
    )

    allocations = {}

    for user in users:

        requested = user[
            "requested_bandwidth"
        ]

        allocation = min(
            equal_share,
            requested
        )

        allocations[
            user["user_id"]
        ] = allocation

    return allocations


# ============================================================
# 2. PROPORTIONAL ALLOCATION
# ============================================================

def proportional_allocation(
    users,
    total_bandwidth
):
    """
    Allocate bandwidth according to each user's
    requested bandwidth.

    If total demand is greater than capacity:

        allocation =
        user demand / total demand
        × total available bandwidth
    """

    total_requested = sum(
        user["requested_bandwidth"]
        for user in users
    )

    allocations = {}

    if total_requested == 0:

        return {
            user["user_id"]: 0
            for user in users
        }

    for user in users:

        requested = user[
            "requested_bandwidth"
        ]

        if total_requested <= total_bandwidth:

            allocation = requested

        else:

            allocation = (
                requested
                / total_requested
            ) * total_bandwidth

        allocations[
            user["user_id"]
        ] = allocation

    return allocations


# ============================================================
# 3. CALCULATE COMMON METRICS
# ============================================================

def calculate_metrics(
    users,
    allocations,
    total_bandwidth
):
    """
    Calculate performance metrics for an allocation strategy.

    Metrics:

    - Total allocated bandwidth
    - Utilization
    - Jain fairness index
    - Average utility
    """

    # --------------------------------------------------------
    # TOTAL ALLOCATED BANDWIDTH
    # --------------------------------------------------------

    total_allocated = sum(
        allocations.values()
    )


    # --------------------------------------------------------
    # BANDWIDTH UTILIZATION
    # --------------------------------------------------------

    if total_bandwidth > 0:

        utilization = (
            total_allocated
            / total_bandwidth
        ) * 100

    else:

        utilization = 0


    # --------------------------------------------------------
    # JAIN'S FAIRNESS INDEX
    # --------------------------------------------------------

    fairness = jains_fairness_index(
        allocations
    )


    # --------------------------------------------------------
    # USER UTILITIES
    # --------------------------------------------------------

    utilities = []

    for user in users:

        user_id = user["user_id"]

        allocated = allocations.get(
            user_id,
            0
        )

        # Total bandwidth currently being used
        total_usage = total_allocated

        # Activity weight.
        # If the simulator does not provide it,
        # use 1.0 as the default.
        activity_weight = user.get(
            "activity_weight",
            1.0
        )

        # IMPORTANT:
        # This matches the actual calculate_utility()
        # function in your utility.py.

        utility = calculate_utility(

            bandwidth=allocated,

            total_usage=total_usage,

            total_bandwidth=total_bandwidth,

            activity_weight=activity_weight,

            congestion_penalty=0.5

        )

        utilities.append(
            utility
        )


    # --------------------------------------------------------
    # AVERAGE UTILITY
    # --------------------------------------------------------

    if utilities:

        average_utility = (
            sum(utilities)
            / len(utilities)
        )

    else:

        average_utility = 0


    # --------------------------------------------------------
    # RETURN METRICS
    # --------------------------------------------------------

    return {

        "total_allocated":
            round(
                total_allocated,
                2
            ),

        "utilization":
            round(
                utilization,
                2
            ),

        "fairness":
            round(
                fairness,
                4
            ),

        "average_utility":
            round(
                average_utility,
                4
            )

    }


# ============================================================
# 4. EVALUATE EQUAL ALLOCATION
# ============================================================

def evaluate_equal(
    users,
    total_bandwidth
):
    """
    Evaluate the Equal Allocation strategy.
    """

    allocations = equal_allocation(

        users,

        total_bandwidth

    )

    metrics = calculate_metrics(

        users,

        allocations,

        total_bandwidth

    )

    return {

        "strategy":
            "Equal Allocation",

        "allocations":
            allocations,

        "metrics":
            metrics

    }


# ============================================================
# 5. EVALUATE PROPORTIONAL ALLOCATION
# ============================================================

def evaluate_proportional(
    users,
    total_bandwidth
):
    """
    Evaluate the Proportional Allocation strategy.
    """

    allocations = proportional_allocation(

        users,

        total_bandwidth

    )

    metrics = calculate_metrics(

        users,

        allocations,

        total_bandwidth

    )

    return {

        "strategy":
            "Proportional Allocation",

        "allocations":
            allocations,

        "metrics":
            metrics

    }


# ============================================================
# 6. EVALUATE GAME THEORY
# ============================================================

def evaluate_game_theory(
    users,
    total_bandwidth
):
    """
    Evaluate the Game Theory allocation strategy.

    This uses our existing allocation_service.py.
    """

    result = allocate_bandwidth(

        simulated_users=users,

        total_bandwidth=total_bandwidth,

        congestion_penalty=0.5,

        step=0.5,

        max_iterations=100

    )


    # --------------------------------------------------------
    # Extract allocations
    # --------------------------------------------------------

    allocations = {

        user["user_id"]:
            user["allocated_bandwidth"]

        for user in result["users"]

    }


    # --------------------------------------------------------
    # Extract metrics
    # --------------------------------------------------------

    if result["users"]:

        average_utility = (

            sum(
                user["utility"]
                for user in result["users"]
            )

            / len(result["users"])

        )

    else:

        average_utility = 0


    metrics = {

        "total_allocated":
            result[
                "total_allocated_bandwidth"
            ],

        "utilization":
            result[
                "utilization_percentage"
            ],

        "fairness":
            result[
                "jain_fairness_index"
            ],

        "average_utility":
            round(
                average_utility,
                4
            )

    }


    return {

        "strategy":
            "Game Theory",

        "allocations":
            allocations,

        "metrics":
            metrics

    }


# ============================================================
# 7. EVALUATE ALL THREE STRATEGIES
# ============================================================

def evaluate_all_strategies(
    users,
    total_bandwidth
):
    """
    Run all three allocation strategies.
    """

    equal_result = evaluate_equal(

        users,

        total_bandwidth

    )


    proportional_result = evaluate_proportional(

        users,

        total_bandwidth

    )


    game_result = evaluate_game_theory(

        users,

        total_bandwidth

    )


    return [

        equal_result,

        proportional_result,

        game_result

    ]


# ============================================================
# 8. DISPLAY RESULTS
# ============================================================

def display_evaluation_results(
    results
):
    """
    Display comparison results in the terminal.
    """

    print()

    print("=" * 90)

    print(
        "          BANDWIDTH ALLOCATION COMPARISON"
    )

    print("=" * 90)

    print()

    print(
        f"{'Strategy':<25}"
        f"{'Allocated':>15}"
        f"{'Utilization':>15}"
        f"{'Fairness':>12}"
        f"{'Avg Utility':>15}"
    )

    print("-" * 90)


    for result in results:

        metrics = result["metrics"]

        print(

            f"{result['strategy']:<25}"

            f"{metrics['total_allocated']:>12.2f} Mbps"

            f"{metrics['utilization']:>12.2f}%"

            f"{metrics['fairness']:>12.4f}"

            f"{metrics['average_utility']:>14.4f}"

        )


    print("-" * 90)

    print()


# ============================================================
# 9. MAIN PROGRAM
# ============================================================

if __name__ == "__main__":

    print()

    print("=" * 90)

    print(
        "       SMART WI-FI BANDWIDTH EVALUATION"
    )

    print("=" * 90)

    print()


    # --------------------------------------------------------
    # GENERATE SYNTHETIC TRAFFIC
    # --------------------------------------------------------

    scenario = generate_traffic_scenario(

        scenario="medium",

        seed=42

    )


    users = scenario["users"]

    total_bandwidth = (
        scenario["total_bandwidth"]
    )


    # --------------------------------------------------------
    # DISPLAY NETWORK INFORMATION
    # --------------------------------------------------------

    print(
        f"Total Bandwidth : "
        f"{total_bandwidth:.2f} Mbps"
    )

    print(
        f"Number of Users : "
        f"{len(users)}"
    )

    print()


    # --------------------------------------------------------
    # RUN EVALUATION
    # --------------------------------------------------------

    results = evaluate_all_strategies(

        users,

        total_bandwidth

    )


    # --------------------------------------------------------
    # DISPLAY RESULTS
    # --------------------------------------------------------

    display_evaluation_results(
        results
    )