import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from scipy.stats import ttest_rel

from feature_mapping import MAP_ENGELEN_LATEST_NEW_OLD

def find_unique_configs(base_dir: str) -> list[str]:

    return sorted(
        list(
            set(
                d.split("_seed")[0] for d in os.listdir(base_dir) 
                if os.path.isdir(os.path.join(base_dir, d)) 
                #and d.startswith("file_")
            )
        )
    )


def extract_seeds(metric_files: list[str]) -> set[int]:
    """Return a set containing the seeds for one config
    """
    return set([int(s.split("seed")[-1].rstrip("/metrics.csv")) for s in metric_files])


def find_metric_files_per_config(base_dir: str, config: str):

    candidate_metric_files: list[str] = [
        os.path.join(base_dir, d, "metrics.csv") for d in os.listdir(base_dir)
        if os.path.isdir(os.path.join(base_dir, d))
        # and d.startswith(config)
        and d.startswith(f"{config}_seed")  # in case there are configs named "engelen" and "engelen_latest", it's true that "engelen_latest" starts with "engelen"
    ]
    return sorted(
        [fp for fp in candidate_metric_files if os.path.isfile(fp)],
        key=lambda fp: int(os.path.basename(os.path.dirname(fp)).split("_seed")[-1])
    )



def find_per_class_files_per_config(base_dir: str, config: str, filename: str) -> list[str]:
    """Find per-class CSV files (e.g. accuracy_by_attack_category.csv) for a given config."""
    candidate_files: list[str] = [
        os.path.join(base_dir, d, filename) for d in os.listdir(base_dir)
        if os.path.isdir(os.path.join(base_dir, d))
        and d.startswith(f"{config}_seed")
    ]
    return sorted(
        [fp for fp in candidate_files if os.path.isfile(fp)],
        key=lambda fp: int(os.path.basename(os.path.dirname(fp)).split("_seed")[-1])
    )


def set_first_row_as_header(df: pd.DataFrame):

    new_header = df.iloc[0] #grab the first row for the header
    df = df.iloc[1:] #take the data less the header row
    df.columns = new_header #set the header row as the df header␂
    df = df.rename_axis(None, axis=1)
    return df


def get_p_value(metrics1: pd.Series, metrics2: pd.Series) -> float:

    # a1 = metrics1.to_numpy()  # this gives dtype=object
    # a2 = metrics2.to_numpy()
    
    a1 = metrics1.astype(float).to_numpy()  # dtype=float
    a2 = metrics2.astype(float).to_numpy()

    # print("GG")

    print(f"{a1=}")
    print(f"{a2=}")

    return ttest_rel(a1, a2).pvalue


def load_per_class_file(filepath: str) -> pd.Series:
    """
    Load a per-class CSV (accuracy_by_attack_category.csv).
 
    Expected format:
        (empty) | value
        class_A | 0.91
        class_B | 0.87
        ...
 
    Returns a Series indexed by class name.
    """
    df = pd.read_csv(filepath, header=0, index_col=0)
    # The CSV has an unnamed first column (class names) and a second column named "value"
    # After read_csv with index_col=0, we get a single column DataFrame
    series = df.iloc[:, 0].astype(float)
    series.name = "value"
    return series

    
def load_per_class_data_for_config(
    base_dir: str, config: str, filename: str
) -> tuple[pd.DataFrame, list[int]]:
    """
    Load per-class data across all seeds for a given config and file.
 
    Returns:
        df: DataFrame where rows=seeds, columns=class names
        seeds: list of seed integers in the same order as rows
    """
    files = find_per_class_files_per_config(base_dir, config, filename)
    rows = []
    seeds = []
    for fp in files:
        seed = int(os.path.basename(os.path.dirname(fp)).split("_seed")[-1])
        series = load_per_class_file(fp)
        rows.append(series)
        seeds.append(seed)
 
    if not rows:
        return pd.DataFrame(), []
 
    df = pd.DataFrame(rows).reset_index(drop=True)
    return df, seeds


