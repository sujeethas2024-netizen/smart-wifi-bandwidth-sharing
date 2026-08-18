from .utility import calculate_utility


# ==================================================
# BEST RESPONSE
# ==================================================

def find_best_response(
    user,
    users,
    current_allocations,
    total_bandwidth,
    congestion_penalty=0.5,
    step=0.5
):
    """
    Find the best bandwidth strategy for one player.

    The player considers different possible bandwidth
    values and chooses the one that gives maximum utility.

    This is called a BEST RESPONSE.
    """

    # ----------------------------------------------
    # Bandwidth used by other players
    # ----------------------------------------------

    other_usage = sum(

        current_allocations[
            other.user_id
        ]

        for other in users

        if other.user_id != user.user_id

    )


    # ----------------------------------------------
    # Maximum bandwidth available to this player
    # ----------------------------------------------

    remaining_bandwidth = (

        total_bandwidth
        - other_usage

    )


    if remaining_bandwidth < 0:

        remaining_bandwidth = 0


    # User cannot receive more than what they requested
    maximum_bandwidth = min(

        user.requested_bandwidth,

        remaining_bandwidth

    )


    # ----------------------------------------------
    # Search for best strategy
    # ----------------------------------------------

    best_bandwidth = 0.0

    best_utility = float("-inf")


    candidate = 0.0


    while candidate <= (
        maximum_bandwidth + 0.000001
    ):

        total_usage = (
            other_usage
            + candidate
        )


        utility = calculate_utility(

            bandwidth=candidate,

            total_usage=total_usage,

            total_bandwidth=total_bandwidth,

            activity_weight=user.weight,

            congestion_penalty=
                congestion_penalty

        )


        # ------------------------------------------
        # Better strategy found
        # ------------------------------------------

        if utility > best_utility:

            best_utility = utility

            best_bandwidth = candidate


        candidate += step


    return (
        round(best_bandwidth, 2),
        best_utility
    )


# ==================================================
# NASH EQUILIBRIUM
# ==================================================

def find_nash_equilibrium(
    users,
    total_bandwidth,
    congestion_penalty=0.5,
    step=0.5,
    max_iterations=100
):
    """
    Find an approximate Nash Equilibrium.

    Each player repeatedly chooses their best response
    to the strategies of the other players.

    The process stops when the allocation becomes stable.
    """

    # ----------------------------------------------
    # Initial strategy
    # ----------------------------------------------

    allocations = {

        user.user_id: 0.0

        for user in users

    }


    # ----------------------------------------------
    # Iterative best-response process
    # ----------------------------------------------

    iterations_used = 0


    for iteration in range(
        max_iterations
    ):

        iterations_used = (
            iteration + 1
        )


        old_allocations = (
            allocations.copy()
        )


        # ------------------------------------------
        # Every player chooses a best response
        # ------------------------------------------

        for user in users:

            best_bandwidth, _ = (
                find_best_response(

                    user=user,

                    users=users,

                    current_allocations=
                        allocations,

                    total_bandwidth=
                        total_bandwidth,

                    congestion_penalty=
                        congestion_penalty,

                    step=step
                )
            )


            allocations[
                user.user_id
            ] = best_bandwidth


        # ------------------------------------------
        # Check convergence
        # ------------------------------------------

        total_change = sum(

            abs(

                allocations[
                    user.user_id
                ]

                -

                old_allocations[
                    user.user_id
                ]

            )

            for user in users

        )


        # If strategies barely changed,
        # we consider the game stable.

        if total_change < step:

            break


    # ----------------------------------------------
    # Store final strategies in User objects
    # ----------------------------------------------

    for user in users:

        user.allocated_bandwidth = (
            allocations[
                user.user_id
            ]
        )


    # ----------------------------------------------
    # Calculate final utilities
    # ----------------------------------------------

    total_usage = sum(

        user.allocated_bandwidth

        for user in users

    )


    for user in users:

        user.utility = calculate_utility(

            bandwidth=
                user.allocated_bandwidth,

            total_usage=
                total_usage,

            total_bandwidth=
                total_bandwidth,

            activity_weight=
                user.weight,

            congestion_penalty=
                congestion_penalty

        )


    # ----------------------------------------------
    # Return result
    # ----------------------------------------------

    return {

        "allocations":
            allocations,

        "iterations":
            iterations_used

    }