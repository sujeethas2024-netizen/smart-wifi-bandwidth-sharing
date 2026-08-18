from game_theory.congestion_game import User

from game_theory.nash_equilibrium import (
    find_nash_equilibrium
)

from game_theory.fairness import (
    jains_fairness_index
)


def allocate_bandwidth(
    total_bandwidth,
    user_data
):

    # ---------------------------------
    # Create Game Theory players
    # ---------------------------------

    users = []


    for data in user_data:

        user = User(

            user_id=data.get(
                "user_id"
            ),

            activity=data.get(
                "activity",
                "browsing"
            ),

            requested_bandwidth=float(
                data.get(
                    "requested_bandwidth",
                    5
                )
            )
        )

        users.append(user)


    # ---------------------------------
    # Find Nash Equilibrium
    # ---------------------------------

    result = find_nash_equilibrium(

        users,

        total_bandwidth
    )


    allocations = result[
        "allocations"
    ]


    # ---------------------------------
    # Calculate fairness
    # ---------------------------------

    fairness = jains_fairness_index(
        allocations
    )


    # ---------------------------------
    # Prepare response
    # ---------------------------------

    user_results = []


    for user in users:

        user_results.append({

            "user_id":
                user.user_id,

            "activity":
                user.activity,

            "requested_bandwidth":
                user.requested_bandwidth,

            "allocated_bandwidth":
                user.allocated_bandwidth,

            "utility":
                round(
                    user.utility,
                    4
                )

        })


    return {

        "total_bandwidth":
            total_bandwidth,

        "iterations":
            result[
                "iterations"
            ],

        "users":
            user_results,

        "allocations":
            allocations,

        "fairness_index":
            fairness

    }