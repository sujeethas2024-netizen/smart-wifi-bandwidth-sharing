"""
Statistical Tests for Experiment Comparison

Implements paired t-test, Wilcoxon signed-rank test, Mann-Whitney U test,
Cohen's d, confidence intervals, Benjamini-Hochberg FDR correction, and
strategy comparison helpers for evaluating allocation algorithms.
"""

import csv
import json
import os
import warnings
from typing import Optional, Dict, Any, List, Tuple

import numpy as np
from scipy import stats


# ============================================================
# PAIRING UTILITIES
# ============================================================

def build_paired_groups(
    raw_results: list,
    metric: str,
    baseline: str,
    proposed: str,
) -> Tuple[np.ndarray, np.ndarray, int]:
    """
    Build paired samples from raw experiment results.

    Pairs are constructed on (seed, number_of_users) so that each
    observation corresponds to the same experimental condition
    across both algorithms.

    Parameters
    ----------
    raw_results : list
        Raw result dictionaries.
    metric : str
        Metric name to extract.
    baseline : str
        Baseline strategy name.
    proposed : str
        Proposed strategy name.

    Returns
    -------
    tuple
        (baseline_values, proposed_values, pair_count) as numpy arrays.
    """
    lookup: Dict[Tuple[int, int], Dict[str, float]] = {}
    for r in raw_results:
        key = (int(r["seed"]), int(r["number_of_users"]))
        strategy = r.get("strategy")
        if strategy in (baseline, proposed):
            if metric not in r:
                continue
            try:
                value = float(r[metric])
            except (TypeError, ValueError):
                continue
            lookup.setdefault(key, {})[strategy] = value

    baseline_vals: List[float] = []
    proposed_vals: List[float] = []
    for pair in lookup.values():
        if baseline in pair and proposed in pair:
            baseline_vals.append(pair[baseline])
            proposed_vals.append(pair[proposed])

    return np.array(baseline_vals), np.array(proposed_vals), len(baseline_vals)


# ============================================================
# STATISTICAL TESTS
# ============================================================

def paired_t_test(group1: list, group2: list) -> Dict[str, Any]:
    """
    Perform a paired t-test between two groups.

    Parameters
    ----------
    group1 : list
        First sample of measurements.
    group2 : list
        Second sample of measurements.

    Returns
    -------
    dict
        Dictionary containing t_statistic, p_value, degrees_of_freedom,
        and a warning flag if sample size is too small.
    """
    a = np.array(group1, dtype=float)
    b = np.array(group2, dtype=float)

    if len(a) < 2 or len(b) < 2:
        return {
            "t_statistic": None,
            "p_value": None,
            "degrees_of_freedom": None,
            "warning": "Sample size too small for t-test (n < 2)",
        }

    if len(a) != len(b):
        return {
            "t_statistic": None,
            "p_value": None,
            "degrees_of_freedom": None,
            "warning": "Groups must have equal length for paired t-test",
        }

    t_stat, p_val = stats.ttest_rel(a, b)
    dof = len(a) - 1

    return {
        "t_statistic": float(t_stat),
        "p_value": float(p_val),
        "degrees_of_freedom": int(dof),
        "warning": None,
    }


def wilcoxon_signed_rank_test(group1: list, group2: list) -> Dict[str, Any]:
    """
    Perform a Wilcoxon signed-rank test (paired non-parametric).

    Parameters
    ----------
    group1 : list
        First sample.
    group2 : list
        Second sample.

    Returns
    -------
    dict
        Dictionary containing w_statistic, p_value, and warning flag.
    """
    a = np.array(group1, dtype=float)
    b = np.array(group2, dtype=float)

    if len(a) < 2 or len(b) < 2:
        return {
            "w_statistic": None,
            "p_value": None,
            "warning": "Sample size too small for Wilcoxon test (n < 2)",
        }

    if len(a) != len(b):
        return {
            "w_statistic": None,
            "p_value": None,
            "warning": "Groups must have equal length for Wilcoxon test",
        }

    try:
        w_stat, p_val = stats.wilcoxon(a, b, alternative="two-sided")
    except ValueError as e:
        return {
            "w_statistic": None,
            "p_value": None,
            "warning": f"Wilcoxon test failed: {e}",
        }

    return {
        "w_statistic": float(w_stat),
        "p_value": float(p_val),
        "warning": None,
    }


