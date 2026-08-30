"""
Utility Function for WiFi Bandwidth Allocation

Computes the payoff/utility for a single user in a congestion game.

Utility Model
-------------

U_i = w_B * log(1 + B_i)
      - w_C * B_i * (total_usage / total_bandwidth)
      - w_L * (latency_penalty_i)
      - w_J * (jitter_penalty_i)

Where:
    B_i              = allocated bandwidth to user i
    total_usage      = sum of all allocated bandwidths
    total_bandwidth  = total available bandwidth
    w_B              = bandwidth benefit weight (activity-based)
    w_C              = congestion penalty weight
    w_L              = latency sensitivity weight (QoS-based)
    w_J              = jitter sensitivity weight (QoS-based)

Activity weights (w_B) are defined in congestion_game.py.
QoS sensitivity weights are defined in this module.

References:
    - Nash Equilibrium for non-cooperative congestion games
    - Jain's Fairness Index for allocation evaluation
"""
import math


# ============================================================
# QoS SENSITIVITY WEIGHTS
# ============================================================
# Higher weight = more sensitive to that metric.
# Derived from standard QoS classifications for the activities
# present in the dataset.

QoS_WEIGHTS = {
    # activity: (latency_sensitivity, jitter_sensitivity)
    "browsing":      (0.3, 0.2),
    "online_class":  (0.9, 0.7),
    "gaming":        (1.0, 1.0),
    "streaming":     (0.5, 0.4),
    "downloading":   (0.1, 0.1),
    # Fallback for unknown activities
    "default":       (0.5, 0.5),
}


def get_qos_weights(activity: str):
    """Return (latency_weight, jitter_weight) for an activity."""
    return QoS_WEIGHTS.get(activity, QoS_WEIGHTS["default"])


# ============================================================
# CALCULATE UTILITY
# ============================================================

def calculate_utility(
    bandwidth,
    total_usage,
    total_bandwidth,
    activity_weight=1.0,
    congestion_penalty=0.5,
    latency=0.0,
    jitter=0.0,
    activity=None,
):
    """
    Calculate the utility/payoff of a Wi-Fi user.

    Parameters
    ----------
    bandwidth : float
        Bandwidth allocated to the user (Mbps).
    total_usage : float
        Total bandwidth currently being used by all users.
    total_bandwidth : float
        Total available network bandwidth (Mbps).
    activity_weight : float
        Importance of the user's current activity (from ACTIVITY_WEIGHTS).
    congestion_penalty : float
        Penalty coefficient for network congestion.
    latency : float
        Measured/simulated latency (ms). Used for QoS penalty.
    jitter : float
        Measured/simulated jitter (ms). Used for QoS penalty.
    activity : str or None
        Activity name. Used to look up QoS sensitivity weights.

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
    # QoS PENALTIES (latency + jitter)
    # ------------------------------------------------
    #
    # Only applied when latency/jitter values are provided.
    # Weights are activity-specific so that gaming/voice calls
    # are penalized more for poor latency than downloads.
    # ------------------------------------------------

    qos_penalty = 0.0

    if latency > 0 or jitter > 0:
        lat_w, jit_w = get_qos_weights(activity) if activity else (0.5, 0.5)

        # Normalize latency to [0, 1] assuming 0-100 ms range
        lat_norm = min(latency / 100.0, 1.0)
        # Normalize jitter to [0, 1] assuming 0-20 ms range
        jit_norm = min(jitter / 20.0, 1.0)

        qos_penalty = (
            lat_w * lat_norm * 0.5
            + jit_w * jit_norm * 0.3
        ) * bandwidth

    # ------------------------------------------------
    # FINAL UTILITY
    # ------------------------------------------------

    utility = (
        benefit
        - congestion_cost
        - qos_penalty
    )

    return utility
