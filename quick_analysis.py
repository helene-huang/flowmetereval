import numpy as np
import pandas as pd
import polars as pl
import matplotlib.pyplot as plt

import matplotlib.colors as mcolors

def plot_binned_heatmap(csv_path: str, n_time_bins: int = 500, output_path: str = "timegoeson_cicids2017.png", split: float | None=None):
    # 1. Read data and map labels to category IDs
    df = (
        pl.read_csv(csv_path, columns=["Timestamp", "Label"])
        .with_columns(
            pl.col("Timestamp").str.to_datetime(),
            pl.col("Label").cast(pl.Categorical).to_physical().alias("Label_ID")
        )
    )

    timestamps = df["Timestamp"].to_numpy()
    label_ids  = df["Label_ID"].to_numpy()

    # 2. Build a 2D count matrix: rows = labels, cols = time bins
    t_min, t_max = timestamps.min(), timestamps.max()
    time_bin_indices = np.floor(
        (timestamps - t_min) / (t_max - t_min) * (n_time_bins - 1)
    ).astype(int)

    n_labels = int(label_ids.max()) + 1
    count_matrix = np.zeros((n_labels, n_time_bins), dtype=np.float32)
    np.add.at(count_matrix, (label_ids, time_bin_indices), 1)

    # 3. Log-scale the counts so sparse and dense regions are both visible
    display_matrix = np.log1p(count_matrix)

    # 4. Plot as a heatmap — each cell's colour encodes event density
    fig, ax = plt.subplots(figsize=(14, max(4, n_labels * 0.5)))
    img = ax.imshow(
        display_matrix,
        aspect="auto",
        origin="lower",
        cmap="Blues",        
        interpolation="nearest",
    )

    if split is not None:
        #split_ts = np.quantile(timestamps[df["Label"] == "Normal"], split)
        #split_ts = np.quantile(timestamps[df["Label"] != "Normal"], split)
        split_ts = np.quantile(timestamps, split)
        split_bin = (split_ts - t_min) / (t_max - t_min) * (n_time_bins - 1)
        ax.axvline(split_bin, color="red", linestyle="--", linewidth=1.5, label=f"split={split}")
        ax.legend(loc="upper right")

    # 5. X-axis: map bin indices back to real timestamps
    n_xticks = 8
    xtick_bins = np.linspace(0, n_time_bins - 1, n_xticks, dtype=int)
    xtick_vals = xtick_bins / (n_time_bins - 1) * (t_max - t_min) + t_min
    xtick_labels = pd.to_datetime(xtick_vals, unit="s").strftime("%Y-%m-%d")
    ax.set_xticks(xtick_bins)
    ax.set_xticklabels(xtick_labels, rotation=30, ha="right")

    # 6. Y-axis: original label names, preserving category order
    label_names = (
        df.select(["Label", "Label_ID"])
        .unique()
        .sort("Label_ID")["Label"]
        .to_list()
    )
    ax.set_yticks(range(n_labels))
    ax.set_yticklabels(label_names)

    # 7. Colorbar
    cbar = fig.colorbar(img, ax=ax, pad=0.02)
    raw_ticks = np.expm1(np.linspace(0, display_matrix.max(), 6))
    cbar.set_ticks(np.log1p(raw_ticks))
    cbar.set_ticklabels([f"{v:.0f}" for v in raw_ticks])
    cbar.set_label("event count")

    ax.set_xlabel("Timestamp")
    ax.set_ylabel("Label")
    ax.set_title("Event density over time (binned)")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.show()


if __name__ == "__main__":

    # csv_path = "./data/insdn/hhuang_fix/final/insdn.csv"
    csv_path = "./data/cicids2017/hhuang_fix/cicids2017.csv"

    plot_binned_heatmap(csv_path, n_time_bins=500, split=0.3)
