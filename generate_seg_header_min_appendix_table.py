"""Generate the appendix LaTeX table for the segment-header-minimum experiment.

This script is a restricted version of the overall-results table generator. It
prints only the corrected-value configuration phi_S and the header-augmented
configuration phi_A. Bold values are computed only within this restricted
appendix comparison.

The dagger logic is unchanged: a dagger marks the better value when a
duplicate/no-duplicate pair differs significantly.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


DEFAULT_RESULTS_DIR = Path("results")
DEFAULT_ALPHA = 0.05
DEFAULT_OUTPUT_FILE_NAME = "seg_header_min_exp_ad_table.tex"
MISSING_VALUE = "---"
DAGGER = r"$^{\dagger}$"

DATASETS: list[tuple[str, str]] = [
    ("cicids2017_merged", r"\cicids"),
    ("insdn_hhuang_fix", r"\insdn"),
]

APPENDIX_CONFIG_GROUPS: list[tuple[str, str, str, str]] = [
    (
        "S",
        "engelen_corrected_values_no_duplicates",
        "engelen_corrected_values_with_duplicates",
        r"$\varphi_{S}$",
    ),
    (
        "A",
        "engelen_corrected_values_no_duplicates_with_seg_header_min",
        "engelen_corrected_values_with_duplicates_with_seg_header_min",
        (
            r"\makecell[c]{"
            r"$\varphi_{S}$ + \\ "
            r"\featurename{Fwd/Bwd} \\ "
            r"\featurename{Segment} \\ "
            r"\featurename{Header} \\ "
            r"\featurename{Length Min}"
            r"}"
        ),
    ),
]

APPENDIX_CONFIG_NAMES: set[str] = {
    config_name
    for _, no_duplicate_config, duplicate_config, _ in APPENDIX_CONFIG_GROUPS
    for config_name in (no_duplicate_config, duplicate_config)
}

METRICS: list[tuple[str, str]] = [
    ("accuracy", "Accuracy"),
    ("tpr", "TPR"),
    ("fpr", "FPR"),
    ("f1", "F1"),
    ("roc_auc", "ROC-AUC"),
]

P_VALUE_COLUMNS = [
    "pvalue",
    "p_value",
    "p-value",
    "p.val",
    "p_val",
    "p",
    "adjusted_pvalue",
    "adjusted_p_value",
    "pvalue_adjusted",
    "p_value_adjusted",
    "p_adjusted",
    "p_adj",
]

DatasetResults = tuple[pd.DataFrame, dict[str, set[str]], dict[str, set[str]]]
ResultsCache = dict[str, DatasetResults]


def parse_args() -> argparse.Namespace:
    """Read command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate the appendix segment-header-minimum results table."
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=DEFAULT_RESULTS_DIR,
        help="Directory containing one subdirectory per dataset. Default: results.",
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=DEFAULT_ALPHA,
        help="P-value threshold. Default: 0.05.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=(
            "Output .tex path. Default: "
            "results/seg_header_min_exp_ad_table.tex."
        ),
    )
    return parser.parse_args()


def read_dataset_results(
    results_dir: Path,
    dataset_folder: str,
    alpha: float,
) -> DatasetResults:
    """Read one dataset and compute appendix-local bold/dagger annotations."""
    metrics_path = results_dir / dataset_folder / "overall_metrics_summary.csv"
    ttest_path = results_dir / dataset_folder / "ttest_results.csv"

    metrics_table = pd.read_csv(metrics_path)
    ttest_table = pd.read_csv(ttest_path)

    appendix_metrics_table = restrict_metrics_to_appendix_configs(metrics_table)
    appendix_ttest_table = restrict_ttests_to_appendix_configs(ttest_table)

    bold_configs_by_metric = find_bold_configs_by_metric(
        appendix_metrics_table,
        appendix_ttest_table,
    )
    dagger_configs_by_metric = find_dagger_configs_by_metric(
        appendix_metrics_table,
        appendix_ttest_table,
        alpha,
    )

    return appendix_metrics_table, bold_configs_by_metric, dagger_configs_by_metric


def restrict_metrics_to_appendix_configs(metrics_table: pd.DataFrame) -> pd.DataFrame:
    """Keep only the configurations printed in the appendix table."""
    return metrics_table[metrics_table["config"].isin(APPENDIX_CONFIG_NAMES)].copy()


def restrict_ttests_to_appendix_configs(ttest_table: pd.DataFrame) -> pd.DataFrame:
    """Keep only pairwise tests where both configs are in the appendix table."""
    return ttest_table[
        ttest_table["config1"].isin(APPENDIX_CONFIG_NAMES)
        & ttest_table["config2"].isin(APPENDIX_CONFIG_NAMES)
    ].copy()


