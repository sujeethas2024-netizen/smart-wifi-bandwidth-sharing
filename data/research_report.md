# Smart WiFi Bandwidth Sharing — Research Report

*Generated: 2026-08-30T04:34:56.893491 (UTC)*

## Provenance Metadata

All metrics are labeled according to the project's data provenance model:

- SIMULATION: synthetic traffic scenarios (user demand).
- CALCULATED_FROM_REAL_DATA: allocation + metrics (deterministic).
- REAL_DATASET: not used in simulation experiments.
- REAL_RUNTIME_MEASUREMENT: not used (simulation environment).
- USER_INPUT: not used.

## 1. Experimental Configuration

- Random seed (base): `42`
- Repetitions: `2`
- User counts: `[5, 10]`
- Algorithms: `['equal', 'proportional']`
- Total bandwidth: `100.0` Mbps
- Scenario: `medium`
- Alpha (alpha-fair): `1.0`
- Max iterations (game theory): `100`
- Utility weights: `{'w_throughput': 1.0, 'w_latency': 0.5, 'w_jitter': 0.3, 'w_congestion': 0.5, 'w_qos': 0.4}`
- Traffic class distribution: `{'browsing': 0.2, 'online_class': 0.2, 'gaming': 0.2, 'streaming': 0.2, 'downloading': 0.2}`

## 2. Raw Results Summary

Total raw repetitions: `8`

Sample of raw results (first 10 rows):

| experiment_id | timestamp | seed | number_of_users | strategy | total_bandwidth | total_allocated | utilization_percentage | jain_fairness_index | average_utility | latency_ms | jitter_ms | repetition | computational_time | convergence_iterations | data_source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| exp_42_5_equal_1 | 2026-08-30T04:34:56.762050 | 42 | 5 | equal | 100.0 | 43.51 | 43.51 | 0.8536 | 0.3838 | 16.95 | 1.13 | 1 | 0.0001 | nan | SIMULATION |
| exp_42_5_equal_2 | 2026-08-30T04:34:56.762129 | 43 | 5 | equal | 100.0 | 57.93 | 57.93 | 0.8118 | -1.0786 | 8.54 | 4.48 | 2 | 0.0001 | nan | SIMULATION |
| exp_42_5_proportional_1 | 2026-08-30T04:34:56.762198 | 42 | 5 | proportional | 100.0 | 43.51 | 43.51 | 0.8536 | 0.3838 | 16.95 | 1.13 | 1 | 0.0001 | nan | SIMULATION |
| exp_42_5_proportional_2 | 2026-08-30T04:34:56.762258 | 43 | 5 | proportional | 100.0 | 57.93 | 57.93 | 0.8118 | -1.0786 | 8.54 | 4.48 | 2 | 0.0001 | nan | SIMULATION |
| exp_42_10_equal_1 | 2026-08-30T04:34:56.762336 | 42 | 10 | equal | 100.0 | 83.16 | 83.16 | 0.9016 | -1.1497 | 16.95 | 1.13 | 1 | 0.0001 | nan | SIMULATION |
| exp_42_10_equal_2 | 2026-08-30T04:34:56.762406 | 43 | 10 | equal | 100.0 | 88.73 | 88.73 | 0.9512 | -1.6432 | 8.54 | 4.48 | 2 | 0.0001 | nan | SIMULATION |
| exp_42_10_proportional_1 | 2026-08-30T04:34:56.762477 | 42 | 10 | proportional | 100.0 | 100.0 | 100.0 | 0.7951 | -2.6027 | 16.95 | 1.13 | 1 | 0.0001 | nan | SIMULATION |
| exp_42_10_proportional_2 | 2026-08-30T04:34:56.762549 | 43 | 10 | proportional | 100.0 | 100.0 | 100.0 | 0.8273 | -2.6745 | 8.54 | 4.48 | 2 | 0.0001 | nan | SIMULATION |


## 3. Aggregated Statistics

Total aggregated groups: `4`

