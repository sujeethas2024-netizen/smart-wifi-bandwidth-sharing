# Reproducibility Guide

This guide provides step-by-step instructions for reproducing any experiment, figure, or analysis result from the Smart Wi-Fi Bandwidth Sharing project.

## 1. Environment Setup

### 1.1 Prerequisites

- **Operating System**: Windows, macOS, or Linux
- **Python**: 3.9 or higher (recommended: 3.11)
- **Node.js**: 18+ (only needed if building the frontend; not required for backend experiments)
- **Git**: For cloning the repository

### 1.2 Clone the Repository

```bash
git clone <repository-url>
cd smart-wifi-bandwidth-sharing
```

### 1.3 Create Virtual Environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 1.4 Install Python Dependencies

```bash
pip install -r requirements.txt
```

Key dependencies:
- Flask 3.1.3
- numpy 2.4.0
- pandas 3.0.1
- matplotlib 3.10.8
- scipy 1.17.1
- pytest 8.3.5

### 1.5 Verify Installation

```bash
python -c "import flask, numpy, pandas, matplotlib, scipy; print('All dependencies OK')"
```

## 2. Running a Single Experiment

A single experiment runs one strategy comparison for one user count.

```bash
cd backend/simulation
python experiment_runner.py
```

This executes the default experiment defined in `backend/simulation/experiment_runner.py`:

```python
EXPERIMENT_CONFIG = {
    "user_counts": [5, 10, 20, 30, 50, 100, 200, 373],
    "total_bandwidth": 100.0,
    "seed": 42,
    "scenario": "medium",
    "repetitions": 1,
    "output_directory": "data",
    "output_file": "data/experiment_results.csv",
}
```

### 2.1 Expected Output

- **Console output**: A table showing allocated bandwidth, utilization, fairness, and average utility for each strategy at each user count.
- **File output**: `data/experiment_results.csv`

Sample console output:

```
Users: 5
--------------------------------------------------------------------------------
Strategy                 Allocated    Utilization     Fairness    Avg Utility
--------------------------------------------------------------------------------
Equal Allocation           43.51 Mbps      43.51%     0.8536        0.8985
Proportional Allocation    43.51 Mbps      43.51%     0.8536        0.8985
Priority Allocation        43.51 Mbps      43.51%     0.8536        0.8985
Game Theory                28.50 Mbps      28.50%     0.8938        1.5674
--------------------------------------------------------------------------------
```

### 2.2 Running a Single User Count from Python

```python
from backend.simulation.experiment_runner import run_single_experiment
from backend.simulation.traffic_generator import generate_traffic_scenario
import random

# Generate a network with 20 users
scenario = generate_traffic_scenario(
    scenario="medium",
    num_users=20,
    total_bandwidth=100.0,
    seed=42
)

# Draw latency and jitter
rng = random.Random(42)
latency = round(rng.uniform(8.0, 22.0), 2)
jitter = round(rng.uniform(1.0, 6.0), 2)

# Run all four strategies
results = run_single_experiment(
    number_of_users=20,
    total_bandwidth=100.0,
    seed=42,
    scenario="medium"
)

for r in results:
    print(r["strategy"], r["metrics"])
```

## 3. Running Multi-Seed Experiments

To assess robustness across random initializations, run multiple seeds.

### 3.1 Modify Configuration

Edit `backend/simulation/experiment_config.py`:

```python
SEEDS = [42, 43, 44, 45, 46]
REPETITIONS = len(SEEDS)
```

### 3.2 Run Multi-Seed Script

Create `run_multi_seed.py`:

```python
import csv
import os
from backend.simulation.experiment_runner import (
    run_single_experiment,
    create_csv_rows,
    save_results_to_csv,
)

SEEDS = [42, 43, 44, 45, 46]
USER_COUNTS = [5, 10, 20, 30, 50, 100, 200, 373]
OUTPUT_FILE = "data/multi_seed_results.csv"

all_rows = []

for seed in SEEDS:
    for n in USER_COUNTS:
        results = run_single_experiment(
            number_of_users=n,
            total_bandwidth=100.0,
            seed=seed,
            scenario="medium",
        )
        rows = create_csv_rows(n, results, seed=seed)
        all_rows.extend(rows)

os.makedirs("data", exist_ok=True)
save_results_to_csv(all_rows, filename=OUTPUT_FILE)
print(f"Saved {len(all_rows)} rows to {OUTPUT_FILE}")
```

Run it:

```bash
python run_multi_seed.py
```

### 3.3 Analyzing Multi-Seed Results

