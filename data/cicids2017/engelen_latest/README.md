# CICFlowmeter (Liu, Engelen et al.)

This version of CIC-IDS 2017 is extracted using the latest version of CICFlowmeter by Liu, Engelen, et al [1].

Link to the repo: https://github.com/GintsEngelen/CICFlowMeter

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

## Reference

[1] Liu L, Engelen G, Lynar T, Essam D, Joosen W. Error prevalence in nids datasets: A case study on cic-ids-2017 and cse-cic-ids-2018. In2022 IEEE conference on communications and network security (CNS) 2022 Oct 3 (pp. 254-262). IEEE.

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