| number_of_users | strategy | n | total_allocated_mean | total_allocated_median | total_allocated_std_dev | total_allocated_min | total_allocated_max | total_allocated_ci_95_lower | total_allocated_ci_95_upper | utilization_percentage_mean | utilization_percentage_median | utilization_percentage_std_dev | utilization_percentage_min | utilization_percentage_max | utilization_percentage_ci_95_lower | utilization_percentage_ci_95_upper | jain_fairness_index_mean | jain_fairness_index_median | jain_fairness_index_std_dev | jain_fairness_index_min | jain_fairness_index_max | jain_fairness_index_ci_95_lower | jain_fairness_index_ci_95_upper | average_utility_mean | average_utility_median | average_utility_std_dev | average_utility_min | average_utility_max | average_utility_ci_95_lower | average_utility_ci_95_upper | computational_time_mean | computational_time_median | computational_time_std_dev | computational_time_min | computational_time_max | computational_time_ci_95_lower | computational_time_ci_95_upper |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5 | equal | 2 | 50.72 | 50.72 | 10.19648 | 43.51 | 57.93 | -40.891736 | 142.331736 | 50.72 | 50.72 | 10.19648 | 43.51 | 57.93 | -40.891736 | 142.331736 | 0.8327 | 0.8327 | 0.029557 | 0.8118 | 0.8536 | 0.56714 | 1.09826 | -0.3474 | -0.3474 | 1.034073 | -1.0786 | 0.3838 | -9.638177 | 8.943377 | 0.0001 | 0.0001 | 0.0 | 0.0001 | 0.0001 | 0.0001 | 0.0001 |
| 5 | proportional | 2 | 50.72 | 50.72 | 10.19648 | 43.51 | 57.93 | -40.891736 | 142.331736 | 50.72 | 50.72 | 10.19648 | 43.51 | 57.93 | -40.891736 | 142.331736 | 0.8327 | 0.8327 | 0.029557 | 0.8118 | 0.8536 | 0.56714 | 1.09826 | -0.3474 | -0.3474 | 1.034073 | -1.0786 | 0.3838 | -9.638177 | 8.943377 | 0.0001 | 0.0001 | 0.0 | 0.0001 | 0.0001 | 0.0001 | 0.0001 |
| 10 | equal | 2 | 85.945 | 85.945 | 3.938585 | 83.16 | 88.73 | 50.55822 | 121.33178 | 85.945 | 85.945 | 3.938585 | 83.16 | 88.73 | 50.55822 | 121.33178 | 0.9264 | 0.9264 | 0.035072 | 0.9016 | 0.9512 | 0.611286 | 1.241514 | -1.39645 | -1.39645 | 0.348957 | -1.6432 | -1.1497 | -4.531706 | 1.738806 | 0.0001 | 0.0001 | 0.0 | 0.0001 | 0.0001 | 0.0001 | 0.0001 |
| 10 | proportional | 2 | 100.0 | 100.0 | 0.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 0.0 | 100.0 | 100.0 | 100.0 | 100.0 | 0.8112 | 0.8112 | 0.022769 | 0.7951 | 0.8273 | 0.60663 | 1.01577 | -2.6386 | -2.6386 | 0.05077 | -2.6745 | -2.6027 | -3.094753 | -2.182447 | 0.0001 | 0.0001 | 0.0 | 0.0001 | 0.0001 | 0.0001 | 0.0001 |


## 4. Statistical Significance Tests

### Metric: `average_utility`

- Baseline (`equal`) mean: `-0.8719250000000001` (n=4)
- Proposed (`game_theory`) mean: `None` (n=0)
- Paired t-test: t=`None`, p=`None`, dof=`None`
- Cohen's d: `None` (insufficient data)
- Warning: Sample size too small for t-test (n < 2)

### Metric: `jain_fairness_index`

- Baseline (`equal`) mean: `0.87955` (n=4)
- Proposed (`game_theory`) mean: `None` (n=0)
- Paired t-test: t=`None`, p=`None`, dof=`None`
- Cohen's d: `None` (insufficient data)
- Warning: Sample size too small for t-test (n < 2)

### Metric: `utilization_percentage`

