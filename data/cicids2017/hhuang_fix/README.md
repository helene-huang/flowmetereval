# CIC-IDS 2017 (hhuang fix)

This version of CIC-IDS 2017 was extracted using the version of CICFlowMeter by Huang et al.

## Get the dataset

The complete dataset can be downloaded directly from [here](https://zenodo.org/records/22016274).

If instead you want to generate it, follow these steps:
1) Download the PCAP files from the [CIC website](https://cicresearch.ca/CICDataset/CIC-IDS-2017/) and move them to `data/cicids2017/raw`
2) Make sure raw PCAP files are fixed and ordered by running `data/cicids2017/raw/fix_reorder.sh` (see the detailed instructions in `data/cicids2017/raw/README.md`)
3) Extract the CSV files using `hhuang/cicflowmeter:latest` (see `cicflowmeter/hhuang` directory) and place them in `data/cicids2017/hhuang_fix/unlabeled`
4) Label the CSV files by running `data/cicids2017/labeling/cicids2017_label_transfer.py`: navigate to `data/cicids2017/labeling` and run
```sh
uv run cicids2017_label_transfer.py --path ../hhuang_fix/
```
5) Merge the labeled files into a single `cicids2017.csv` file by navigating to `data/cicids2017/hhuang_fix/` and running
```sh
uv run merge_csvs.py
```

MD5 checksum:
```
ea6046dd1a3399ecbc88d682c3b5ba3e  cicids2017.csv
```
