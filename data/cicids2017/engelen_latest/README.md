# CICFlowmeter (Engelen et al., commit `4dd5319ad36457010d7a406505790b17a5828108`)

This version of the dataset is extracted using the latest version of CICFlowmeter by Engelen et al.

## Get the dataset

1) Extract the CSV files using `engelen/CICFlowmeter` (see `cicflowmeter/engelen` directory) and place them in `data/cicids2017/engelen_latest/unlabeled`
2) Label the CSV files by running `data/cicids2017/labeling/cicids2017_label_transfer.py`: navigate to `data/cicids2017/labeling` and run
```sh
uv run cicids2017_label_transfer.py --path ../engelen_latest/
```
3) Merge the labeled files into a single `cicids2017.csv` file by navigating to `data/cicids2017/engelen_latest/` and running
```sh
uv run merge_csvs.py
```