- Baseline (`equal`) mean: `68.3325` (n=4)
- Proposed (`game_theory`) mean: `None` (n=0)
- Paired t-test: t=`None`, p=`None`, dof=`None`
- Cohen's d: `None` (insufficient data)
- Warning: Sample size too small for t-test (n < 2)


## 5. Baseline Comparison

Comparison of proposed strategy against the equal-allocation baseline.

| equal | proportional |
| --- | --- |
| -0.3474 | -0.3474 |
| -1.39645 | -2.6386 |


## 6. Scalability Analysis

Computational time vs number of users (mean across algorithms):

| number_of_users | computational_time_mean |
| --- | --- |
| 5.0 | 0.0001 |
| 10.0 | 0.0001 |


## 7. Sensitivity Analysis

### Parameter: `w_throughput`

| experiment_id | timestamp | seed | parameter | parameter_value | number_of_users | strategy | total_bandwidth | total_allocated | utilization_percentage | jain_fairness_index | average_utility | latency_ms | jitter_ms | computational_time | data_source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sensitivity_42_5_equal_w_throughput_0.5_42 | 2026-08-30T04:34:56.853045 | 42 | w_throughput | 0.5 | 5 | equal | 100.0 | 43.51 | 43.51 | 0.8536 | -0.945416 | 16.95 | 1.13 | 0.000114 | SIMULATION |
| sensitivity_42_5_equal_w_throughput_0.5_43 | 2026-08-30T04:34:56.853251 | 43 | w_throughput | 0.5 | 5 | equal | 100.0 | 57.93 | 57.93 | 0.8118 | -2.448095 | 8.54 | 4.48 | 7.2e-05 | SIMULATION |
| sensitivity_42_5_proportional_w_throughput_0.5_42 | 2026-08-30T04:34:56.853435 | 42 | w_throughput | 0.5 | 5 | proportional | 100.0 | 43.51 | 43.51 | 0.8536 | -0.945416 | 16.95 | 1.13 | 6.3e-05 | SIMULATION |
| sensitivity_42_5_proportional_w_throughput_0.5_43 | 2026-08-30T04:34:56.853596 | 43 | w_throughput | 0.5 | 5 | proportional | 100.0 | 57.93 | 57.93 | 0.8118 | -2.448095 | 8.54 | 4.48 | 5.2e-05 | SIMULATION |
| sensitivity_42_10_equal_w_throughput_0.5_42 | 2026-08-30T04:34:56.853806 | 42 | w_throughput | 0.5 | 10 | equal | 100.0 | 83.16 | 83.16 | 0.9016 | -2.424284 | 16.95 | 1.13 | 6.9e-05 | SIMULATION |
| sensitivity_42_10_equal_w_throughput_0.5_43 | 2026-08-30T04:34:56.853999 | 43 | w_throughput | 0.5 | 10 | equal | 100.0 | 88.73 | 88.73 | 0.9512 | -2.924249 | 8.54 | 4.48 | 6.4e-05 | SIMULATION |
| sensitivity_42_10_proportional_w_throughput_0.5_42 | 2026-08-30T04:34:56.854179 | 42 | w_throughput | 0.5 | 10 | proportional | 100.0 | 100.0 | 100.0 | 0.7951 | -3.928942 | 16.95 | 1.13 | 5.2e-05 | SIMULATION |
| sensitivity_42_10_proportional_w_throughput_0.5_43 | 2026-08-30T04:34:56.854307 | 43 | w_throughput | 0.5 | 10 | proportional | 100.0 | 100.0 | 100.0 | 0.8273 | -3.978468 | 8.54 | 4.48 | 4e-05 | SIMULATION |
| sensitivity_42_5_equal_w_throughput_1.0_42 | 2026-08-30T04:34:56.854409 | 42 | w_throughput | 1.0 | 5 | equal | 100.0 | 43.51 | 43.51 | 0.8536 | 0.450404 | 16.95 | 1.13 | 2.9e-05 | SIMULATION |
| sensitivity_42_5_equal_w_throughput_1.0_43 | 2026-08-30T04:34:56.854501 | 43 | w_throughput | 1.0 | 5 | equal | 100.0 | 57.93 | 57.93 | 0.8118 | -0.904578 | 8.54 | 4.48 | 2.8e-05 | SIMULATION |
| sensitivity_42_5_proportional_w_throughput_1.0_42 | 2026-08-30T04:34:56.854598 | 42 | w_throughput | 1.0 | 5 | proportional | 100.0 | 43.51 | 43.51 | 0.8536 | 0.450404 | 16.95 | 1.13 | 3.2e-05 | SIMULATION |
| sensitivity_42_5_proportional_w_throughput_1.0_43 | 2026-08-30T04:34:56.854690 | 43 | w_throughput | 1.0 | 5 | proportional | 100.0 | 57.93 | 57.93 | 0.8118 | -0.904578 | 8.54 | 4.48 | 2.8e-05 | SIMULATION |
| sensitivity_42_10_equal_w_throughput_1.0_42 | 2026-08-30T04:34:56.854802 | 42 | w_throughput | 1.0 | 10 | equal | 100.0 | 83.16 | 83.16 | 0.9016 | -1.107616 | 16.95 | 1.13 | 3.5e-05 | SIMULATION |
| sensitivity_42_10_equal_w_throughput_1.0_43 | 2026-08-30T04:34:56.854920 | 43 | w_throughput | 1.0 | 10 | equal | 100.0 | 88.73 | 88.73 | 0.9512 | -1.541165 | 8.54 | 4.48 | 3.8e-05 | SIMULATION |
| sensitivity_42_10_proportional_w_throughput_1.0_42 | 2026-08-30T04:34:56.855033 | 42 | w_throughput | 1.0 | 10 | proportional | 100.0 | 100.0 | 100.0 | 0.7951 | -2.558143 | 16.95 | 1.13 | 3.5e-05 | SIMULATION |
| sensitivity_42_10_proportional_w_throughput_1.0_43 | 2026-08-30T04:34:56.855143 | 43 | w_throughput | 1.0 | 10 | proportional | 100.0 | 100.0 | 100.0 | 0.8273 | -2.566841 | 8.54 | 4.48 | 3.4e-05 | SIMULATION |
| sensitivity_42_5_equal_w_throughput_1.5_42 | 2026-08-30T04:34:56.855242 | 42 | w_throughput | 1.5 | 5 | equal | 100.0 | 43.51 | 43.51 | 0.8536 | 1.846224 | 16.95 | 1.13 | 2.8e-05 | SIMULATION |
| sensitivity_42_5_equal_w_throughput_1.5_43 | 2026-08-30T04:34:56.855332 | 43 | w_throughput | 1.5 | 5 | equal | 100.0 | 57.93 | 57.93 | 0.8118 | 0.63894 | 8.54 | 4.48 | 2.7e-05 | SIMULATION |
| sensitivity_42_5_proportional_w_throughput_1.5_42 | 2026-08-30T04:34:56.855421 | 42 | w_throughput | 1.5 | 5 | proportional | 100.0 | 43.51 | 43.51 | 0.8536 | 1.846224 | 16.95 | 1.13 | 2.7e-05 | SIMULATION |
| sensitivity_42_5_proportional_w_throughput_1.5_43 | 2026-08-30T04:34:56.855511 | 43 | w_throughput | 1.5 | 5 | proportional | 100.0 | 57.93 | 57.93 | 0.8118 | 0.63894 | 8.54 | 4.48 | 2.7e-05 | SIMULATION |
| sensitivity_42_10_equal_w_throughput_1.5_42 | 2026-08-30T04:34:56.855621 | 42 | w_throughput | 1.5 | 10 | equal | 100.0 | 83.16 | 83.16 | 0.9016 | 0.209052 | 16.95 | 1.13 | 3.4e-05 | SIMULATION |
| sensitivity_42_10_equal_w_throughput_1.5_43 | 2026-08-30T04:34:56.855733 | 43 | w_throughput | 1.5 | 10 | equal | 100.0 | 88.73 | 88.73 | 0.9512 | -0.158082 | 8.54 | 4.48 | 3.6e-05 | SIMULATION |
| sensitivity_42_10_proportional_w_throughput_1.5_42 | 2026-08-30T04:34:56.855849 | 42 | w_throughput | 1.5 | 10 | proportional | 100.0 | 100.0 | 100.0 | 0.7951 | -1.187343 | 16.95 | 1.13 | 3.5e-05 | SIMULATION |
| sensitivity_42_10_proportional_w_throughput_1.5_43 | 2026-08-30T04:34:56.855960 | 43 | w_throughput | 1.5 | 10 | proportional | 100.0 | 100.0 | 100.0 | 0.8273 | -1.155213 | 8.54 | 4.48 | 3.4e-05 | SIMULATION |


