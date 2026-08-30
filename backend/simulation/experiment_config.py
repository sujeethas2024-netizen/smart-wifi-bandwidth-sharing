"""
Experiment Configuration

Reproducible settings for research experiments.
Modify these values to change experimental parameters.
"""

# ============================================================
# EXPERIMENT PARAMETERS
# ============================================================

EXPERIMENT_SEED = 42

TOTAL_BANDWIDTH_MBPS = 100.0

USER_COUNTS = [
    5,
    10,
    20,
    30,
    50,
    100,
    200,
    373,
]

SCENARIO = "medium"

REPETITIONS = 1

# ============================================================
# GAME THEORY PARAMETERS
# ============================================================

CONGESTION_PENALTY = 0.5

STEP_SIZE = 0.5

MAX_ITERATIONS = 100

# ============================================================
# QoS PARAMETERS
# ============================================================

LATENCY_RANGE_MS = (8.0, 22.0)

JITTER_RANGE_MS = (1.0, 6.0)

# ============================================================
# PATHS
# ============================================================

OUTPUT_DIRECTORY = "data"

OUTPUT_FILE = "data/experiment_results.csv"

DATASET_PATH = "data/processed_users.csv"

# ============================================================
# EXPERIMENT METADATA
# ============================================================

EXPERIMENT_DESCRIPTION = (
    "Scalability experiment comparing Equal, Proportional, "
    "Priority, and Game Theory allocation strategies across "
    "increasing user counts."
)

VERSION = "1.0.0"
