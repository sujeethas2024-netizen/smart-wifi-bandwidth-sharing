import math


def calculate_utility(
    bandwidth,
    total_usage,
    total_bandwidth,
    activity_weight=1.0,
    congestion_penalty=0.5
):
    """
    Calculate the utility/payoff of a Wi-Fi user.

    Utility consists of:

        Utility = Benefit - Congestion Cost

    Parameters
    ----------
    bandwidth : float
        Bandwidth allocated to the user.

    total_usage : float
        Total bandwidth currently being used by all users.

    total_bandwidth : float
        Total available network bandwidth.

    activity_weight : float
        Importance of the user's current activity.

    congestion_penalty : float
        Penalty caused by network congestion.

    Returns
    -------
    float
        Utility/payoff of the user.
    """

    # Invalid bandwidth
    if bandwidth < 0:
        return float("-inf")

    # Network must have positive bandwidth
    if total_bandwidth <= 0:
        return float("-inf")

    # No bandwidth means no benefit
    if bandwidth == 0:
        return 0.0

    # ------------------------------------------------
    # BENEFIT
    # ------------------------------------------------
    #
    # log(1 + bandwidth) gives diminishing returns.
    #
    # Example:
    # First few Mbps are very valuable.
    # Additional Mbps provide smaller extra benefit.
    #
    benefit = (
        activity_weight
        * math.log(1 + bandwidth)
    )

    # ------------------------------------------------
    # CONGESTION
    # ------------------------------------------------

    congestion_ratio = (
        total_usage / total_bandwidth
    )

    # ------------------------------------------------
    # CONGESTION COST
    # ------------------------------------------------

    congestion_cost = (
        congestion_penalty
        * bandwidth
        * congestion_ratio
    )

    # ------------------------------------------------
    # FINAL UTILITY
    # ------------------------------------------------

    utility = (
        benefit
        - congestion_cost
    )

    return utility