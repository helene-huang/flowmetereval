# CIC-IDS 2017 (latest Liu, Engelen et al. version)

This version of CIC-IDS 2017 was extracted using the latest version of CICFlowmeter by Liu, Engelen et al. [1].

Link to the repo: https://github.com/GintsEngelen/CICFlowMeter

## Get the dataset

1) Download the PCAP files from the [CIC website](https://cicresearch.ca/CICDataset/CIC-IDS-2017/) and move them to `data/cicids2017/raw`
2) Make sure raw PCAP files are fixed and ordered by running `data/cicids2017/raw/fix_reorder.sh` (see the detailed instructions in `data/cicids2017/raw/README.md`)
3) Extract the CSV files using `engelen/cicflowmeter:latest` (see `cicflowmeter/engelen` directory) and place them in `data/cicids2017/engelen_latest/unlabeled`
4) Label the CSV files by running `data/cicids2017/labeling/cicids2017_liu_engelen_labeling_fixed.ipynb`
5) Merge the labeled files into a single `cicids2017.csv` file by navigating to `data/cicids2017/engelen_latest/` and running
```sh
uv run merge_csvs.py
```

## Reference

[1] Liu L, Engelen G, Lynar T, Essam D, Joosen W. Error prevalence in NIDS datasets: A case study on CIC-IDS-2017 and CSE-CIC-IDS-2018. In 2022 IEEE Conference on Communications and Network Security (CNS) 2022 Oct 3 (pp. 254-262). IEEE.

```bibtex
@inproceedings{liu2022error,
  title={Error prevalence in nids datasets: A case study on cic-ids-2017 and cse-cic-ids-2018},
  author={Liu, Lisa and Engelen, Gints and Lynar, Timothy and Essam, Daryl and Joosen, Wouter},
  booktitle={2022 IEEE conference on communications and network security (CNS)},
  pages={254--262},
  year={2022},
  organization={IEEE}
}
```