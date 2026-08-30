# Experiment Methodology

## 1. Overview

This document describes the experimental framework used to evaluate bandwidth allocation strategies in the Smart Wi-Fi Bandwidth Sharing project.

The experiments answer the following research questions:

1. How does the Nash equilibrium allocation strategy compare to baseline strategies (Equal, Proportional, Priority) as the number of users increases?
2. How does allocation fairness (Jain's Fairness Index) vary with network scale?
3. How does average user utility vary across strategies and user counts?
4. What is the convergence behavior of the best-response dynamics?

## 2. Experiment Design

### 2.1 Structure

Experiments are organized as a **scalability study**:

- **Independent variable**: Number of users n ∈ {5, 10, 20, 30, 50, 100, 200, 373}
- **Dependent variables**: Allocation metrics per strategy (see Section 4)
- **Control variables**: Fixed parameters held constant across all runs (see Section 5)
- **Repetitions**: 1 per configuration (single-seed deterministic)

Each configuration produces one row per strategy in the output CSV, yielding 4 × 8 = 32 rows for the default experiment.

### 2.2 Why These User Counts?

The selected user counts span a wide range:

- **5–10 users**: Small home networks, underutilized capacity.
- **20–50 users**: Small office or dense residential scenarios.
- **100–200 users**: Large apartment buildings or campus hotspots.
- **373 users**: Matches the size of the real dataset (`data/Cleaned_Dataset.csv`), enabling future validation against real-world traces.

## 3. Independent Variables

| Variable | Type | Values / Range | Description |
|----------|------|----------------|-------------|
| `number_of_users` | Discrete | 5, 10, 20, 30, 50, 100, 200, 373 | Number of simulated Wi-Fi users |
| `total_bandwidth` | Continuous | 100.0 Mbps (fixed) | Total available channel capacity |
| `scenario` | Categorical | "medium" (fixed) | Traffic scenario label |
| `seed` | Integer | 42 (default) | Random seed for reproducibility |
| `congestion_penalty` | Continuous | 0.5 (fixed) | Weight w_C in the utility function |
| `step_size` | Continuous | 0.5 Mbps (fixed) | Grid search resolution for best response |
| `max_iterations` | Integer | 100 (fixed) | Maximum Nash equilibrium iterations |

### 3.1 Latency and Jitter

Latency and jitter are drawn from uniform distributions per experiment run:

- Latency: Uniform(8.0, 22.0) ms
- Jitter: Uniform(1.0, 6.0) ms

These ranges reflect typical 2.4 GHz and 5 GHz Wi-Fi operating conditions under moderate load.

The same seed produces identical latency/jitter values, ensuring reproducibility.

## 4. Dependent Variables

### 4.1 Primary Metrics

| Metric | Definition | Formula | Interpretation |
|--------|-----------|---------|----------------|
| `total_allocated` | Sum of all allocated bandwidths | Σ B_i | Higher = more capacity utilized |
| `utilization_percentage` | Fraction of total capacity used | (Σ B_i / B_total) × 100 | Higher = more efficient use of spectrum |
| `jain_fairness_index` | Jain's Fairness Index | (Σ B_i)^2 / (n · Σ B_i^2) | Closer to 1 = more equitable |
| `average_utility` | Mean utility across all users | (1/n) Σ U_i | Higher = greater aggregate welfare |

### 4.2 Derived Metrics

| Metric | Definition |
|--------|-----------|
| `unused_bandwidth` | B_total - Σ B_i |
| `fairness_status` | Categorical label: Excellent / Good / Moderate / Poor |
| `iterations` | Number of Nash iterations until convergence |

### 4.3 Per-User Metrics (Game Theory only)

| Metric | Definition |
|--------|-----------|
| `user_id` | Unique player identifier |
| `activity` | Traffic class (browsing, gaming, etc.) |
| `requested_bandwidth` | User's demand r_i |
| `allocated_bandwidth` | Final allocation B_i |
| `utility` | U_i at equilibrium |
| `activity_weight` | w_i for the user's activity |

## 5. Control Variables

These parameters are held constant across all experiment configurations unless explicitly varied in a sensitivity analysis:

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `total_bandwidth` | 100.0 Mbps | Typical aggregated Wi-Fi 6 capacity for a dense environment |
| `congestion_penalty` (w_C) | 0.5 | Mid-range penalty; sensitive to change |
| `step_size` (δ) | 0.5 Mbps | Balances accuracy and computation time |
| `max_iterations` | 100 | Sufficient for convergence in all tested configurations |
| `latency_range` | 8–22 ms | Measured Wi-Fi RTT range under moderate load |
| `jitter_range` | 1–6 ms | Measured Wi-Fi jitter range under moderate load |
| `activity_distribution` | Uniform over activities | Synthetic traffic generator selects activities uniformly at random |

## 6. Reproducibility

### 6.1 Deterministic Generation

All random values (user activities, bandwidth requests, latency, jitter) are generated from a fixed seed using Python's `random.Random(seed)`. Setting the same seed always produces the same synthetic network state.

### 6.2 Experiment Identity

Each experiment row is tagged with:

```
experiment_id = f"exp_{seed}_{number_of_users}"
```

This allows results to be traced back to the exact configuration that produced them.

### 6.3 Timestamp

Results include an ISO 8601 UTC timestamp (`datetime.utcnow().isoformat()`) recording when the experiment was executed.

## 7. Statistical Methods

### 7.1 Current Analysis

The current experiment design uses **single-seed, single-repetition** runs. This is appropriate for:

- Demonstrating algorithmic behavior across scales.
- Generating deterministic baseline comparisons.
- Producing figures for documentation and visualization.

Because there is only one observation per (user_count, strategy) cell, **statistical significance testing is not applicable** in the default setup.

### 7.2 When to Use Statistical Tests

If you increase `REPETITIONS` ≥ 2 in `backend/simulation/experiment_config.py`, the following methods become applicable:

| Comparison | Test | Assumptions |
|------------|------|-------------|
| Two independent groups, normal distribution | Independent samples t-test | Equal variances, n ≥ 30 per group (or normally distributed) |
| Two independent groups, unknown/non-normal distribution | Mann-Whitney U test | Ordinal or continuous data, independent samples |
| Multiple groups, normal distribution | One-way ANOVA | Normality, homogeneity of variance |
| Multiple groups, non-normal | Kruskal-Wallis H test | Ordinal or continuous data |

### 7.3 Confidence Intervals

For a sample of size k with mean μ and sample standard deviation s:

```
95% CI = μ ± t_{0.025, k-1} · (s / √k)
```

where t_{0.025, k-1} is the critical value from the Student t-distribution with k-1 degrees of freedom.

If k = 1 (current default), the confidence interval is undefined.

## 8. Baselines

The four strategies compared in every experiment were chosen to represent a spectrum of design philosophies:

| Strategy | Philosophy | Why Included |
|----------|-----------|--------------|
| **Equal Allocation** | Strict egalitarianism | Simplest possible policy; upper bound on fairness, lower bound on efficiency when requests differ |
| **Proportional Allocation** | Demand-responsive fairness | Industry standard (e.g., weighted fair queuing); respects individual demands |
| **Priority Allocation** | QoS differentiation | Represents how real networks often prioritize latency-sensitive traffic (e.g., Skype over FTP) |
| **Game Theory (Nash)** | Non-cooperative equilibrium | The proposed contribution; tests whether self-interested best responses yield better aggregate outcomes |

### 8.1 Why Not Max-Min Fairness or α-Fairness?

Max-min fairness and α-fairness are well-established benchmarks in network resource allocation. They are documented in `docs/game_theory.md` as planned extensions but are **not yet implemented** in the current codebase. Adding them would require:

- Implementing a water-filling algorithm for max-min fairness.
- Parameterizing the utility exponent α for α-fairness.
- Extending the evaluation service and CSV schema.

## 9. Experiment Execution Flow

```
run_experiment()
    │
    ├── for number_of_users in USER_COUNTS:
    │       │
    │       ├── generate_traffic_scenario(scenario, num_users, seed)
    │       │       ├── generate_users(num_users, seed)
    │       │       └── compute demand_ratio, congestion_level
    │       │
    │       ├── draw latency, jitter from RNG(seed)
    │       │
    │       └── evaluate_all_strategies(users, total_bandwidth, latency, jitter)
    │               ├── evaluate_equal(...)
    │               ├── evaluate_proportional(...)
    │               ├── evaluate_priority(...)
    │               └── evaluate_game_theory(...)
    │                       └── allocate_bandwidth(...)
    │                               └── find_nash_equilibrium(...)
    │
    └── save_results_to_csv(all_rows)
```

## 10. Threats to Validity

### 10.1 Internal Validity

- **Synthetic traffic only**: Results depend on the random user generator, not on real packet captures. Conclusions about real-world behavior require validation with production traces.
- **Single seed**: Random variation is not captured. Different seeds may produce different rankings.
- **Fixed latency/jitter**: These are drawn once per user count, not per strategy or per iteration. In reality, allocation strategy can affect measured latency.

### 10.2 External Validity

- **Single network capacity**: All experiments use 100 Mbps total bandwidth. Scaling to Gigabit or sub-6 GHz links may change relative performance.
- **Single traffic mix**: Activities are drawn uniformly. Real networks have skewed distributions (e.g., 80% streaming, 10% browsing).
- **No mobility**: Users are stationary with fixed demands. Mobile Wi-Fi with handoffs is not modeled.

### 10.3 Construct Validity

- **Utility function**: The chosen weights (w_C = 0.5, activity weights, QoS weights) are heuristic. Different parameterizations could change equilibrium outcomes.
- **Fairness metric**: Jain's index is sensitive to the number of users and does not distinguish between "everyone gets a little" and "everyone gets enough."
