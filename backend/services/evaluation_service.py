"""
Evaluation Service

Compares bandwidth allocation strategies:

1. Equal Allocation
2. Proportional Allocation
3. Priority-Based Allocation (QoS-aware)
4. Game Theory Allocation (Nash Equilibrium)

Metrics:
- Total allocated bandwidth
- Bandwidth utilization
- Jain's fairness index
- Average utility

No external APIs are used.
All data is generated locally or loaded from the dataset.
"""

import math

import numpy as np

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
# ACTIVITY PRIORITY MAPPING
# ============================================================
# Higher priority = more important for QoS.
# Used by the Priority-Based allocation strategy.

ACTIVITY_PRIORITY = {

    "browsing": 1.0,

    "downloading": 1.2,

    "streaming": 1.5,

    "online_class": 1.8,

    "gaming": 2.0

}


def get_activity_priority(activity: str) -> float:
    """Return QoS priority weight for an activity."""
    return ACTIVITY_PRIORITY.get(activity, 1.0)


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
# 3. PRIORITY-BASED ALLOCATION (QoS-aware)
# ============================================================

def priority_allocation(
    users,
    total_bandwidth
):
    """
    Allocate bandwidth based on activity QoS priority.

    Higher-priority activities (gaming, online_class) receive
    proportionally more bandwidth than lower-priority ones
    (browsing, downloading).

    If total demand exceeds capacity, priority weights are used
    to scale allocations while respecting individual demands.
    """
    if not users:
        return {}

    # Calculate total priority weight
    total_priority = sum(
        get_activity_priority(user.get("activity", ""))
        for user in users
    )

    if total_priority == 0:
        return equal_allocation(users, total_bandwidth)

    allocations = {}
    remaining = total_bandwidth

    # Sort users by priority (highest first) for fair-share allocation
    sorted_users = sorted(
        users,
        key=lambda u: get_activity_priority(u.get("activity", "")),
        reverse=True,
    )

    for user in sorted_users:
        requested = user["requested_bandwidth"]
        priority = get_activity_priority(user.get("activity", ""))

        # Proportional share based on priority
        share = (priority / total_priority) * total_bandwidth

        # Cannot exceed requested amount
        allocation = min(share, requested)

        allocations[user["user_id"]] = allocation
        remaining -= allocation

    # If bandwidth remains after satisfying all requests,
    # redistribute equally among all users
    if remaining > 0 and allocations:
        equal_extra = remaining / len(allocations)
        for uid in allocations:
            allocations[uid] += equal_extra

    return allocations


# ============================================================
# 4. CALCULATE COMMON METRICS
# ============================================================