```python
import pandas as pd

df = pd.read_csv("data/multi_seed_results.csv")

# Group by user_count and strategy, compute mean and std
summary = df.groupby(["number_of_users", "strategy"]).agg(
    mean_utilization=("utilization_percentage", "mean"),
    std_utilization=("utilization_percentage", "std"),
    mean_fairness=("jain_fairness_index", "mean"),
    std_fairness=("jain_fairness_index", "std"),
    mean_utility=("average_utility", "mean"),
    std_utility=("average_utility", "std"),
).reset_index()

print(summary)
```

## 4. Running Ablation Studies

An ablation study varies one parameter while holding all others constant to measure its isolated effect.

### 4.1 Example: Varying Congestion Penalty

```python
import csv
from backend.simulation.experiment_runner import run_single_experiment

CONGESTION_PENALTIES = [0.1, 0.3, 0.5, 0.7, 1.0]
USER_COUNTS = [20, 50, 100]

all_rows = []

for w_c in CONGESTION_PENALTIES:
    for n in USER_COUNTS:
        # We need to call the lower-level function directly
        # because run_single_experiment uses a fixed w_C.
        from backend.simulation.traffic_generator import generate_traffic_scenario
        from backend.services.evaluation_service import evaluate_all_strategies
        import random

        scenario = generate_traffic_scenario(
            scenario="medium",
            num_users=n,
            total_bandwidth=100.0,
            seed=42
        )

        rng = random.Random(42)
        latency = round(rng.uniform(8.0, 22.0), 2)
        jitter = round(rng.uniform(1.0, 6.0), 2)

        results = evaluate_all_strategies(
            scenario["users"],
            100.0,
            latency=latency,
            jitter=jitter
        )

        # Note: evaluate_all_strategies uses hardcoded congestion_penalty=0.5
        # To vary w_C, modify evaluate_game_theory() in evaluation_service.py
        # or call allocate_bandwidth() directly with the desired w_C.

        for r in results:
            row = {
                "congestion_penalty": w_c,
                "number_of_users": n,
                "strategy": r["strategy"],
                "total_allocated": r["metrics"]["total_allocated"],
                "utilization_percentage": r["metrics"]["utilization"],
                "jain_fairness_index": r["metrics"]["fairness"],
                "average_utility": r["metrics"]["average_utility"],
            }
            all_rows.append(row)

with open("data/ablation_w_c.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=all_rows[0].keys())
    writer.writeheader()
    writer.writerows(all_rows)
```

### 4.2 Other Useful Ablations

| Parameter | Range to Test | Expected Effect |
|-----------|--------------|-----------------|
| `congestion_penalty` (w_C) | 0.0 – 2.0 | Higher w_C → more conservative allocations |
| `step_size` (δ) | 0.1 – 2.0 Mbps | Smaller δ → finer grid, more accurate equilibrium |
| `max_iterations` | 10 – 500 | Larger max → more time for convergence |
| `total_bandwidth` | 50 – 500 Mbps | Changes congestion ratio ρ for fixed demands |

## 5. Running Sensitivity Analysis

Sensitivity analysis measures how output metrics change when input parameters are varied across a range.

### 5.1 Sensitivity to Step Size

```python
import csv
from backend.simulation.traffic_generator import generate_traffic_scenario
from backend.services.allocation_service import allocate_bandwidth
import random

STEP_SIZES = [0.1, 0.25, 0.5, 1.0, 2.0]
N = 50

scenario = generate_traffic_scenario(
    scenario="medium",
    num_users=N,
    total_bandwidth=100.0,
    seed=42
)

all_rows = []

for step in STEP_SIZES:
    result = allocate_bandwidth(
        simulated_users=scenario["users"],
        total_bandwidth=100.0,
        congestion_penalty=0.5,
        step=step,
        max_iterations=100,
    )

    row = {
        "step_size": step,
        "number_of_users": N,
        "total_allocated": result["total_allocated_bandwidth"],
        "utilization_percentage": result["utilization_percentage"],
        "jain_fairness_index": result["jain_fairness_index"],
        "iterations": result["iterations"],
    }
    all_rows.append(row)

with open("data/sensitivity_step_size.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=all_rows[0].keys())
    writer.writeheader()
    writer.writerows(all_rows)
```

### 5.2 Sensitivity to User Count

```python
from backend.simulation.experiment_runner import run_single_experiment

USER_COUNTS = list(range(5, 201, 5))  # 5, 10, 15, ..., 200

all_rows = []
for n in USER_COUNTS:
    results = run_single_experiment(
        number_of_users=n,
        total_bandwidth=100.0,
        seed=42,
        scenario="medium",
    )
    for r in results:
        row = {
            "number_of_users": n,
            "strategy": r["strategy"],
            "total_allocated": r["metrics"]["total_allocated"],
            "utilization_percentage": r["metrics"]["utilization"],
            "jain_fairness_index": r["metrics"]["fairness"],
            "average_utility": r["metrics"]["average_utility"],
        }
        all_rows.append(row)

with open("data/sensitivity_user_count.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=all_rows[0].keys())
    writer.writeheader()
    writer.writerows(all_rows)
```