def save_per_seed_table(
    res: dict[str, pd.DataFrame],
    seeds_dict: dict[str, set[int]],
    unique_configs: list[str],
    metric: str,
    base_dir: str,
):
    """
    Save a CSV with rows=seeds and columns=configs for a given overall metric.
    Seeds are matched across configs when possible.
    """
    all_seeds = sorted(set().union(*seeds_dict.values()))
    rows = []
    for seed in all_seeds:
        row = {"seed": seed}
        for config in unique_configs:
            if seed in seeds_dict[config]:
                # Find the row index corresponding to this seed
                # Seeds are stored in sorted order in res[config]
                sorted_seeds = sorted(seeds_dict[config])
                if seed in sorted_seeds:
                    idx = sorted_seeds.index(seed)
                    val = res[config][metric].astype(float).iloc[idx]
                    row[config] = val
                else:
                    row[config] = np.nan
            else:
                row[config] = np.nan
        rows.append(row)
 
    table = pd.DataFrame(rows).set_index("seed")
    out_path = os.path.join(base_dir, f"per_seed_{metric}.csv")
    table.to_csv(out_path)
    print(f"  Saved per-seed table: {out_path}")
    return table


def build_beautiful_table(
        unique_configs: list[str], 
        per_class_data: dict[str, tuple[pd.DataFrame, list[int]]], 
        content: str='meanpmstd'
) -> pd.DataFrame:

    class_names = []
    for config in unique_configs:
        df, seeds = per_class_data.get(config, (pd.DataFrame(), []))
        if not df.empty:
            class_names = list(df.columns)
            break
 
    if not class_names:
        print("  No class names found, skipping accuracy_per_attack_per_config.csv")
        return pd.DataFrame()
    rows = []
    for class_name in class_names:
        row = {"class": class_name}
        for config in unique_configs:
            df, seeds = per_class_data.get(config, (pd.DataFrame(), []))
            if not df.empty and class_name in df.columns:
                # Mean accuracy across all seeds for this class and config
                mu = df[class_name].astype(float).mean()
                sigma = df[class_name].astype(float).std()
                if content == 'meanpmstd':
                    row[config] = f"{mu:.4f} $\\pm$ {sigma:.4f}"
                elif content == 'mean':
                    row[config] = mu
                elif content == 'std':
                    row[config] = sigma
            else:
                row[config] = np.nan
        rows.append(row)
 
    table = pd.DataFrame(rows).set_index("class")
    
    # table = table.drop(["engelen_corrected_values_no_duplicates_with_seg_header_min",
    #                    "engelen_corrected_values_with_duplicates_with_seg_header_min"], 
    #                    axis=1)
    
    # Reorder the columns before saving to latex
    desired_order = [
        "engelen_with_duplicates",
        "engelen_no_duplicates",
        "hhuang_with_duplicates",
        "hhuang_no_duplicates",
        "engelen_corrected_values_with_duplicates",
        "engelen_corrected_values_no_duplicates",
        "engelen_corrected_values_with_duplicates_with_seg_header_min",
        "engelen_corrected_values_no_duplicates_with_seg_header_min",
    ]

    # Put engelen_paper first if it exists
    #if "engelen_paper" in table.columns:
    #    desired_order = ["engelen_paper"] + desired_order
    table = table[desired_order]

    return table



def save_mean_accuracy_per_attack_per_config(
    per_class_data: dict[str, tuple[pd.DataFrame, list[int]]],
    unique_configs: list[str],
    base_dir: str,
):
    """
    Save a summary CSV: mean accuracy per attack class, one column per config.
 
    Output shape: rows=attack classes, columns=configs
    Example (accuracy_per_attack_per_config.csv):
        class | baseline | model_A | model_B
        DoS   | 0.91     | 0.94    | 0.90
        Probe | 0.87     | 0.85    | 0.88
    """
    # Get the list of attack class names from the first config that has data

    table = build_beautiful_table(unique_configs, per_class_data, content='meanpmstd')
    if len(table) == 0:
        return

    mean_recall_table = build_beautiful_table(unique_configs, per_class_data, content='mean')

    micro_recall_table = mean_recall_table.agg(lambda x: rf"{x.mean():.4f}$\pm${x.std():.4f}")
    micro_recall_table.columns = ['micro detection rate']
    micro_recall_table.to_latex(os.path.join(base_dir, "micro_accuracy_across_attacks.tex"))

    out_path = os.path.join(base_dir, "mean_accuracy_per_attack_per_config.csv")
    table.to_csv(out_path)
        
    table.to_latex(
        os.path.join(base_dir, "mean_accuracy_per_attack_per_config.tex"),
    )
    
    print(f"  Saved accuracy per attack per config: {out_path}")


