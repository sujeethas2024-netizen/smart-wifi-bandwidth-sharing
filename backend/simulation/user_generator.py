import random


# ============================================================
# ACTIVITY CONFIGURATION
# ============================================================
#
# Each activity has:
#
# min_bandwidth = minimum expected bandwidth demand
# max_bandwidth = maximum expected bandwidth demand
# weight        = importance used by the Game Theory model
#
# These values are simulated values, NOT API data.
# ============================================================

ACTIVITY_CONFIG = {

    "browsing": {
        "min_bandwidth": 2,
        "max_bandwidth": 10,
        "weight": 1.0
    },

    "online_class": {
        "min_bandwidth": 5,
        "max_bandwidth": 15,
        "weight": 1.5
    },

    "gaming": {
        "min_bandwidth": 5,
        "max_bandwidth": 20,
        "weight": 1.3
    },

    "streaming": {
        "min_bandwidth": 8,
        "max_bandwidth": 25,
        "weight": 1.4
    },

    "downloading": {
        "min_bandwidth": 10,
        "max_bandwidth": 30,
        "weight": 1.1
    }
}


# ============================================================
# AVAILABLE ACTIVITIES
# ============================================================

ACTIVITIES = list(
    ACTIVITY_CONFIG.keys()
)


# ============================================================
# GENERATE ONE USER
# ============================================================

def generate_user(user_id):
    """
    Generate a single simulated Wi-Fi user.

    Each user receives:

        user_id
        activity
        requested_bandwidth
        activity_weight
    """

    # Randomly select an activity
    activity = random.choice(
        ACTIVITIES
    )

    # Get configuration for activity
    config = ACTIVITY_CONFIG[
        activity
    ]

    # Generate bandwidth demand
    requested_bandwidth = random.uniform(
        config["min_bandwidth"],
        config["max_bandwidth"]
    )

    # Round to two decimal places
    requested_bandwidth = round(
        requested_bandwidth,
        2
    )

    return {

        "user_id": user_id,

        "activity": activity,

        "requested_bandwidth":
            requested_bandwidth,

        "activity_weight":
            config["weight"]
    }


# ============================================================
# GENERATE MULTIPLE USERS
# ============================================================

def generate_users(
    number_of_users,
    seed=None
):
    """
    Generate multiple simulated Wi-Fi users.

    Parameters
    ----------
    number_of_users : int
        Number of users to generate.

    seed : int or None
        Optional random seed.

        Using the same seed produces the same
        users, which is useful for experiments.

    Returns
    -------
    list
        List of simulated users.
    """

    if number_of_users <= 0:
        raise ValueError(
            "Number of users must be greater than zero."
        )

    # Set seed if provided
    if seed is not None:
        random.seed(seed)

    users = []

    for user_id in range(
        1,
        number_of_users + 1
    ):

        user = generate_user(
            user_id
        )

        users.append(user)

    return users


# ============================================================
# DISPLAY USERS
# ============================================================

def display_users(users):
    """
    Display generated users in a readable format.
    """

    print()
    print("=" * 75)
    print("              SIMULATED WI-FI USERS")
    print("=" * 75)

    print(
        f"{'User':<10}"
        f"{'Activity':<20}"
        f"{'Requested Bandwidth':<25}"
    )

    print("-" * 75)

    for user in users:

        print(
            f"{user['user_id']:<10}"
            f"{user['activity']:<20}"
            f"{user['requested_bandwidth']:>8.2f} Mbps"
        )

    print("=" * 75)


# ============================================================
# TESTING THE MODULE DIRECTLY
# ============================================================

if __name__ == "__main__":

    users = generate_users(
        number_of_users=10,
        seed=42
    )

    display_users(users)