def find_bold_configs_by_metric(
    metrics_table: pd.DataFrame,
    ttest_table: pd.DataFrame,
) -> dict[str, set[str]]:
    """Find configs that should be printed in bold.

    The best appendix config is bolded. Any appendix config that is not
    statistically different from that best appendix config is also bolded.
    """
    bold_configs_by_metric: dict[str, set[str]] = {}

    for metric_name in metrics_table["metric"].unique():
        metric_rows = metrics_table[metrics_table["metric"] == metric_name]
        best_config = find_best_config(metric_rows, metric_name)

        bold_configs = {best_config}
        metric_ttests = ttest_table[ttest_table["metric"] == metric_name]

        for _, ttest_row in metric_ttests.iterrows():
            compared_configs = {ttest_row["config1"], ttest_row["config2"]}

            if best_config not in compared_configs:
                continue

            if is_false_like(ttest_row["significant"]):
                other_config = ttest_row["config2"]
                if ttest_row["config1"] != best_config:
                    other_config = ttest_row["config1"]
                bold_configs.add(other_config)

        bold_configs_by_metric[metric_name] = bold_configs

    return bold_configs_by_metric


def find_dagger_configs_by_metric(
    metrics_table: pd.DataFrame,
    ttest_table: pd.DataFrame,
    alpha: float,
) -> dict[str, set[str]]:
    """Find duplicate/no-duplicate winners that should receive a dagger."""
    dagger_configs_by_metric: dict[str, set[str]] = {}

    for metric_name in metrics_table["metric"].unique():
        dagger_configs_by_metric[metric_name] = set()

        for _, no_duplicate_config, duplicate_config, _ in APPENDIX_CONFIG_GROUPS:
            ttest_row = find_ttest_row(
                ttest_table,
                metric_name,
                duplicate_config,
                no_duplicate_config,
            )

            if ttest_row is None:
                continue

            if not is_statistically_significant(ttest_row, alpha):
                continue

            better_config = find_better_config_between_two(
                metrics_table,
                metric_name,
                duplicate_config,
                no_duplicate_config,
            )

            if better_config is not None:
                dagger_configs_by_metric[metric_name].add(better_config)

    return dagger_configs_by_metric


def find_best_config(metric_rows: pd.DataFrame, metric_name: str) -> str:
    """Return the best config for a metric."""
    if metric_rows.empty:
        raise ValueError(f"No rows found for metric: {metric_name}")

    if metric_name == "fpr":
        best_row_index = metric_rows["mean"].idxmin()
    else:
        best_row_index = metric_rows["mean"].idxmax()

    return str(metric_rows.loc[best_row_index, "config"])


def find_better_config_between_two(
    metrics_table: pd.DataFrame,
    metric_name: str,
    first_config: str,
    second_config: str,
) -> str | None:
    """Return the better config between two configs for one metric."""
    first_mean = find_metric_mean(metrics_table, first_config, metric_name)
    second_mean = find_metric_mean(metrics_table, second_config, metric_name)

    if first_mean is None or second_mean is None:
        return None

    if first_mean == second_mean:
        return None

    if metric_name == "fpr":
        if first_mean < second_mean:
            return first_config
        return second_config

    if first_mean > second_mean:
        return first_config
    return second_config


def find_metric_mean(
    metrics_table: pd.DataFrame,
    config_name: str,
    metric_name: str,
) -> float | None:
    """Read the mean value for one config/metric pair."""
    matching_rows = metrics_table[
        (metrics_table["config"] == config_name)
        & (metrics_table["metric"] == metric_name)
    ]

    if matching_rows.empty:
        return None

    return float(matching_rows.iloc[0]["mean"])


def find_ttest_row(
    ttest_table: pd.DataFrame,
    metric_name: str,
    first_config: str,
    second_config: str,
) -> pd.Series | None:
    """Find the statistical-test row comparing two configs."""
    matching_rows = ttest_table[
        (ttest_table["metric"] == metric_name)
        & (
            (
                (ttest_table["config1"] == first_config)
                & (ttest_table["config2"] == second_config)
            )
            | (
                (ttest_table["config1"] == second_config)
                & (ttest_table["config2"] == first_config)
            )
        )
    ]

    if matching_rows.empty:
        return None

    return matching_rows.iloc[0]


def is_statistically_significant(ttest_row: pd.Series, alpha: float) -> bool:
    """Return True when a statistical-test row is significant."""
    p_value = find_p_value(ttest_row)

    if p_value is not None:
        return p_value < alpha

    if "significant" not in ttest_row.index:
        return False

    return is_true_like(ttest_row["significant"])


def find_p_value(ttest_row: pd.Series) -> float | None:
    """Read a p-value from a statistical-test row."""
    for column_name in P_VALUE_COLUMNS:
        if column_name not in ttest_row.index:
            continue

        p_value = parse_p_value(ttest_row[column_name])

        if p_value is not None:
            return p_value

    return None


def parse_p_value(value: object) -> float | None:
    """Convert a CSV p-value cell to a float."""
    if pd.isna(value):
        return None

    text_value = str(value).strip()

    if text_value.startswith("<"):
        text_value = text_value[1:].strip()

    try:
        return float(text_value)
    except ValueError:
        return None


def is_false_like(value: object) -> bool:
    """Return True when a CSV value means logical False."""
    if isinstance(value, bool):
        return not value

    if pd.isna(value):
        return False

    normalized_value = str(value).strip().lower()
    return normalized_value in {"false", "0", "0.0", "no", "n"}


