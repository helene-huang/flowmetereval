"""Generate the LaTeX table with the overall model results.

The script reads, for each dataset, two CSV files:

- overall_metrics_summary.csv: mean/std results for each metric and config.
- ttest_results.csv: pairwise statistical tests between configs.

For each metric, the script bolds the best config and all configs that are not
statistically different from that best config. For FPR, lower is better. For all
other metrics, higher is better.

The script also compares each duplicate/no-duplicate config pair. When one side
is statistically significantly better than the other, the better value receives
a dagger in the table.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


DEFAULT_RESULTS_DIR = Path("results")
DEFAULT_ALPHA = 0.05
OUTPUT_FILE_NAME = "results_table.tex"
MISSING_VALUE = "---"
DAGGER = r"$^{\dagger}$"

DATASETS: list[tuple[str, str]] = [
    ("cicids2017_merged", r"\cicids"),
    ("insdn_hhuang_fix", r"\insdn"),
]

CONFIG_GROUPS: list[tuple[str, str | None, str]] = [
    ("engelenpaper", None, "engelen_paper"),
    ("O", "engelen_no_duplicates", "engelen_with_duplicates"),
    ("C", "hhuang_no_duplicates", "hhuang_with_duplicates"),
    (
        "S",
        "engelen_corrected_values_no_duplicates",
        "engelen_corrected_values_with_duplicates",
    ),
    (
        "A",  # a for appendix
        "engelen_corrected_values_no_duplicates_with_seg_header_min",
        "engelen_corrected_values_with_duplicates_with_seg_header_min",
    ),
]

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
    """Read command-line arguments.

    Returns:
        Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Generate the LaTeX overall results table."
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
        help="P-value threshold used for dagger annotations. Default: 0.05.",
    )
    return parser.parse_args()


def read_dataset_results(
    results_dir: Path,
    dataset_folder: str,
    alpha: float,
) -> DatasetResults:
    """Read one dataset and compute bold/dagger annotations.

    Args:
        results_dir: Root directory containing the dataset result folders.
        dataset_folder: Name of the dataset result folder.
        alpha: P-value threshold used for dagger annotations.

    Returns:
        The cleaned metric table, the configs that should be bolded by metric,
        and the configs that should receive a dagger by metric.
    """
    metrics_path = results_dir / dataset_folder / "overall_metrics_summary.csv"
    ttest_path = results_dir / dataset_folder / "ttest_results.csv"

    metrics_table = pd.read_csv(metrics_path)
    ttest_table = pd.read_csv(ttest_path)

    # The *_with_se rows are auxiliary rows and should not appear in the table.
    # metrics_table = metrics_table[
    #     ~metrics_table["config"].str.contains("_with_se", na=False)
    # ]

    bold_configs_by_metric = find_bold_configs_by_metric(metrics_table, ttest_table)
    dagger_configs_by_metric = find_dagger_configs_by_metric(
        metrics_table,
        ttest_table,
        alpha,
    )

    return metrics_table, bold_configs_by_metric, dagger_configs_by_metric


