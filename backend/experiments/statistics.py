"""
Statistical Tests for Experiment Comparison

Implements paired t-test, Mann-Whitney U test, Cohen's d, and
strategy comparison helpers for evaluating allocation algorithms.
"""

import warnings
from typing import Optional, Dict, Any

import numpy as np
from scipy import stats


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


def compare_strategies(
    raw_results: list,
    metric: str,
    baseline: str,
    proposed: str,
) -> Dict[str, Any]:
    """
    Compare two strategies using appropriate statistical tests.

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
