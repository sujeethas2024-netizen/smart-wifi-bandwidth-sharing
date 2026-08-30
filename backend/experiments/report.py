"""
Research Report Generation

Builds a comprehensive Markdown research report (data/research_report.md)
from the artifacts produced by the multi-seed runner, ablation study, and
sensitivity analysis.

If the experiments have not been run yet, every data-dependent section is
clearly marked as ``PENDING`` so the document remains valid and complete.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

import pandas as pd

from backend.experiments.config_schema import ExperimentConfig
from backend.experiments.statistics import compare_strategies
from backend.data_provenance import (
    SIMULATION,
    CALCULATED_FROM_REAL_DATA,
    REAL_DATASET,
    REAL_RUNTIME_MEASUREMENT,
    USER_INPUT,
)


# ============================================================
# PENDING MARKER
# ============================================================

PENDING = "PENDING — run experiments to generate data"

BASELINE_STRATEGY = "equal"
PROPOSED_STRATEGY = "game_theory"
COMPARISON_METRICS = ["average_utility", "jain_fairness_index", "utilization_percentage"]


# ============================================================
# LOAD ARTIFACTS
# ============================================================

def _load_csv(output_directory: str, filename: str) -> Optional[pd.DataFrame]:
    """Load a CSV artifact if it exists, else return None."""
    path = os.path.join(output_directory, filename)
    if not os.path.exists(path):
        return None
    return pd.read_csv(path)


def _load_json(output_directory: str, filename: str) -> Optional[dict]:
    """Load a JSON artifact if it exists, else return None."""
    path = os.path.join(output_directory, filename)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================
# SECTION BUILDERS
# ============================================================

def _section_configuration(config: dict) -> str:
    """Build the experimental configuration section."""
    if config is None:
        return f"{PENDING}\n"

    lines = [
        f"- Random seed (base): `{config.get('seed')}`",
        f"- Repetitions: `{config.get('repetitions')}`",
        f"- User counts: `{config.get('user_counts')}`",
        f"- Algorithms: `{config.get('algorithms')}`",
        f"- Total bandwidth: `{config.get('total_bandwidth')}` Mbps",
        f"- Scenario: `{config.get('scenario')}`",
        f"- Alpha (alpha-fair): `{config.get('alpha')}`",
        f"- Max iterations (game theory): `{config.get('max_iterations')}`",
        f"- Utility weights: `{config.get('utility_weights')}`",
        f"- Traffic class distribution: `{config.get('traffic_class_distribution')}`",
    ]
    return "\n".join(lines) + "\n"


def _md_table(df: pd.DataFrame) -> str:
    """Render a DataFrame as a Markdown table (no external dependency)."""
    if df is None or df.empty:
        return "(no data)"
    cols = list(df.columns)
    header = "| " + " | ".join(str(c) for c in cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    rows = []
    for _, row in df.iterrows():
        rows.append(
            "| " + " | ".join(str(row[c]) for c in cols) + " |"
        )
    return "\n".join([header, sep] + rows)


def _md_series(series: pd.Series, index_name: str, value_name: str) -> str:
    """Render a Series as a two-column Markdown table."""
    df = series.reset_index()
    df.columns = [index_name, value_name]
    return _md_table(df)


def _section_raw_results(raw_df: pd.DataFrame) -> str:
    """Build the raw results summary section."""
    if raw_df is None or raw_df.empty:
        return f"{PENDING}\n"

    lines = [
        f"Total raw repetitions: `{len(raw_df)}`",
        "",
        "Sample of raw results (first 10 rows):",
        "",
        _md_table(raw_df.head(10)),
        "",
    ]
    return "\n".join(lines) + "\n"


def _section_aggregated(agg_df: pd.DataFrame) -> str:
    """Build the aggregated statistics tables section."""
    if agg_df is None or agg_df.empty:
        return f"{PENDING}\n"

    lines = [
        f"Total aggregated groups: `{len(agg_df)}`",
        "",
        _md_table(agg_df),
        "",
    ]
    return "\n".join(lines) + "\n"


def _section_significance(raw_df: pd.DataFrame) -> str:
    """Build the statistical significance section."""
    if raw_df is None or raw_df.empty:
        return f"{PENDING}\n"

    lines = []
    for metric in COMPARISON_METRICS:
        comparison = compare_strategies(
            raw_df.to_dict("records"),
            metric=metric,
            baseline=BASELINE_STRATEGY,
            proposed=PROPOSED_STRATEGY,
        )
        t = comparison["paired_t_test"]
        d = comparison["cohens_d"]
        lines.append(f"### Metric: `{metric}`")
        lines.append("")
        lines.append(
            f"- Baseline (`{BASELINE_STRATEGY}`) mean: "
            f"`{comparison['baseline_mean']}` (n={comparison['baseline_n']})"
        )
        lines.append(
            f"- Proposed (`{PROPOSED_STRATEGY}`) mean: "
            f"`{comparison['proposed_mean']}` (n={comparison['proposed_n']})"
        )
        lines.append(
            f"- Paired t-test: t=`{t.get('t_statistic')}`, "
            f"p=`{t.get('p_value')}`, dof=`{t.get('degrees_of_freedom')}`"
        )
        lines.append(
            f"- Cohen's d: `{d.get('cohens_d')}` "
            f"({d.get('interpretation')})"
        )
        if comparison.get("warning"):
            lines.append(f"- Warning: {comparison['warning']}")
        lines.append("")

    return "\n".join(lines) + "\n"


def _section_baseline_comparison(agg_df: pd.DataFrame) -> str:
    """Build the baseline comparison tables section."""
    if agg_df is None or agg_df.empty:
        return f"{PENDING}\n"

    lines = ["Comparison of proposed strategy against the equal-allocation baseline."]
    try:
        pivot = agg_df.pivot(
            index="number_of_users",
            columns="strategy",
            values="average_utility_mean",
        )
        if BASELINE_STRATEGY in pivot.columns and PROPOSED_STRATEGY in pivot.columns:
            pivot = pivot[[BASELINE_STRATEGY, PROPOSED_STRATEGY]]
        lines.append("")
        lines.append(_md_table(pivot))
        lines.append("")
    except Exception as exc:  # pragma: no cover - defensive
        lines.append(f"{PENDING} (pivot failed: {exc})")
        lines.append("")

    return "\n".join(lines) + "\n"


def _section_scalability(agg_df: pd.DataFrame) -> str:
    """Build the scalability analysis section."""
    if agg_df is None or agg_df.empty:
        return f"{PENDING}\n"

    lines = [
        "Computational time vs number of users (mean across algorithms):",
        "",
    ]
    if "computational_time_mean" in agg_df.columns:
        grp = agg_df.groupby("number_of_users")["computational_time_mean"].mean()
        lines.append(_md_series(grp, "number_of_users", "computational_time_mean"))
    else:
        # computational_time lives in raw results; describe qualitatively.
        lines.append(
            "Computational time is recorded per repetition in `raw_results.csv`. "
            "Aggregate `computational_time_mean` by re-running with the runner to "
            "populate this table."
        )
    lines.append("")
    return "\n".join(lines) + "\n"


def _section_sensitivity(sens_df: pd.DataFrame) -> str:
    """Build the sensitivity analysis section."""
    if sens_df is None or sens_df.empty:
        return f"{PENDING}\n"

    lines = []
    for parameter in sorted(sens_df["parameter"].unique()):
        sub = sens_df[sens_df["parameter"] == parameter]
        lines.append(f"### Parameter: `{parameter}`")
        lines.append("")
        lines.append(_md_table(sub))
        lines.append("")
    return "\n".join(lines) + "\n"


def _section_ablation(ablation_json: Optional[dict]) -> str:
    """Build the ablation study section."""
    if ablation_json is None:
        return f"{PENDING}\n"

    impact = ablation_json.get("impact", {})
    if not impact:
        return f"{PENDING} (no ablation impact data available)\n"

    lines = ["Mean delta (full model - ablated) per component:"]
    lines.append("")
    for component, deltas in impact.items():
        lines.append(f"### Component removed: `{component}`")
        lines.append("")
        for metric, delta in deltas.items():
            lines.append(f"- `{metric}`: `{delta}`")
        lines.append("")

    return "\n".join(lines) + "\n"


def _section_plots(raw_df: pd.DataFrame, sens_df: pd.DataFrame, ablation_json: dict) -> str:
    """Build the generated-plots inventory section."""
    lines = [
        "Plots are generated from the CSV artifacts. When experiments have not "
        "been run, the artifacts are absent and plotting is skipped.",
        "",
        "- `fairness_by_users.png` — Jain fairness index vs number of users "
        "(one line per algorithm) from `aggregated_results.csv`.",
    ]
    if raw_df is not None and not raw_df.empty:
        lines.append(
            "- `utility_distribution.png` — distribution of average utility "
            "across repetitions from `raw_results.csv`."
        )
    lines.append(
        "- `computational_time.png` — mean computational time vs number of users "
        "from `aggregated_results.csv`."
    )
    if sens_df is not None and not sens_df.empty:
        lines.append(
            "- `sensitivity_<parameter>.png` — fairness/utility/utilization vs "
            "weight value from `sensitivity_results.csv`."
        )
    if ablation_json is not None and ablation_json.get("impact"):
        lines.append(
            "- `ablation_impact.png` — component impact bars from "
            "`ablation_results.csv`."
        )
    lines.append("")
    return "\n".join(lines) + "\n"


def _section_reproducibility(config: dict) -> str:
    """Build the reproducibility instructions section."""
    seed = config.get("seed") if config else 42
    lines = [
        "1. Set the working directory to the repository root (so `data/` resolves).",
        "2. Install dependencies: `pip install -r requirements.txt`.",
        "3. Run the multi-seed experiment:",
        "",
        "```python",
        "from backend.experiments.config_schema import ExperimentConfig",
        "from backend.experiments.runner import run_multi_seed_experiment",
        "",
        f"config = ExperimentConfig.from_dict({config if config else {'seed': seed}})",
        "run_multi_seed_experiment(config)",
        "```",
        "",
        "4. Run the ablation study:",
        "",
        "```python",
        "from backend.experiments.ablation import run_ablation",
        "run_ablation(config)",
        "```",
        "",
        "5. Run a sensitivity analysis:",
        "",
        "```python",
        "from backend.experiments.sensitivity import run_sensitivity_analysis",
        "run_sensitivity_analysis(config, 'w_throughput', [0.5, 1.0, 1.5, 2.0])",
        "```",
        "",
        "6. Generate this report:",
        "",
        "```python",
        "from backend.experiments.report import generate_report",
        "generate_report()",
        "```",
        "",
        "All randomness is seeded; identical seeds reproduce identical results.",
        "",
    ]
    return "\n".join(lines) + "\n"


# ============================================================
# BUILD REPORT
# ============================================================

def build_report_markdown(output_directory: str = "data") -> str:
    """
    Build the Markdown research report string.

    Parameters
    ----------
    output_directory : str
        Directory containing experiment artifacts.

    Returns
    -------
    str
        Markdown content of the research report.
    """
    raw_df = _load_csv(output_directory, "raw_results.csv")
    agg_df = _load_csv(output_directory, "aggregated_results.csv")
    sens_df = _load_csv(output_directory, "sensitivity_results.csv")
    config = _load_json(output_directory, "experiment_config.json")
    ablation_json = _load_json(output_directory, "ablation_results.json")

    timestamp = datetime.utcnow().isoformat()
    has_data = raw_df is not None and not raw_df.empty

    sections = []

    # Title
    sections.append("# Smart WiFi Bandwidth Sharing — Research Report\n")
    sections.append(f"*Generated: {timestamp} (UTC)*\n")

    # Provenance metadata
    sections.append("## Provenance Metadata\n")
    sections.append(
        "All metrics are labeled according to the project's data provenance model:\n"
    )
    sections.append(f"- {SIMULATION}: synthetic traffic scenarios (user demand).")
    sections.append(
        f"- {CALCULATED_FROM_REAL_DATA}: allocation + metrics (deterministic)."
    )
    sections.append(f"- {REAL_DATASET}: not used in simulation experiments.")
    sections.append(
        f"- {REAL_RUNTIME_MEASUREMENT}: not used (simulation environment)."
    )
    sections.append(f"- {USER_INPUT}: not used.\n")

    # Configuration
    sections.append("## 1. Experimental Configuration\n")
    sections.append(_section_configuration(config))

    # Raw results
    sections.append("## 2. Raw Results Summary\n")
    sections.append(_section_raw_results(raw_df))

    # Aggregated
    sections.append("## 3. Aggregated Statistics\n")
    sections.append(_section_aggregated(agg_df))

    # Significance
    sections.append("## 4. Statistical Significance Tests\n")
    sections.append(_section_significance(raw_df) if has_data else f"{PENDING}\n")

    # Baseline comparison
    sections.append("## 5. Baseline Comparison\n")
    sections.append(_section_baseline_comparison(agg_df))

    # Scalability
    sections.append("## 6. Scalability Analysis\n")
    sections.append(_section_scalability(agg_df))

    # Sensitivity
    sections.append("## 7. Sensitivity Analysis\n")
    sections.append(_section_sensitivity(sens_df))

    # Ablation
    sections.append("## 8. Ablation Study\n")
    sections.append(_section_ablation(ablation_json))

    # Plots
    sections.append("## 9. Generated Plots\n")
    sections.append(_section_plots(raw_df, sens_df, ablation_json))

    # Reproducibility
    sections.append("## 10. Reproducibility Instructions\n")
    sections.append(_section_reproducibility(config))

    return "\n".join(sections)


# ============================================================
# GENERATE REPORT (PUBLIC)
# ============================================================

def generate_report(
    config: ExperimentConfig = None,
    output_directory: str = None,
) -> Dict[str, Any]:
    """
    Generate the research report and write it to data/research_report.md.

    The report works even when no experiments have been run: every data
    dependent section is clearly marked as PENDING.

    Parameters
    ----------
    config : ExperimentConfig or None
        Optional configuration (used to choose the output directory).
    output_directory : str or None
        Explicit output directory. Takes precedence over ``config``.

    Returns
    -------
    dict
        Dictionary with the markdown content and provenance metadata.
    """
    if output_directory is None:
        output_directory = config.output_directory if config else "data"
    os.makedirs(output_directory, exist_ok=True)

    markdown = build_report_markdown(output_directory)

    report_path = os.path.join(output_directory, "research_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    return {
        "status": "success",
        "report_path": report_path,
        "markdown": markdown,
        "provenance": {
            "user_demand": SIMULATION,
            "allocation": CALCULATED_FROM_REAL_DATA,
            "metrics": CALCULATED_FROM_REAL_DATA,
            "note": (
                "Report is generated from experiment artifacts. Sections without "
                "data are marked PENDING."
            ),
        },
    }