def run_per_class_ttests(
    per_class_data: dict[str, tuple[pd.DataFrame, list[int]]],
    seeds_dict_per_class: dict[str, set[int]],
    unique_configs: list[str],
    base_dir: str,
):
    """
    For each attack class, run a paired t-test between every pair of configs.
    Saves results to ttest_results_accuracy_by_attack_category.csv.
 
    A paired t-test checks: "is the difference between config A and config B
    consistent enough across seeds to be considered real, or could it be random?"
    p_value < 0.05 means the difference is likely real.
    """
    ttest_results = []
 
    # Get class names from the first config that has data
    class_names = []
    for config in unique_configs:
        df, seeds = per_class_data.get(config, (pd.DataFrame(), []))
        if not df.empty:
            class_names = list(df.columns)
            break
 
    if not class_names:
        print("  No class names found, skipping t-tests.")
        return
 
    for class_name in class_names:
        for i, config in enumerate(unique_configs):
            for j, other_config in enumerate(unique_configs):
                if j <= i:
                    continue  # skip duplicate pairs and self-comparisons
 
                print("================================")
                print(f"Class: {class_name}, Config 1: {config}, Config 2: {other_config}")
 
                seeds1 = seeds_dict_per_class.get(config, set())
                seeds2 = seeds_dict_per_class.get(other_config, set())
 
                if seeds1 == seeds2 and seeds1:
                    # Same seeds: we can do a paired t-test
                    df1, _ = per_class_data[config]
                    df2, _ = per_class_data[other_config]
 
                    if class_name not in df1.columns or class_name not in df2.columns:
                        print(f"  Class '{class_name}' missing in one config, skipping.")
                        continue
 
                    vals1 = df1[class_name].astype(float).to_numpy()
                    vals2 = df2[class_name].astype(float).to_numpy()
 
                    pval = ttest_rel(vals1, vals2).pvalue
                    significant = pval < 0.05
                    print(f"  p-value: {pval} (significant: {significant})")
 
                    ttest_results.append({
                        "class": class_name,
                        "config1": config,
                        "config2": other_config,
                        "p_value": pval,
                        "significant": significant,
                        "same_seeds": True,
                    })
                else:
                    # Different seeds: cannot do a paired t-test, log NaN
                    print("  Configs have different seeds: cannot do paired t-test.")
                    ttest_results.append({
                        "class": class_name,
                        "config1": config,
                        "config2": other_config,
                        "p_value": np.nan,
                        "significant": np.nan,
                        "same_seeds": False,
                    })
 
    if ttest_results:
        ttest_df = pd.DataFrame(ttest_results)
        out_path = os.path.join(base_dir, "ttest_results_accuracy_by_attack_category.csv")
        ttest_df.to_csv(out_path, index=False)
        print(f"\nSaved per-class t-test results: {out_path}")




# ------------------------------------------------------------------- #
#  Feature importances: average over seeds, compare across configs    #
# ------------------------------------------------------------------- #
 
def find_feature_importance_files_per_config(base_dir: str, config: str) -> list[str]:
    """Find all feature_importances.csv files for a given config across seeds."""
    files = []
    for entry in os.scandir(base_dir):
        if entry.is_dir() and entry.name.startswith(config + "_seed"):
            fpath = os.path.join(entry.path, "feature_importances.csv")
            if os.path.isfile(fpath):
                files.append(fpath)
    return sorted(files)


def load_feature_importances_for_config(base_dir: str, config: str) -> pd.Series:
    """
    Load feature_importances.csv for all seeds of a config and return
    a Series of mean importance values indexed by feature name.
    """
    files = find_feature_importance_files_per_config(base_dir, config)
 
    if not files:
        print(f"  Warning: no feature_importances.csv found for config '{config}'")
        return pd.Series(dtype=float)
 
    dfs = []
    for fpath in files:
        df = pd.read_csv(fpath, index_col=0, header=0)
        # Defensive: keep only the first column in case of extra columns
        series = df.iloc[:, 0].rename(config)
        series.index.name = "feature"
        dfs.append(series)
 
    # Stack seeds as columns, average row-wise (features are consistent within a config)
    combined = pd.concat(dfs, axis=1)  # shape: [n_features x n_seeds]
    mean_series = combined.mean(axis=1)
    mean_series.name = config
    mean_series.index.name = "feature"
 
    print(f"  Config '{config}': averaged {len(files)} seed(s), {len(mean_series)} features")
    return mean_series
 

