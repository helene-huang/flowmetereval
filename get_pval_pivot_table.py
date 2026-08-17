import pandas as pd
import re
import os


result_dir = "./results"
# result_dir = "./results_ad"

# base_dir: str = os.path.join(result_dir, "insdn_hhuang_fix")
base_dir: str = os.path.join(result_dir, "cicids2017_merged")

pval_file = os.path.join(base_dir, "ttest_results_accuracy_by_attack_category.csv")
res_file = os.path.join(base_dir, "mean_accuracy_per_attack_per_config.csv")

# pval_file = "./ttest_results_accuracy_by_attack_category.csv"
# res_file = "./mean_accuracy_per_attack_per_config.csv"
pvalue_table = pd.read_csv(pval_file)
result_table = pd.read_csv(res_file)
# -----------------------------------------------------------------------------
# Inputs:
#   result_table : dataframe with columns
#       class, engelen_no_duplicates, engelen_paper, ...
#
#   pvalue_table : dataframe with columns
#       class, config1, config2, p_value, significant, same_seeds
# -----------------------------------------------------------------------------

configs = [c for c in result_table.columns if c != "class"]

# -----------------------------------------------------------------------------
# Extract mean values
# -----------------------------------------------------------------------------

means = result_table.copy()

for cfg in configs:
    means[cfg] = (
        means[cfg]
        .str.extract(r'([0-9]*\.?[0-9]+)')[0]
        .astype(float)
    )

# -----------------------------------------------------------------------------
# Determine the best configuration for each class
# -----------------------------------------------------------------------------

best_config = (
    means
    .set_index("class")[configs]
    .idxmax(axis=1)
)

# -----------------------------------------------------------------------------
# Build lookup dictionary for significance tests
# -----------------------------------------------------------------------------

sig_lookup = {}

for _, row in pvalue_table.iterrows():

    key = (
        row["class"],
        frozenset((row["config1"], row["config2"]))
    )

    sig_lookup[key] = row["significant"]

# -----------------------------------------------------------------------------
# Determine which configs are NOT significantly different from the best
# -----------------------------------------------------------------------------

highlight = {}

for cls in means["class"]:

    best = best_config.loc[cls]

    tied = {best}

    for cfg in configs:

        if cfg == best:
            continue

        key = (
            cls,
            frozenset((best, cfg))
        )

        significant = sig_lookup.get(key, True)

        if not significant:
            tied.add(cfg)

    highlight[cls] = tied

# -----------------------------------------------------------------------------
# Create formatted dataframe
# -----------------------------------------------------------------------------

formatted = result_table.copy()

for cls in formatted["class"]:

    best = best_config.loc[cls]
    tied = highlight[cls]

    row_idx = formatted.index[formatted["class"] == cls][0]

    for cfg in configs:

        value = formatted.at[row_idx, cfg]

        if cfg == best:
            formatted.at[row_idx, cfg] = rf"\textbf{{{value}}}"

        elif cfg in tied:
            formatted.at[row_idx, cfg] = rf"\textbf{{{value}}}"

# -----------------------------------------------------------------------------
# Result
# -----------------------------------------------------------------------------


formatted["class"] = formatted["class"].apply(lambda x: x.replace(" - Attempted", "$^\dagger$"))
formatted["class"] = formatted["class"].apply(lambda x: x.replace("Web Attack", "WA"))

print(formatted)

# Optionally save:
formatted.to_latex(os.path.join(base_dir, "highlighted_results.tex"), index=False)



# import pandas as pd
# 
# if __name__ == "__main__":
# 
#     pval_file = "./ttest_results_accuracy_by_attack_category.csv"
#     res_file = "./mean_accuracy_per_attack_per_config.csv"
#     dfp = pd.read_csv(pval_file)
# 
#     print(dfp.head())
# 
#     df = pd.read_csv(res_file)
# 
#     print(df.head())