def find_bold_configs_by_metric(
    metrics_table: pd.DataFrame,
    ttest_table: pd.DataFrame,
) -> dict[str, set[str]]:
    """Find configs that should be printed in bold.

    The best config is bolded. Any config that is not statistically different
    from the best config is also bolded.

    Args:
        metrics_table: Table with mean/std results for all configs.
        ttest_table: Table with pairwise statistical test results.

    Returns:
        Dictionary mapping each metric to the configs that should be bolded.
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
    """Find duplicate/no-duplicate winners that should receive a dagger.

    A dagger is added only when a duplicate/no-duplicate pair was compared,
    the p-value is below ``alpha``, and one value is better than the other.
    Lower is better for FPR. Higher is better for all other metrics.

    Args:
        metrics_table: Table with mean/std results for all configs.
        ttest_table: Table with pairwise statistical test results.
        alpha: P-value threshold used for dagger annotations.

    Returns:
        Dictionary mapping each metric to the configs that should receive a
        dagger.
    """
    dagger_configs_by_metric: dict[str, set[str]] = {}

    for metric_name in metrics_table["metric"].unique():
        dagger_configs_by_metric[metric_name] = set()

        for _, no_duplicate_config, duplicate_config in CONFIG_GROUPS:
            if no_duplicate_config is None:
                continue

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
    """Return the best config for a metric.

    Lower is better for FPR. Higher is better for all other metrics.

    Args:
        metric_rows: Rows containing all configs for one metric.
        metric_name: Name of the metric being compared.

    Returns:
        Name of the config with the best mean value for the metric.
    """
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
    """Return the better config between two configs for one metric.

    Args:
        metrics_table: Table with mean/std results for all configs.
        metric_name: Name of the metric being compared.
        first_config: First config name.
        second_config: Second config name.

    Returns:
        The better config name, or None if one config is missing or the two
        configs have the same mean value.
    """
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
    """Read the mean value for one config/metric pair.

    Args:
        metrics_table: Table with mean/std results for all configs.
        config_name: Config name to look up.
        metric_name: Metric name to look up.

    Returns:
        The mean value, or None when the config/metric pair is missing.
    """
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
    """Find the statistical-test row comparing two configs.

    The config order does not matter: ``config1=A, config2=B`` and
    ``config1=B, config2=A`` are treated as the same comparison.

    Args:
        ttest_table: Table with pairwise statistical test results.
        metric_name: Name of the metric being compared.
        first_config: First config name.
        second_config: Second config name.

    Returns:
        The first matching t-test row, or None when the comparison is missing.
    """
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
    """Return True when a statistical-test row is significant.

    The function prefers a p-value column when available. If no p-value column
    exists, it falls back to a ``significant`` column.

    Args:
        ttest_row: Row from the statistical-test table.
        alpha: P-value threshold.

    Returns:
        True when the row indicates statistical significance, otherwise False.
    """
    p_value = find_p_value(ttest_row)

    if p_value is not None:
        return p_value < alpha

    if "significant" not in ttest_row.index:
        return False

    return is_true_like(ttest_row["significant"])


def find_p_value(ttest_row: pd.Series) -> float | None:
    """Read a p-value from a statistical-test row.

    Args:
        ttest_row: Row from the statistical-test table.

    Returns:
        The p-value, or None when no recognised p-value column is available.
    """
    for column_name in P_VALUE_COLUMNS:
        if column_name not in ttest_row.index:
            continue

        p_value = parse_p_value(ttest_row[column_name])

        if p_value is not None:
            return p_value

    return None


def parse_p_value(value: object) -> float | None:
    """Convert a CSV p-value cell to a float.

    Args:
        value: Raw p-value cell read from the CSV file.

    Returns:
        The parsed p-value, or None when the value cannot be parsed.
    """
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
    """Return True when a CSV value means logical False.

    This avoids the classic Python trap where ``bool("False")`` is True.

    Args:
        value: Value read from the CSV file.

    Returns:
        True when the value represents logical False, otherwise False.
    """
    if isinstance(value, bool):
        return not value

    if pd.isna(value):
        return False

    normalized_value = str(value).strip().lower()
    return normalized_value in {"false", "0", "0.0", "no", "n"}


def is_true_like(value: object) -> bool:
    """Return True when a CSV value means logical True.

    Args:
        value: Value read from the CSV file.

    Returns:
        True when the value represents logical True, otherwise False.
    """
    if isinstance(value, bool):
        return value

    if pd.isna(value):
        return False

    normalized_value = str(value).strip().lower()
    return normalized_value in {"true", "1", "1.0", "yes", "y"}


def format_metric_value(
    results_cache: ResultsCache,
    dataset_folder: str,
    config_name: str | None,
    metric_name: str,
) -> str:
    """Return one LaTeX cell for a config/metric/dataset combination.

    Args:
        results_cache: Cached metric tables and annotations for each dataset.
        dataset_folder: Dataset folder used as key in ``results_cache``.
        config_name: Name of the config to print, or None if no config exists.
        metric_name: Name of the metric to print.

    Returns:
        Formatted LaTeX cell containing ``mean ± std``, or the missing-value
        marker when the config/metric pair is unavailable.
    """
    if config_name is None:
        return MISSING_VALUE

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


def make_group_label(group_name: str, group_index: int) -> str:
    """Return the LaTeX label used in the first column of a config group.

    Args:
        group_name: Short config-group name, such as ``O``, ``C``, or ``S``.
        group_index: Zero-based index of the config group.

    Returns:
        LaTeX label for the config group.
    """
    if group_index == 0:
        return r"$\engelenpaper$"

    return rf"$\varphi_{{{group_name}}}$"


def make_result_row(
    results_cache: ResultsCache,
    metric_name: str,
    metric_label: str,
    left_cell: str,
    no_duplicate_config: str | None,
    duplicate_config: str,
) -> str:
    """Build one body row of the LaTeX table.

    The column order is dataset-first, then duplicate/no-duplicate status:

    1. CICIDS with duplicates.
    2. CICIDS without duplicates.
    3. INSDN with duplicates.
    4. INSDN without duplicates.

    Args:
        results_cache: Cached metric tables and annotations for each dataset.
        metric_name: Machine-readable metric name used in the CSV files.
        metric_label: Human-readable metric label printed in the table.
        left_cell: First LaTeX cell of the row, containing the multirow label
            when needed.
        no_duplicate_config: Config name without duplicates, or None if the
            config group has no no-duplicate variant.
        duplicate_config: Config name with duplicates.

    Returns:
        One complete LaTeX table row.
    """
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
    """Build and return the full LaTeX table.

    Args:
        results_cache: Cached metric tables and annotations for each dataset.
        alpha: P-value threshold used for dagger annotations.

    Returns:
        Complete LaTeX table as a string.
    """
    lines: list[str] = []
    add_line = lines.append

    add_line(r"\begin{table}")
    add_line(r"    \scriptsize")
    add_line(r"    \setlength{\tabcolsep}{6pt}")
    add_line(r"    \centering")
    add_line(
        rf"    \caption{{Model performance on \cicids and \insdn. Values in bold are the best results and the results that are not significantly different from the best result. A dagger ($^\dagger$) marks the better value when duplicate and no-duplicate variants differ significantly ($p < {alpha:g}$).}}"
    )
    add_line(r"    \label{tab:results_rf}")
    add_line(r"    \resizebox{\textwidth}{!}{")
    add_line(r"    \begin{tabular}{l l c c c c}")
    add_line(r"        \toprule")
    add_line(
        r"        & & \multicolumn{2}{c}{\textbf{\cicids}} & \multicolumn{2}{c}{\textbf{\insdn}} \\"
    )
    add_line(r"        \cmidrule(lr){3-4} \cmidrule(lr){5-6}")
    add_line(
        r"        \textbf{Config} & \textbf{Metric} & \textbf{w/ duplicates $\varphi_{i}'$} & \textbf{w/o duplicates $\varphi_{i}$} & \textbf{w/ duplicates $\varphi_{i}'$} & \textbf{w/o duplicates $\varphi_{i}$} \\"
    )
    add_line(r"        \midrule")

    for group_index, (group_name, no_duplicate_config, duplicate_config) in enumerate(
        CONFIG_GROUPS
    ):
        group_label = make_group_label(group_name, group_index)

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

        if group_index != len(CONFIG_GROUPS) - 1:
            add_line(r"        \midrule")

    add_line(r"        \bottomrule")
    add_line(r"    \end{tabular}")
    add_line(r"    }")
    add_line(r"\end{table}")

    return "\n".join(lines)


def main() -> None:
    """Read the result CSVs and write the LaTeX table."""
    args = parse_args()
    results_dir: Path = args.results_dir
    alpha: float = args.alpha

    results_cache = {
        dataset_folder: read_dataset_results(results_dir, dataset_folder, alpha)
        for dataset_folder, _ in DATASETS
    }

    output_path = results_dir / OUTPUT_FILE_NAME
    output_path.write_text(build_latex_table(results_cache, alpha), encoding="utf-8")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