def save_mean_feature_importances(
    base_dir: str,
    unique_configs: list[str],
    fill_missing: float = float("nan"),
) -> pd.DataFrame:
    """
    For each config, compute mean feature importances across seeds.
    Combine into a single DataFrame (features x configs), saving to CSV.
    Missing features for a given config are filled with `fill_missing` (default NaN).
 
    Returns the combined DataFrame.
    """
    all_series = {}
    for config in unique_configs:
        s = load_feature_importances_for_config(base_dir, config)
        if not s.empty:
            all_series[config] = s
 
    if not all_series:
        print("No feature importance data found.")
        return pd.DataFrame()
 
    # Outer join across all configs: missing features become NaN (or fill_missing)
    combined = pd.concat(all_series.values(), axis=1)  # shape: [n_features x n_configs]
    combined.columns = list(all_series.keys())
    combined.index.name = "feature"
 
    if not np.isnan(fill_missing):
        combined = combined.fillna(fill_missing)
 
    out_path = os.path.join(base_dir, "mean_feature_importances.csv")
    combined.to_csv(out_path)
    print(f"\nSaved combined feature importances to: {out_path}")
    print(combined)
 
    return combined
 

def add_remapped_config_columns(
    fi_df: pd.DataFrame,
    source_config: str,
    new_config_name: str,
    feature_map: dict,  # keys = current names (in source_config), values = desired display names
    base_dir: str,
    top_n: int = 10,
) -> pd.DataFrame:
    """
    Takes the top-N features from `source_config` in fi_df, remaps their
    names via `feature_map`, and appends them as a new config column
    (`new_config_name`) to the top-10 table.

    feature_map: {new_name_in_source: old_name_to_display}
    """
    col = fi_df[source_config].dropna()
    top = col.nlargest(top_n).reset_index()
    top.columns = ["feature", "importance"]
    top["importance"] = top["importance"].round(4)

    # Remap feature names, warn if any are missing from the map
    missing = set(top["feature"]) - set(feature_map.keys())
    if missing:
        print(f"  Warning: {len(missing)} feature(s) from '{source_config}' not found in map: {missing}")

    top["feature"] = top["feature"].map(feature_map).fillna(top["feature"])  # fallback to original if missing

    return top  # caller inserts this into the side-by-side table


def save_top_n_feature_importances(
    fi_df: pd.DataFrame,
    base_dir: str,
    top_n: int = 30,
    configs: list[str] = ["engelen_with_duplicates", "engelen_paper", "hhuang_no_duplicates"],
    extra_cols: dict[str, pd.DataFrame] | None = None,  # {display_name: top-N DataFrame}
) -> pd.DataFrame:
    """
    extra_cols: pre-built top-N DataFrames (with 'feature'/'importance' columns)
    to append as additional configs in the side-by-side table.
    """
    frames = {}

    if extra_cols:
        for name, top_df in extra_cols.items():
            frames[name] = top_df.reset_index(drop=True)

    # for config in fi_df.columns:
    for config in configs:
        col = fi_df[config].dropna()
        top = col.nlargest(top_n).reset_index()
        top.columns = ["feature", "importance"]
        top["importance"] = top["importance"].round(4)
        frames[config] = top


    combined = pd.concat(frames, axis=1)
    combined.index = range(1, top_n + 1)
    combined.index.name = "rank"

    out_path = os.path.join(base_dir, f"top{top_n}_feature_importances.csv")
    combined.to_csv(out_path)
    print(f"Saved top-{top_n} feature importances to: {out_path}")
    print(combined.to_string())

    return combined



# ------------------------------------------ #
#  Feature importances: bar chart            #
# ------------------------------------------ #