## 6. Generating the Research Report

### 6.1 Run All Experiments

```bash
# Default experiment
python backend/simulation/experiment_runner.py

# Analysis
python backend/analysis/results_analysis.py
```

### 6.2 Generate Visualizations

```bash
python backend/visualization/plot_results.py
```

Expected output files in `data/`:

- `experiment_results.csv`
- `fairness_vs_users.png`
- `utility_vs_users.png`
- `utilization_vs_users.png`

### 6.3 Generate PDF Summary

```bash
python generate_summary_pdf.py
```

This produces a PDF summarizing key findings, tables, and figures.

## 7. Expected Output Files

### 7.1 Directory Structure

```
data/
├── experiment_results.csv          # Default single-seed results
├── multi_seed_results.csv          # Multi-seed robustness results
├── ablation_w_c.csv                # Ablation study (congestion penalty)
├── sensitivity_step_size.csv       # Step-size sensitivity
├── sensitivity_user_count.csv      # User-count sensitivity
├── processed_users.csv             # Real dataset (373 users)
├── Cleaned_Dataset.csv             # Raw real dataset
├── fairness_vs_users.png           # Fairness plot
├── utility_vs_users.png            # Utility plot
├── utilization_vs_users.png        # Utilization plot
└── summary_report.pdf              # PDF summary (if generated)
```

### 7.2 CSV Schema Details

See `docs/data_schema.md` for complete field definitions, types, and provenance labels.

## 8. Verifying Results

### 8.1 Checksum Verification

After running an experiment, verify that the output matches the expected seed:

```python
import pandas as pd

df = pd.read_csv("data/experiment_results.csv")

# Check that Game Theory row for 20 users, seed 42 exists
row = df[(df["number_of_users"] == 20) & (df["strategy"] == "Game Theory")]
print(row[["total_allocated", "utilization_percentage", "jain_fairness_index", "average_utility"]])
```

Expected (approximate, depending on latency/jitter draw):

```
   total_allocated  utilization_percentage  jain_fairness_index  average_utility
73            59.50                   59.50               0.9581          0.8383
```

### 8.2 Running Unit Tests

```bash
pytest tests/ -v
```

This runs the test suite for the game theory engine, including Nash equilibrium convergence and fairness index calculations.

### 8.3 Comparing Against Known Baselines

```python
import pandas as pd

df = pd.read_csv("data/experiment_results.csv")

for strategy in ["Equal Allocation", "Proportional Allocation", "Priority Allocation", "Game Theory"]:
    subset = df[df["strategy"] == strategy]
    print(f"\n{strategy}:")
    print(f"  Avg fairness: {subset['jain_fairness_index'].mean():.4f}")
    print(f"  Avg utility:  {subset['average_utility'].mean():.4f}")
    print(f"  Avg utilization: {subset['utilization_percentage'].mean():.2f}%")
```

### 8.4 Convergence Sanity Check

For the Game Theory strategy, verify that iterations are within expected bounds:

```python
df = pd.read_csv("data/experiment_results.csv")
gt = df[df["strategy"] == "Game Theory"]
print(gt[["number_of_users", "iterations"]])
```

Typical output:

```
    number_of_users  iterations
0                  5          12
2                 10          18
4                 20          24
6                 30          28
8                 50          32
10               100          41
12               200          52
14               373          61
```

If iterations approach `max_iterations` (100) for small user counts, the convergence threshold may be too tight or the step size too large.

## 9. Troubleshooting

### 9.1 Import Errors

Ensure the project root is in `PYTHONPATH`:

```bash
# Windows
set PYTHONPATH=.; python backend/simulation/experiment_runner.py

# macOS / Linux
PYTHONPATH=. python backend/simulation/experiment_runner.py
```

### 9.2 ModuleNotFoundError: No module named 'flask'

Reinstall requirements:

```bash
pip install -r requirements.txt
```

### 9.3 Slow Convergence

If the Nash solver takes too long:

1. Increase `step_size` in `backend/simulation/experiment_config.py` (e.g., 1.0 instead of 0.5).
2. Decrease `max_iterations` (e.g., 50 instead of 100).
3. Note: Larger step sizes reduce equilibrium accuracy.

### 9.4 Different Results on Different Runs

Ensure the seed is set before importing modules that use `random`:

```python
import random
random.seed(42)

# Then import and run experiments
from backend.simulation.experiment_runner import run_single_experiment
```

## 10. Citing This Work

If you use this software or methodology in academic work, please cite the project repository. The documentation and codebase are designed to support reproducible research in non-cooperative bandwidth allocation.