def mann_whitney_u_test(group1: list, group2: list) -> Dict[str, Any]:
    """
    Perform a Mann-Whitney U test (non-parametric alternative).

    Parameters
    ----------
    group1 : list
        First sample.
    group2 : list
        Second sample.

    Returns
    -------
    dict
        Dictionary containing u_statistic, p_value, and warning flag.
    """
    a = np.array(group1, dtype=float)
    b = np.array(group2, dtype=float)

    if len(a) < 2 or len(b) < 2:
        return {
            "u_statistic": None,
            "p_value": None,
            "warning": "Sample size too small for Mann-Whitney U test (n < 2)",
        }

    try:
        u_stat, p_val = stats.mannwhitneyu(a, b, alternative="two-sided")
    except ValueError as e:
        return {
            "u_statistic": None,
            "p_value": None,
            "warning": f"Mann-Whitney U test failed: {e}",
        }

    return {
        "u_statistic": float(u_stat),
        "p_value": float(p_val),
        "warning": None,
    }


def cohens_d(group1: list, group2: list) -> Dict[str, Any]:
    """
    Calculate Cohen's d effect size.

    Parameters
    ----------
    group1 : list
        First sample.
    group2 : list
        Second sample.

    Returns
    -------
    dict
        Dictionary containing cohens_d and interpretation label.
    """
    a = np.array(group1, dtype=float)
    b = np.array(group2, dtype=float)

    n1, n2 = len(a), len(b)
    if n1 < 2 or n2 < 2:
        return {
            "cohens_d": None,
            "interpretation": "insufficient data",
            "warning": "Sample size too small for Cohen's d (n < 2)",
        }

    mean1, mean2 = np.mean(a), np.mean(b)
    var1, var2 = np.var(a, ddof=1), np.var(b, ddof=1)

    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    if pooled_std == 0:
        return {
            "cohens_d": 0.0 if mean1 == mean2 else float("inf"),
            "interpretation": "undefined (zero variance)",
            "warning": None,
        }

    d = (mean1 - mean2) / pooled_std
    abs_d = abs(d)

    if abs_d < 0.2:
        interpretation = "negligible"
    elif abs_d < 0.5:
        interpretation = "small"
    elif abs_d < 0.8:
        interpretation = "medium"
    else:
        interpretation = "large"

    return {
        "cohens_d": float(d),
        "interpretation": interpretation,
        "warning": None,
    }


def confidence_interval(
    group1: list,
    group2: list,
    confidence: float = 0.95,
) -> Dict[str, Any]:
    """
    Compute confidence interval for the mean difference of paired samples.

    Parameters
    ----------
    group1 : list
        First sample.
    group2 : list
        Second sample.
    confidence : float
        Confidence level (default 0.95).

    Returns
    -------
    dict
        Dictionary containing mean_difference, ci_lower, ci_upper, and warning.
    """
    a = np.array(group1, dtype=float)
    b = np.array(group2, dtype=float)

    if len(a) < 2 or len(b) < 2:
        return {
            "mean_difference": None,
            "ci_lower": None,
            "ci_upper": None,
            "warning": "Sample size too small for confidence interval (n < 2)",
        }

    if len(a) != len(b):
        return {
            "mean_difference": None,
            "ci_lower": None,
            "ci_upper": None,
            "warning": "Groups must have equal length for paired CI",
        }

    differences = a - b
    mean_diff = np.mean(differences)
    std_err = stats.sem(differences)
    if std_err == 0:
        return {
            "mean_difference": float(mean_diff),
            "ci_lower": float(mean_diff),
            "ci_upper": float(mean_diff),
            "warning": "Zero standard error; CI collapsed to point estimate",
        }

    alpha = 1.0 - confidence
    dof = len(differences) - 1
    ci = stats.t.interval(alpha / 2.0, dof, loc=mean_diff, scale=std_err)

    return {
        "mean_difference": float(mean_diff),
        "ci_lower": float(ci[0]),
        "ci_upper": float(ci[1]),
        "warning": None,
    }