def load_feature_importances_per_seed_for_config(base_dir: str, config: str) -> pd.DataFrame:
    """
    Load feature_importances.csv for all seeds of a config.
    Returns a DataFrame of shape [n_features x n_seeds].
    """
    files = find_feature_importance_files_per_config(base_dir, config)

    if not files:
        print(f"  Warning: no feature_importances.csv found for config '{config}'")
        return pd.DataFrame()

    dfs = []
    for fpath in files:
        df = pd.read_csv(fpath, index_col=0, header=0)
        series = df.iloc[:, 0]
        series.index.name = "feature"
        dfs.append(series)

    combined = pd.concat(dfs, axis=1)  # [n_features x n_seeds]
    combined.columns = range(len(dfs))
    return combined


def plot_feature_importance_bar_chart(
    base_dir: str,
    configs: list[str],
    top_n: int | None = None,
    order: str = "mean_importance",   # "mean_importance" | "config_name"
    order_config: str | None = None,  # used when order="config_name"
    common_only: bool = False,
    fill_missing: float = 0.0,
    figsize: tuple = (18, 6),
):
    """
    Bar chart of feature importances across configs, grouped by feature.

    Parameters
    ----------
    base_dir       : base directory containing config subdirs
    configs        : list of config names to include (excludes e.g. engelen_latest_og)
    top_n          : if set, only show the top N features (by the chosen ordering)
    order          : "mean_importance" sorts by avg across selected configs;
                     "config_name" sorts by the config given in order_config
    order_config   : config to sort by when order="config_name"
    common_only    : if True, only show features present in ALL selected configs
    fill_missing   : value to use for features absent in a config (default 0.0)
    figsize        : matplotlib figure size
    """

    # ------------------------------------------------------------------ #
    # 1. Load per-seed data for each config                              #
    # ------------------------------------------------------------------ #
    per_seed: dict[str, pd.DataFrame] = {}
    for config in configs:
        df = load_feature_importances_per_seed_for_config(base_dir, config)
        if not df.empty:
            per_seed[config] = df

    if not per_seed:
        print("No data found for any config.")
        return

    # ------------------------------------------------------------------ #
    # 2. Build summary stats: mean, min, max per feature per config      #
    # ------------------------------------------------------------------ #
    means = pd.DataFrame({c: df.mean(axis=1) for c, df in per_seed.items()})
    mins  = pd.DataFrame({c: df.min(axis=1)  for c, df in per_seed.items()})
    maxs  = pd.DataFrame({c: df.max(axis=1)  for c, df in per_seed.items()})

    # ------------------------------------------------------------------ #
    # 3. Filter: common_only or fill missing with 0                      #
    # ------------------------------------------------------------------ #
    if common_only:
        mask = means.notna().all(axis=1)
        means = means[mask]
        mins  = mins[mask]
        maxs  = maxs[mask]
        print(f"  common_only=True: {mask.sum()} features retained out of {len(mask)}")
    else:
        means = means.fillna(fill_missing)
        mins  = mins.fillna(fill_missing)
        maxs  = maxs.fillna(fill_missing)

    # ------------------------------------------------------------------ #
    # 4. Order features                                                  #
    # ------------------------------------------------------------------ #
    if order == "mean_importance":
        sort_vals = means.mean(axis=1)
    elif order == "config_name":
        if order_config is None or order_config not in means.columns:
            raise ValueError(
                f"order='config_name' requires a valid order_config. "
                f"Got: {order_config!r}. Available: {list(means.columns)}"
            )
        sort_vals = means[order_config]
    else:
        raise ValueError(f"Unknown order: {order!r}. Use 'mean_importance' or 'config_name'.")

    sorted_idx = sort_vals.sort_values(ascending=False).index

    if top_n is not None:
        sorted_idx = sorted_idx[:top_n]

    means = means.loc[sorted_idx]
    mins  = mins.loc[sorted_idx]
    maxs  = maxs.loc[sorted_idx]

    # ------------------------------------------------------------------ #
    # 5. Plot                                                            #
    # ------------------------------------------------------------------ #
    n_features = len(means)
    n_configs  = len(configs)

    # bar_width  = 0.8 / n_configs   # bars fill 80% of each feature slot
    bar_width = min(0.15, 0.8 / n_configs)
    # x          = np.arange(n_features)
    feature_spacing = 1.0  # smaller = less space between bars
    x = np.arange(n_features) * feature_spacing

    fig, ax = plt.subplots(figsize=figsize)

    for i, config in enumerate(configs):
        if config not in means.columns:
            continue

        offset     = (i - n_configs / 2 + 0.5) * bar_width
        mean_vals  = means[config].values
        err_low    = mean_vals - mins[config].values
        err_high   = maxs[config].values - mean_vals

        ax.bar(
            x + offset,
            mean_vals,
            width=bar_width,
            label=config,
            alpha=0.85,
        )
        ax.errorbar(
            x + offset,
            mean_vals,
            yerr=(err_low, err_high),
            fmt="none",
            color="black",
            capsize=3,
            linewidth=1,
        )

    ax.set_xticks(x)
    # ax.set_xticklabels(means.index, rotation=90, fontsize=8)

    x_labels = [
        f"{feature}\n(previously: {MAP_ENGELEN_LATEST_NEW_OLD[feature]})"
        if (
            "Seg" in feature
            and feature in MAP_ENGELEN_LATEST_NEW_OLD
            and MAP_ENGELEN_LATEST_NEW_OLD[feature] != feature
        )
        else feature
        for feature in means.index
    ]

    ax.set_xticklabels(x_labels, rotation=45, ha="right", fontsize=7)

    # set the duplictes in bold
    payload_features_to_bold = {
        "Fwd Segment Payload Length Avg",
        "Fwd Segment Payload Length Mean",
    }

    displayed_features = set(means.index)
    if payload_features_to_bold.issubset(displayed_features):
        for tick_label, feature in zip(ax.get_xticklabels(), means.index):
            if feature in payload_features_to_bold:
                tick_label.set_fontweight("bold")

    ax.set_ylabel("Feature Importance")
    ax.set_xlabel("Feature")

    """ title_parts = []
    if top_n:
        title_parts.append(f"Top {top_n}")
    title_parts.append("Feature Importances by Config")
    if common_only:
        title_parts.append("(common features only)")
    ax.set_title(" - ".join(title_parts)) """
    
    # ax.set_title("Top-20 Feature Importances with Corrected Feature Names")
    # ax.set_title("Top-20 Feature Importances Ranked by φ′C")
    ax.set_title("Top-20 Feature Importances Ranked by φ′O")

    ax.legend(loc="upper right", fontsize=8)
    # ax.set_xlim(-0.5, n_features - 0.5)
    ax.set_xlim(x[0] - feature_spacing / 2, x[-1] + feature_spacing / 2)
    plt.tight_layout()

    # ------------------------------------------------------------------ #
    # 6. Save                                                            #
    # ------------------------------------------------------------------ #
    suffix_parts = []
    if top_n:
        suffix_parts.append(f"top{top_n}")
    suffix_parts.append(f"order_{order}")
    if common_only:
        suffix_parts.append("common")
    suffix = "_".join(suffix_parts)

    out_path = os.path.join(base_dir, f"feature_importance_barchart_{suffix}.pdf")
    plt.savefig(out_path)
    plt.draw()
    print(f"Saved bar chart to: {out_path}")




