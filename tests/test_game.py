import sys
import os


# --------------------------------------------------
# Add backend folder to Python path
# --------------------------------------------------

PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        ".."
    )
)

BACKEND_PATH = os.path.join(
    PROJECT_ROOT,
    "backend"
)

sys.path.insert(
    0,
    BACKEND_PATH
)


# --------------------------------------------------
# Import Game Theory modules
# --------------------------------------------------

from game_theory.congestion_game import User

from game_theory.nash_equilibrium import (
    find_nash_equilibrium
)

from game_theory.fairness import (
    jains_fairness_index
)


# --------------------------------------------------
# Network Configuration
# --------------------------------------------------

TOTAL_BANDWIDTH = 40


# --------------------------------------------------
# Create Wi-Fi Users
# --------------------------------------------------

users = [

    User(
        user_id=1,
        activity="browsing",
        requested_bandwidth=10
    ),

    User(
        user_id=2,
        activity="online_class",
        requested_bandwidth=15
    ),

    User(
        user_id=3,
        activity="gaming",
        requested_bandwidth=20
    ),

    User(
        user_id=4,
        activity="downloading",
        requested_bandwidth=30
    )

]


# --------------------------------------------------
# Run Game Theory Algorithm
# --------------------------------------------------

print()
print("=" * 60)
print("       SMART WI-FI BANDWIDTH SHARING")
print("=" * 60)

print()

print(
    f"Total Available Bandwidth : "
    f"{TOTAL_BANDWIDTH} Mbps"
)

print(
    f"Number of Active Users    : "
    f"{len(users)}"
)

print()


# --------------------------------------------------
# Find Nash Equilibrium
# --------------------------------------------------

result = find_nash_equilibrium(

    users,

    TOTAL_BANDWIDTH
)


allocations = result["allocations"]


# --------------------------------------------------
# Calculate Fairness
# --------------------------------------------------

fairness = jains_fairness_index(
    allocations
)


# --------------------------------------------------
# Display User Results
# --------------------------------------------------

print("-" * 60)

print(
    "USER BANDWIDTH ALLOCATION"
)

print("-" * 60)


for user in users:

    print(

        f"User {user.user_id:<5} | "

        f"Activity: "
        f"{user.activity:<15} | "

        f"Requested: "
        f"{user.requested_bandwidth:>6.2f} Mbps | "

        f"Allocated: "
        f"{user.allocated_bandwidth:>6.2f} Mbps | "

        f"Utility: "
        f"{user.utility:>8.4f}"

    )


# --------------------------------------------------
# Total Allocated Bandwidth
# --------------------------------------------------

total_allocated = sum(

    user.allocated_bandwidth

    for user in users

)


print()

print("-" * 60)

print(
    f"Total Allocated Bandwidth : "
    f"{total_allocated:.2f} Mbps"
)

print(
    f"Unused Bandwidth          : "
    f"{TOTAL_BANDWIDTH - total_allocated:.2f} Mbps"
)

print(
    f"Iterations                : "
    f"{result['iterations']}"
)

print(
    f"Jain Fairness Index       : "
    f"{fairness:.4f}"
)

print("-" * 60)

print()


# --------------------------------------------------
# Interpret Fairness
# --------------------------------------------------

if fairness >= 0.90:

    print(
        "Fairness Status : EXCELLENT"
    )

elif fairness >= 0.75:

    print(
        "Fairness Status : GOOD"
    )

elif fairness >= 0.50:

    print(
        "Fairness Status : MODERATE"
    )

else:

    print(
        "Fairness Status : POOR"
    )


print()

print("=" * 60)
print("              GAME COMPLETED")
print("=" * 60)
print()