def calculate_metrics(
    users,
    allocations,
    total_bandwidth,
    latency=0.0,
    jitter=0.0
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

        utility = calculate_utility(

            bandwidth=allocated,

            total_usage=total_usage,

            total_bandwidth=total_bandwidth,

            activity_weight=activity_weight,

            congestion_penalty=0.5,

            latency=latency,

            jitter=jitter,

            activity=user.get("activity"),

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
# 5. EVALUATE EQUAL ALLOCATION
# ============================================================

def evaluate_equal(
    users,
    total_bandwidth,
    latency=0.0,
    jitter=0.0
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

        total_bandwidth,

        latency=latency,

        jitter=jitter

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
# 6. EVALUATE PROPORTIONAL ALLOCATION
# ============================================================

def evaluate_proportional(
    users,
    total_bandwidth,
    latency=0.0,
    jitter=0.0
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

        total_bandwidth,

        latency=latency,

        jitter=jitter

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
# 7. EVALUATE PRIORITY-BASED ALLOCATION
# ============================================================

def evaluate_priority(
    users,
    total_bandwidth,
    latency=0.0,
    jitter=0.0
):
    """
    Evaluate the Priority-Based Allocation strategy.
    """

    allocations = priority_allocation(

        users,

        total_bandwidth

    )

    metrics = calculate_metrics(

        users,

        allocations,

        total_bandwidth,

        latency=latency,

        jitter=jitter

    )

    return {

        "strategy":
            "Priority Allocation",

        "allocations":
            allocations,

        "metrics":
            metrics

    }


# ============================================================
# 8. EVALUATE GAME THEORY
# ============================================================

def evaluate_game_theory(
    users,
    total_bandwidth,
    latency=0.0,
    jitter=0.0
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
            metrics,

        "convergence_iterations":
            result.get(
                "convergence_iterations"
            ),

        "converged":
            result.get(
                "converged"
            ),

        "is_nash_equilibrium":
            result.get(
                "is_nash_equilibrium"
            )

    }


# ============================================================
# 9. EVALUATE ALL FOUR STRATEGIES
# ============================================================

def max_min_fairness_allocation(
    users,
    total_bandwidth
):
    """
    Max-min fair bandwidth allocation using water-filling.

    Max-min fairness maximizes the minimum allocation while
    respecting individual user demands.
    """
    if not users:
        return {}

    demands = {
        user["user_id"]: user["requested_bandwidth"]
        for user in users
    }

    allocations = {uid: 0.0 for uid in demands}

    remaining = total_bandwidth

    while remaining > 0:
        active_uids = [
            uid for uid in demands
            if allocations[uid] < demands[uid]
        ]

        if not active_uids:
            break

        equal_share = remaining / len(active_uids)

        updated = False

        for uid in active_uids:
            needed = demands[uid] - allocations[uid]
            give = min(equal_share, needed)
            allocations[uid] += give
            remaining -= give
            updated = True

        if not updated:
            break

    return allocations


def evaluate_max_min_fairness(
    users,
    total_bandwidth,
    latency=0.0,
    jitter=0.0
):
    """
    Evaluate the Max-Min Fairness allocation strategy.
    """
    allocations = max_min_fairness_allocation(
        users,
        total_bandwidth
    )

    metrics = calculate_metrics(
        users,
        allocations,
        total_bandwidth,
        latency=latency,
        jitter=jitter
    )

    return {
        "strategy": "Max-Min Fairness",
        "allocations": allocations,
        "metrics": metrics
    }


def alpha_fair_allocation(
    users,
    total_bandwidth,
    alpha=1.0
):
    """
    Alpha-fair bandwidth allocation.

    Parameters
    ----------
    alpha : float
        Fairness parameter:
          alpha = 0   -> utilitarian
          alpha = 1   -> proportional fairness (Nash)
          alpha = 2   -> harmonic mean fairness
          alpha -> inf -> max-min fairness
    """
    if not users:
        return {}

    demands = {
        user["user_id"]: user["requested_bandwidth"]
        for user in users
    }

    if alpha == float("inf"):
        return max_min_fairness_allocation(users, total_bandwidth)

    if alpha == 0:
        total_demand = sum(demands.values())
        if total_demand <= total_bandwidth:
            return dict(demands)
        allocations = {}
        for uid, demand in demands.items():
            allocations[uid] = (demand / total_demand) * total_bandwidth
        return allocations

    if alpha == 1:
        total_demand = sum(demands.values())
        if total_demand <= total_bandwidth:
            return dict(demands)
        allocations = {}
        for uid, demand in demands.items():
            if demand > 0:
                allocations[uid] = (demand / total_demand) * total_bandwidth
            else:
                allocations[uid] = 0.0
        return allocations

    if alpha == 2:
        total_inv_demand = sum(1.0 / d for d in demands.values() if d > 0)
        if total_inv_demand == 0:
            return dict(demands)
        allocations = {}
        for uid, demand in demands.items():
            if demand > 0:
                allocations[uid] = (1.0 / demand) / total_inv_demand * total_bandwidth
            else:
                allocations[uid] = 0.0
        return allocations

    demands_arr = np.array(list(demands.values()), dtype=float)
    n = len(demands_arr)

    def objective(x):
        if alpha == 1:
            return -np.sum(np.log(np.maximum(x, 1e-12)))
        return -np.sum(np.power(np.maximum(x, 1e-12), 1 - alpha) / (1 - alpha))

    def grad(x):
        if alpha == 1:
            return -1.0 / np.maximum(x, 1e-12)
        return -np.power(np.maximum(x, 1e-12), -alpha)

    x = np.ones(n) * (total_bandwidth / n)
    x = np.minimum(x, demands_arr)

    lr = 0.01
    for _ in range(5000):
        g = grad(x)
        x_new = x - lr * g
        x_new = np.clip(x_new, 0, demands_arr)
        total = np.sum(x_new)
        if total > total_bandwidth:
            x_new = x_new / total * total_bandwidth
        x = x_new

    allocations = {}
    for i, uid in enumerate(demands.keys()):
        allocations[uid] = float(x[i])

    return allocations


def evaluate_alpha_fair(
    users,
    total_bandwidth,
    latency=0.0,
    jitter=0.0,
    alpha=1.0
):
    """
    Evaluate the Alpha-Fair allocation strategy.
    """
    allocations = alpha_fair_allocation(
        users,
        total_bandwidth,
        alpha=alpha
    )

    metrics = calculate_metrics(
        users,
        allocations,
        total_bandwidth,
        latency=latency,
        jitter=jitter
    )

    return {
        "strategy": f"Alpha-Fair (alpha={alpha})",
        "allocations": allocations,
        "metrics": metrics
    }


def evaluate_all_strategies(
    users,
    total_bandwidth,
    latency=0.0,
    jitter=0.0,
    alpha=1.0
):
    """
    Run all allocation strategies.
    """

    equal_result = evaluate_equal(

        users,

        total_bandwidth,

        latency=latency,

        jitter=jitter

    )


    proportional_result = evaluate_proportional(

        users,

        total_bandwidth,

        latency=latency,

        jitter=jitter

    )


    priority_result = evaluate_priority(

        users,

        total_bandwidth,

        latency=latency,

        jitter=jitter

    )


    max_min_result = evaluate_max_min_fairness(

        users,

        total_bandwidth,

        latency=latency,

        jitter=jitter

    )


    alpha_result = evaluate_alpha_fair(

        users,

        total_bandwidth,

        latency=latency,

        jitter=jitter,

        alpha=alpha

    )


    game_result = evaluate_game_theory(

        users,

        total_bandwidth,

        latency=latency,

        jitter=jitter

    )


    return [

        equal_result,

        proportional_result,

        priority_result,

        max_min_result,

        alpha_result,

        game_result

    ]


# ============================================================
# 10. DISPLAY RESULTS
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
# 11. MAIN PROGRAM
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