if __name__ == "__main__":

    # Example path "./results/cicids2017_hhuang_fix/file_0_seed2/metrics.csv"

    result_dir = "./results"
    # result_dir = "./results_ad"

    # base_dir: str = os.path.join(result_dir, "insdn_hhuang_fix")
    base_dir: str = os.path.join(result_dir, "cicids2017_merged")

    unique_configs = find_unique_configs(base_dir)

    print(f"Unique configs found: {str(unique_configs)}")


    # ------------------------------------ -------------- #
    #  Load overall metrics (metrics.csv)                 #
    # --------------------------------------------------- #

    res: dict[str, pd.DataFrame] = {}
    seeds_dict: dict[str, set[int]] = {}

    for config in unique_configs:
        metric_files = find_metric_files_per_config(base_dir, config)

        df = pd.DataFrame()
        for metric_file in metric_files:
            #print(f"Processing file {metric_file}")
            dft: pd.DataFrame = pd.read_csv(metric_file).T
            dft = set_first_row_as_header(dft)
            df = pd.concat((df, dft), axis=0)
        df = df.reset_index(drop=True) 
        res[config] = df
        seeds_dict[config] = extract_seeds(metric_files)


    # ------------------------------------------------------------------ #
    #  Overall metrics: t-tests, per-seed tables, bar charts             #
    # ------------------------------------------------------------------ #
    ttest_results: list[dict] = []

    # Summary of all overall metrics
    overall_summary: list[dict] = []

    for metric in ("accuracy", "tpr", "fpr", "f1", "roc_auc"):
        print(f"\n{'='*60}")
        print(f"Overall metric: {metric}")

        # Per-seed table
        save_per_seed_table(res, seeds_dict, unique_configs, metric, base_dir)

        avg_vals = []
        min_vals = []
        max_vals = []
        x_range = np.arange(len(res))

        for i, config in enumerate(unique_configs):
            mean = res[config][metric].mean()
            std = res[config][metric].std()
            minimum = res[config][metric].min()
            maximum = res[config][metric].max()

            avg_vals.append(mean)
            min_vals.append(minimum)
            max_vals.append(maximum)

            overall_summary.append({
                "config": config,
                "metric": metric,
                "mean": mean,
                "std": std,
                "min": minimum,
                "max": maximum,
            })

            for j, other_config in enumerate(unique_configs):
                if j <= i:  # skip duplicate pairs and self-comparisons
                    continue

                print("================================")
                print(f"Metric: {metric}, Config 1: {config}, Config 2: {other_config}")

                if seeds_dict[config] == seeds_dict[other_config]:
                    print(res[config][metric].dtype)
                    pval = get_p_value(res[config][metric], res[other_config][metric])
                    
                    significant = pval < 0.05
                    print(f"p-value: {pval} (significant: {significant})")
                    
                    ttest_results.append({
                        "metric": metric,
                        "config1": config,
                        "config2": other_config,
                        "p_value": pval,
                        "significant": significant,
                        "same_seeds": True,
                    })

                else:
                    print("Configs have different seeds:")
                    print(f"{config}: {seeds_dict[config]}")
                    print(f"{other_config}: {seeds_dict[other_config]}")
                    ttest_results.append({
                        "metric": metric,
                        "config1": config,
                        "config2": other_config,
                        "p_value": np.nan,
                        "significant": np.nan,
                        "same_seeds": False,
                    })

        avg_array = np.asarray(avg_vals)
        min_array = np.asarray(min_vals)
        max_array = np.asarray(max_vals)

        res_df = pd.DataFrame({"config": unique_configs, "min": min_array, "mean": avg_array, "max": max_array})
        res_df.to_csv(os.path.join(base_dir, f"compare_{metric}.csv"))

        #print(f"{x_range.shape=}")
        #print(f"{avg_array.shape=}")

        plt.figure()
        plt.bar(x_range, avg_array)
        plt.errorbar(x_range, avg_array, yerr=(avg_array-min_array, max_array - avg_array), fmt='.', color='k')
        # plt.xticks(x_range, [f"config {config:d}" for config in unique_configs], rotation=90)
        plt.xticks(x_range, unique_configs, rotation=90)
        plt.ylabel(f"{metric}")
        plt.tight_layout()
        plt.savefig(os.path.join(base_dir, f"compare_{metric}.pdf"))

        plt.draw()

    # Save overall ttest results
    ttest_df = pd.DataFrame(ttest_results)
    ttest_df.to_csv(
        os.path.join(base_dir, "ttest_results.csv"),
        index=False
    )

    
    # Save summary of all overall metrics
    overall_df = pd.DataFrame(overall_summary)

    overall_df = overall_df[
        ["config", "metric", "mean", "std", "min", "max"]
    ]

    overall_df.to_csv(
        os.path.join(base_dir, "overall_metrics_summary.csv"),
        index=False,
    )

    overall_df.to_latex(
        os.path.join(base_dir, "overall_metrics_summary.tex"),
        float_format="%.4f", 
        index=False,
    )

    print(f"Saved overall metric summary to: {os.path.join(base_dir, 'overall_metrics_summary.csv')}")

    # ------------------------------------------------------------------- #
    # Per-attack accuracy: summary table + t-tests                       #
    # Only using accuracy_by_attack_category.csv, ignoring probabilities. #
    # ------------------------------------------------------------------- #
 
    print(f"\n{'='*60}")
    print("Processing accuracy_by_attack_category.csv")
 
    # Load per-class accuracy data for all configs
    # per_class_data[config] = (DataFrame of shape [n_seeds x n_classes], list of seed numbers)
    per_class_data: dict[str, tuple[pd.DataFrame, list[int]]] = {}
    seeds_dict_per_class: dict[str, set[int]] = {}
 
    for config in unique_configs:
        df, seeds = load_per_class_data_for_config(base_dir, config, "accuracy_by_attack_category.csv")
        per_class_data[config] = (df, seeds)
        seeds_dict_per_class[config] = set(seeds)
 
        if df.empty:
            print(f"  Warning: no accuracy_by_attack_category.csv found for config '{config}'")
        else:
            print(f"  Config '{config}': {len(seeds)} seeds, classes: {list(df.columns)}")
 
    # Save mean accuracy per attack class per config (the main summary table)
    save_mean_accuracy_per_attack_per_config(per_class_data, unique_configs, base_dir)
 
    # Run paired t-tests per attack class, per config pair
    run_per_class_ttests(per_class_data, seeds_dict_per_class, unique_configs, base_dir)


    # ------------------------------------------------------------------- #
    #  Feature importances: average over seeds, compare across configs    #
    # ------------------------------------------------------------------- #

    if result_dir == "./results":  # only for random forest model
        print(f"\n{'='*60}")
        print("Processing feature_importances.csv")
    
        # fi_df is shape [n_features x n_configs]
        # Rows with NaN mean that feature was absent in that config.
        fi_df = save_mean_feature_importances(base_dir, unique_configs)

        top_n = 20

        remapped = add_remapped_config_columns(
            fi_df,
            source_config="engelen_with_duplicates",
            new_config_name="engelen_latest_og",
            feature_map=MAP_ENGELEN_LATEST_NEW_OLD,
            base_dir=base_dir,
            top_n=top_n,
        )

        if "cicids2017" in base_dir:
            # CICIDS2017 configs
            configs = ["engelen_with_duplicates", "engelen_paper", "engelen_no_duplicates", "hhuang_with_duplicates", "hhuang_no_duplicates", "engelen_corrected_values_with_duplicates", "engelen_corrected_values_no_duplicates"]
        else:
            # InSDN configs, there is no engelen_paper version for InSDN
            configs = ["engelen_with_duplicates", "engelen_no_duplicates", "hhuang_with_duplicates", "hhuang_no_duplicates"]
        save_top_n_feature_importances(
            fi_df,
            base_dir,
            top_n=top_n,
            configs=configs,
            extra_cols={"engelen_latest_og": remapped},
        )


        # -------------------------------------------------------------------- #
        #  Bar chart of feature importance across configs, grouped by feature  #
        # -------------------------------------------------------------------- #
        CONFIGS_TO_PLOT = [
            "engelen_with_duplicates",
            "engelen_no_duplicates",
            "hhuang_with_duplicates",
            "hhuang_no_duplicates",
            "engelen_corrected_values_with_duplicates", 
            "engelen_corrected_values_no_duplicates"
        ]

        # All features, sorted by mean importance across configs
        #plot_feature_importance_bar_chart(
        #    base_dir, 
        #    CONFIGS_TO_PLOT, 
        #    order="mean_importance")

        # Top-n only
        #plot_feature_importance_bar_chart(
        #    base_dir, 
        #    CONFIGS_TO_PLOT, 
        #    top_n=top_n, 
        #    order="mean_importance")

        # Top-n, sorted by one specific config's ranking
        # plot_feature_importance_bar_chart(
        #     base_dir, 
        #     CONFIGS_TO_PLOT, 
        #     top_n=top_n,
        #     order="config_name",
        #     order_config="engelen_with_duplicates")

        #plot_feature_importance_bar_chart(
        #    base_dir,
        #    ["hhuang_with_duplicates", "engelen_with_duplicates", "engelen_corrected_values_with_duplicates"],
        #    top_n=top_n,
        #    order="config_name",
        #    order_config="hhuang_with_duplicates")
        
        plot_feature_importance_bar_chart(
            base_dir,
            ["engelen_with_duplicates", "hhuang_with_duplicates", "engelen_corrected_values_with_duplicates"],
            top_n=top_n,
            order="config_name",
            order_config="engelen_with_duplicates")


        # Only features present in all configs
        # plot_feature_importance_bar_chart(
        #    base_dir, 
        #    CONFIGS_TO_PLOT, 
        #    top_n=top_n,
        #    order="mean_importance", 
        #    common_only=True)
