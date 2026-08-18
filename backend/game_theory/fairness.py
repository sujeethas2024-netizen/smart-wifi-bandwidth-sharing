# ==================================================
# JAIN'S FAIRNESS INDEX
# ==================================================

def jains_fairness_index(
    allocations
):
    """
    Calculate Jain's Fairness Index.

    Formula:

                 (sum Xi)^2
    J = -----------------------------
             n * sum(Xi^2)

    Where:

    Xi = bandwidth allocated to user i

    n = number of users

    Result:

    0 → Very unfair

    1 → Perfect fairness
    """

    # ----------------------------------------------
    # Extract bandwidth values
    # ----------------------------------------------

    values = list(
        allocations.values()
    )


    # No users
    if not values:

        return 0.0


    # ----------------------------------------------
    # If everybody gets zero bandwidth
    # ----------------------------------------------

    if sum(values) == 0:

        return 0.0


    # ----------------------------------------------
    # Numerator
    # ----------------------------------------------

    numerator = (

        sum(values) ** 2

    )


    # ----------------------------------------------
    # Denominator
    # ----------------------------------------------

    denominator = (

        len(values)

        * sum(

            value ** 2

            for value in values

        )

    )


    # ----------------------------------------------
    # Prevent division by zero
    # ----------------------------------------------

    if denominator == 0:

        return 0.0


    # ----------------------------------------------
    # Jain's Fairness Index
    # ----------------------------------------------

    fairness = (

        numerator
        / denominator

    )


    return round(
        fairness,
        4
    )


# ==================================================
# FAIRNESS INTERPRETATION
# ==================================================

def fairness_status(
    fairness_index
):
    """
    Convert fairness score into a readable status.
    """

    if fairness_index >= 0.90:

        return "Excellent"

    elif fairness_index >= 0.75:

        return "Good"

    elif fairness_index >= 0.50:

        return "Moderate"

    else:

        return "Poor"