def is_true_like(value: object) -> bool:
    """Return True when a CSV value means logical True."""
    if isinstance(value, bool):
        return value

    if pd.isna(value):
        return False

    normalized_value = str(value).strip().lower()
    return normalized_value in {"true", "1", "1.0", "yes", "y"}


def format_metric_value(
    results_cache: ResultsCache,
    dataset_folder: str,
    config_name: str,
    metric_name: str,
) -> str:
    """Return one LaTeX cell for a config/metric/dataset combination."""
    metrics_table, bold_configs_by_metric, dagger_configs_by_metric = results_cache[
        dataset_folder
    ]
    matching_rows = metrics_table[
        (metrics_table["config"] == config_name)
        & (metrics_table["metric"] == metric_name)
    ]

    if matching_rows.empty:
        return MISSING_VALUE

    result_row = matching_rows.iloc[0]
    cell_text = f"{result_row['mean']:.4f} $\\pm$ {result_row['std']:.4f}"

    if config_name in dagger_configs_by_metric.get(metric_name, set()):
        cell_text = f"{cell_text}{DAGGER}"

    if config_name in bold_configs_by_metric.get(metric_name, set()):
        cell_text = f"\\textbf{{{cell_text}}}"

    return cell_text


def make_result_row(
    results_cache: ResultsCache,
    metric_name: str,
    metric_label: str,
    left_cell: str,
    no_duplicate_config: str,
    duplicate_config: str,
) -> str:
    """Build one body row of the LaTeX table."""
    cell_values: list[str] = []

    for dataset_folder, _ in DATASETS:
        duplicate_value = format_metric_value(
            results_cache,
            dataset_folder,
            duplicate_config,
            metric_name,
        )
        no_duplicate_value = format_metric_value(
            results_cache,
            dataset_folder,
            no_duplicate_config,
            metric_name,
        )

        cell_values.extend([duplicate_value, no_duplicate_value])

    return f"{left_cell} & {metric_label} & {' & '.join(cell_values)} \\\\"


def build_latex_table(results_cache: ResultsCache, alpha: float) -> str:
    """Build and return the appendix LaTeX table."""
    lines: list[str] = []
    add_line = lines.append

    add_line(r"\begin{table}")
    add_line(r"    \scriptsize")
    add_line(r"    \setlength{\tabcolsep}{6pt}")
    add_line(r"    \centering")
    add_line(
        rf"    \caption{{Effect of adding segment-header minimum features to the corrected-value configurations for anomaly detection. Values in bold are the best results, and results not significantly different from the best, within this appendix comparison. A dagger ($^\dagger$) marks the better value when duplicate and no-duplicate variants differ significantly ($p < {alpha:g}$).}}"
    )
    add_line(r"    \label{tab:seg_header_min_exp_ad}")
    add_line(r"    \resizebox{\textwidth}{!}{")
    add_line(r"    \begin{tabular}{c l c c c c}")
    add_line(r"        \toprule")
    add_line(
        r"        & & \multicolumn{2}{c}{\textbf{\cicids}} & \multicolumn{2}{c}{\textbf{\insdn}} \\"
    )
    add_line(r"        \cmidrule(lr){3-4} \cmidrule(lr){5-6}")
    add_line(
        r"        \textbf{Config} & \textbf{Metric} & \textbf{w/ duplicates $\varphi_{i}'$} & \textbf{w/o duplicates $\varphi_{i}$} & \textbf{w/ duplicates $\varphi_{i}'$} & \textbf{w/o duplicates $\varphi_{i}$} \\"
    )
    add_line(r"        \midrule")

    for group_index, (
        _group_name,
        no_duplicate_config,
        duplicate_config,
        group_label,
    ) in enumerate(APPENDIX_CONFIG_GROUPS):
        for metric_index, (metric_name, metric_label) in enumerate(METRICS):
            if metric_index == 0:
                left_cell = rf"        \multirow{{5}}{{*}}{{{group_label}}}"
            else:
                left_cell = "        "

            result_row = make_result_row(
                results_cache=results_cache,
                metric_name=metric_name,
                metric_label=metric_label,
                left_cell=left_cell,
                no_duplicate_config=no_duplicate_config,
                duplicate_config=duplicate_config,
            )
            add_line(result_row)

        if group_index != len(APPENDIX_CONFIG_GROUPS) - 1:
            add_line(r"        \midrule")

    add_line(r"        \bottomrule")
    add_line(r"    \end{tabular}")
    add_line(r"    }")
    add_line(r"\end{table}")

    return "\n".join(lines)


def main() -> None:
    """Read the result CSVs and write the appendix LaTeX table."""
    args = parse_args()
    results_dir: Path = args.results_dir
    alpha: float = args.alpha

    results_cache = {
        dataset_folder: read_dataset_results(results_dir, dataset_folder, alpha)
        for dataset_folder, _ in DATASETS
    }

    output_path = args.output
    if output_path is None:
        output_path = results_dir / DEFAULT_OUTPUT_FILE_NAME

    output_path.write_text(build_latex_table(results_cache, alpha), encoding="utf-8")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