# ============================================================
# MULTIPLE COMPARISON CORRECTION
# ============================================================

def benjamini_hochberg_correction(p_values: list) -> List[float]:
    """
    Apply Benjamini-Hochberg FDR correction to a list of p-values.

    Parameters
    ----------
    p_values : list
        List of raw p-values.

    Returns
    -------
    list
        Adjusted p-values (FDR-controlled).
    """
    n = len(p_values)
    if n == 0:
        return []

    sorted_p = sorted([(p, i) for i, p in enumerate(p_values)], key=lambda x: x[0])
    adjusted = []
    for rank, (p, original_idx) in enumerate(sorted_p, start=1):
        adjusted_p = p * n / rank
        adjusted.append((adjusted_p, original_idx))

    # Ensure monotonicity
    adjusted_sorted = sorted(adjusted, key=lambda x: x[0])
    monotonic = []
    prev = 1.0
    for adj_p, idx in adjusted_sorted:
        if adj_p > prev:
            adj_p = prev
        else:
            prev = adj_p
        monotonic.append((adj_p, idx))

    # Reorder to original order
    result = [0.0] * n
    for adj_p, idx in monotonic:
        result[idx] = min(adj_p, 1.0)

    return result


# ============================================================
# PAIRED COMPARISON
# ============================================================

def paired_comparison(
    raw_results: list,
    metric: str,
    baseline: str,
    proposed: str,
) -> Dict[str, Any]:
    """
    Perform a paired comparison between two strategies.

    Pairs are constructed on (seed, number_of_users).

    Parameters
    ----------
    raw_results : list
        Raw result dictionaries.
    metric : str
        Metric to compare.
    baseline : str
        Baseline strategy name.
    proposed : str
        Proposed strategy name.

    Returns
    -------
    dict
        Comparison results.
    """
    baseline_vals, proposed_vals, n_pairs = build_paired_groups(
        raw_results, metric, baseline, proposed
    )

    if n_pairs == 0:
        return {
            "baseline": baseline,
            "proposed": proposed,
            "metric": metric,
            "sample_size": 0,
            "warning": "No paired observations found",
        }

    baseline_list = baseline_vals.tolist()
    proposed_list = proposed_vals.tolist()

    t_result = paired_t_test(baseline_list, proposed_list)
    w_result = wilcoxon_signed_rank_test(baseline_list, proposed_list)
    d_result = cohens_d(baseline_list, proposed_list)
    ci_result = confidence_interval(baseline_list, proposed_list)

    return {
        "baseline": baseline,
        "proposed": proposed,
        "metric": metric,
        "sample_size": n_pairs,
        "baseline_mean": float(np.mean(baseline_vals)),
        "proposed_mean": float(np.mean(proposed_vals)),
        "mean_difference": float(np.mean(baseline_vals - proposed_vals)),
        "paired_t_test": t_result,
        "wilcoxon_signed_rank": w_result,
        "cohens_d": d_result,
        "confidence_interval": ci_result,
        "warning": (
            t_result.get("warning")
            or w_result.get("warning")
            or d_result.get("warning")
            or ci_result.get("warning")
        ),
    }


# ============================================================
# FULL PAIRWISE COMPARISON RUNNER
# ============================================================

def run_all_pairwise_comparisons(
    raw_results: list,
    proposed: str = "game_theory",
    baselines: Optional[list] = None,
    metrics: Optional[list] = None,
) -> list:
    """
    Run all pairwise comparisons between the proposed strategy
    and each baseline for each metric.

    Parameters
    ----------
    raw_results : list
        Raw result dictionaries.
    proposed : str
        Proposed strategy name.
    baselines : list, optional
        List of baseline strategy names.
    metrics : list, optional
        List of metric names to compare.

    Returns
    -------
    list
        List of comparison result dictionaries.
    """
    if baselines is None:
        baselines = [
            "equal",
            "proportional",
            "priority",
            "max_min_fairness",
            "alpha_fair",
        ]
    if metrics is None:
        metrics = [
            "average_utility",
            "jain_fairness_index",
            "utilization_percentage",
            "computational_time",
        ]

    results = []
    p_values = []

    for baseline in baselines:
        for metric in metrics:
            result = paired_comparison(raw_results, metric, baseline, proposed)
            results.append(result)
            if result.get("paired_t_test") and result["paired_t_test"].get("p_value") is not None:
                p_values.append(result["paired_t_test"]["p_value"])
            else:
                p_values.append(1.0)

    adjusted = benjamini_hochberg_correction(p_values)
    for result, adj_p in zip(results, adjusted):
        result["adjusted_p_value"] = adj_p
        raw_p = result.get("paired_t_test", {}).get("p_value")
        if raw_p is not None:
            if adj_p < 0.05:
                result["significance"] = "significant (FDR-adjusted)"
            elif raw_p < 0.05:
                result["significance"] = "significant (raw) but not after FDR"
            else:
                result["significance"] = "not significant"
        else:
            result["significance"] = "not computable"

    return results