## 8. Ablation Study

Mean delta (full model - ablated) per component:

### Component removed: `throughput_benefit`

- `total_allocated_mean`: `0.0`
- `utilization_percentage_mean`: `0.0`
- `jain_fairness_index_mean`: `0.0`
- `average_utility_mean`: `2.840213`

### Component removed: `congestion_penalty`

- `total_allocated_mean`: `0.0`
- `utilization_percentage_mean`: `0.0`
- `jain_fairness_index_mean`: `0.0`
- `average_utility_mean`: `-3.486538`

### Component removed: `latency_penalty`

- `total_allocated_mean`: `0.0`
- `utilization_percentage_mean`: `0.0`
- `jain_fairness_index_mean`: `0.0`
- `average_utility_mean`: `-0.318187`

### Component removed: `jitter_penalty`

- `total_allocated_mean`: `0.0`
- `utilization_percentage_mean`: `0.0`
- `jain_fairness_index_mean`: `0.0`
- `average_utility_mean`: `-0.217957`

### Component removed: `qos_violation_penalty`

- `total_allocated_mean`: `0.0`
- `utilization_percentage_mean`: `0.0`
- `jain_fairness_index_mean`: `0.0`
- `average_utility_mean`: `-0.536145`


## 9. Generated Plots

Plots are generated from the CSV artifacts. When experiments have not been run, the artifacts are absent and plotting is skipped.

