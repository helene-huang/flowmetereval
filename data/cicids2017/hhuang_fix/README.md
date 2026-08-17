# CIC-IDS 2017 (hhuang fix)

This version of the dataset is extracted using the version of CICFlowmeter by Huang et al. including only the feature fixes (without the extended feature set).

## Get the dataset

1) Extract the CSV files using `hhuang/CICFlowmeter:fix` (see `cicflowmeter/hhuang` directory) and place them in `data/cicids2017/hhuang_fix/unlabeled`
2) Label the CSV files by running `data/cicids2017/labeling/cicids2017_label_transfer.py`: navigate to `data/cicids2017/labeling` and run
```sh
uv run cicids2017_label_transfer.py --path ../hhuang_fix/
```
3) Merge the labeled files into a single `cicids2017.csv` file by navigating to `data/cicids2017/hhuang_fix/` and running
```sh
uv run merge_csvs.py
```