# ============================================================
# NASH CONVERGENCE STATISTICS
# ============================================================

def calculate_nash_statistics(raw_results: list) -> Dict[str, Any]:
    """
    Calculate Nash convergence statistics from raw results.

    Parameters
    ----------
    raw_results : list
        Raw result dictionaries.

    Returns
    -------
    dict
        Nash convergence statistics.
    """
    gt_rows = [
        r for r in raw_results
        if r.get("strategy") == "game_theory"
        and r.get("convergence_iterations") not in (None, "")
    ]

    if not gt_rows:
        return {
            "total_runs": 0,
            "convergence_rate": None,
            "nash_verification_rate": None,
            "mean_iterations": None,
            "median_iterations": None,
            "min_iterations": None,
            "max_iterations": None,
            "by_user_count": {},
        }

    iterations = []
    for r in gt_rows:
        try:
            iterations.append(int(r["convergence_iterations"]))
        except (TypeError, ValueError):
            continue
    converged = [bool(r.get("converged")) for r in gt_rows]
    is_nash = [bool(r.get("is_nash_equilibrium")) for r in gt_rows]

    total = len(gt_rows)
    convergence_rate = sum(converged) / total if total > 0 else None
    nash_rate = sum(is_nash) / total if total > 0 else None

    by_user_count: Dict[int, Dict[str, Any]] = {}
    for r in gt_rows:
        n = int(r["number_of_users"])
        by_user_count.setdefault(n, {
            "total": 0,
            "converged": 0,
            "is_nash": 0,
            "iterations": [],
        })
        entry = by_user_count[n]
        entry["total"] += 1
        if bool(r.get("converged")):
            entry["converged"] += 1
        if bool(r.get("is_nash_equilibrium")):
            entry["is_nash"] += 1
        entry["iterations"].append(int(r["convergence_iterations"]))

    for n, entry in by_user_count.items():
        iters = entry["iterations"]
        entry["mean_iterations"] = float(np.mean(iters))
        entry["median_iterations"] = float(np.median(iters))
        entry["min_iterations"] = int(np.min(iters))
        entry["max_iterations"] = int(np.max(iters))
        entry["convergence_rate"] = entry["converged"] / entry["total"]
        entry["nash_rate"] = entry["is_nash"] / entry["total"]

    return {
        "total_runs": total,
        "convergence_rate": convergence_rate,
        "nash_verification_rate": nash_rate,
        "mean_iterations": float(np.mean(iterations)),
        "median_iterations": float(np.median(iterations)),
        "min_iterations": int(np.min(iterations)),
        "max_iterations": int(np.max(iterations)),
        "by_user_count": by_user_count,
    }


# ============================================================
# OUTPUT GENERATION
# ============================================================