- `fairness_by_users.png` — Jain fairness index vs number of users (one line per algorithm) from `aggregated_results.csv`.
- `utility_distribution.png` — distribution of average utility across repetitions from `raw_results.csv`.
- `computational_time.png` — mean computational time vs number of users from `aggregated_results.csv`.
- `sensitivity_<parameter>.png` — fairness/utility/utilization vs weight value from `sensitivity_results.csv`.
- `ablation_impact.png` — component impact bars from `ablation_results.csv`.


## 10. Reproducibility Instructions

1. Set the working directory to the repository root (so `data/` resolves).
2. Install dependencies: `pip install -r requirements.txt`.
3. Run the multi-seed experiment:

```python
from backend.experiments.config_schema import ExperimentConfig
from backend.experiments.runner import run_multi_seed_experiment

config = ExperimentConfig.from_dict({'seed': 42, 'repetitions': 2, 'user_counts': [5, 10], 'total_bandwidth': 100.0, 'scenario': 'medium', 'algorithms': ['equal', 'proportional'], 'utility_weights': {'w_throughput': 1.0, 'w_latency': 0.5, 'w_jitter': 0.3, 'w_congestion': 0.5, 'w_qos': 0.4}, 'traffic_class_distribution': {'browsing': 0.2, 'online_class': 0.2, 'gaming': 0.2, 'streaming': 0.2, 'downloading': 0.2}, 'output_directory': 'data', 'alpha': 1.0, 'max_iterations': 100, 'description': 'Multi-seed reproducible experiment'})
run_multi_seed_experiment(config)
```

4. Run the ablation study:

```python
from backend.experiments.ablation import run_ablation
run_ablation(config)
```

5. Run a sensitivity analysis:

```python
from backend.experiments.sensitivity import run_sensitivity_analysis
run_sensitivity_analysis(config, 'w_throughput', [0.5, 1.0, 1.5, 2.0])
```

6. Generate this report:

```python
from backend.experiments.report import generate_report
generate_report()
```

All randomness is seeded; identical seeds reproduce identical results.