def save_statistical_results(
    comparisons: list,
    nash_stats: Dict[str, Any],
    output_directory: str = "data",
) -> Dict[str, str]:
    """
    Save statistical results to CSV and JSON.

    Parameters
    ----------
    comparisons : list
        List of comparison result dictionaries.
    nash_stats : dict
        Nash convergence statistics.
    output_directory : str
        Output directory path.

    Returns
    -------
    dict
        Paths to created files.
    """
    os.makedirs(output_directory, exist_ok=True)

    csv_path = os.path.join(output_directory, "statistical_results.csv")
    json_path = os.path.join(output_directory, "statistical_results.json")

    fieldnames = [
        "metric",
        "algorithm_a",
        "algorithm_b",
        "sample_size",
        "mean_a",
        "mean_b",
        "mean_difference",
        "test_name",
        "statistic",
        "p_value",
        "adjusted_p_value",
        "confidence_interval_lower",
        "confidence_interval_upper",
        "effect_size",
        "effect_size_interpretation",
        "significance",
    ]

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for result in comparisons:
            t_test = result.get("paired_t_test", {})
            wilcoxon = result.get("wilcoxon_signed_rank", {})
            cohens = result.get("cohens_d", {})
            ci = result.get("confidence_interval", {})

            row = {
                "metric": result.get("metric"),
                "algorithm_a": result.get("baseline"),
                "algorithm_b": result.get("proposed"),
                "sample_size": result.get("sample_size"),
                "mean_a": result.get("baseline_mean"),
                "mean_b": result.get("proposed_mean"),
                "mean_difference": result.get("mean_difference"),
                "test_name": "paired_t_test",
                "statistic": t_test.get("t_statistic") if t_test else None,
                "p_value": t_test.get("p_value") if t_test else None,
                "adjusted_p_value": result.get("adjusted_p_value"),
                "confidence_interval_lower": ci.get("ci_lower") if ci else None,
                "confidence_interval_upper": ci.get("ci_upper") if ci else None,
                "effect_size": cohens.get("cohens_d") if cohens else None,
                "effect_size_interpretation": cohens.get("interpretation") if cohens else None,
                "significance": result.get("significance"),
            }
            writer.writerow(row)

    output = {
        "comparisons": comparisons,
        "nash_statistics": nash_stats,
        "metadata": {
            "total_comparisons": len(comparisons),
            "correction_method": "Benjamini-Hochberg FDR",
            "note": (
                "Paired comparisons are constructed on (seed, number_of_users). "
                "Each observation represents one experimental repetition for a given user count."
            ),
        },
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=str)

    return {
        "csv": csv_path,
        "json": json_path,
    }


# ============================================================
# BACKWARD COMPATIBILITY
# ============================================================

def compare_strategies(
    raw_results: list,
    metric: str,
    baseline: str,
    proposed: str,
) -> Dict[str, Any]:
    """
    Compare two strategies using appropriate statistical tests.

    .. deprecated::
        Use :func:`paired_comparison` or :func:`run_all_pairwise_comparisons`
        for properly paired analyses.

    Parameters
    ----------
    raw_results : list
        List of raw result dictionaries (one per repetition).
    metric : str
        Metric to compare (e.g., "average_utility", "jain_fairness_index").
    baseline : str
        Name of the baseline strategy.
    proposed : str
        Name of the proposed strategy.

    Returns
    -------
    dict
        Comparison results including t-test, Mann-Whitney U, and Cohen's d.
    """
    baseline_vals = [
        r[metric] for r in raw_results
        if r.get("strategy") == baseline and metric in r
    ]
    proposed_vals = [
        r[metric] for r in raw_results
        if r.get("strategy") == proposed and metric in r
    ]

    if len(baseline_vals) < 5 or len(proposed_vals) < 5:
        warning_msg = (
            f"Sample size too small for reliable inference "
            f"(baseline n={len(baseline_vals)}, proposed n={len(proposed_vals)})"
        )
        warnings.warn(warning_msg)

    t_result = paired_t_test(baseline_vals, proposed_vals)
    u_result = mann_whitney_u_test(baseline_vals, proposed_vals)
    d_result = cohens_d(baseline_vals, proposed_vals)

    return {
        "baseline": baseline,
        "proposed": proposed,
        "metric": metric,
        "baseline_n": len(baseline_vals),
        "proposed_n": len(proposed_vals),
        "baseline_mean": float(np.mean(baseline_vals)) if baseline_vals else None,
        "proposed_mean": float(np.mean(proposed_vals)) if proposed_vals else None,
        "paired_t_test": t_result,
        "mann_whitney_u": u_result,
        "cohens_d": d_result,
        "warning": t_result.get("warning") or u_result.get("warning") or d_result.get("warning"),
    }