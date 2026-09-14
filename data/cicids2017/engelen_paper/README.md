# CIC-IDS 2017 (version released by Liu, Engelen et al. 2022)

This version of CIC-IDS 2017 was extracted and labeled by Liu, Engelen et al. [1].

The dataset can be downloaded at this [link](https://intrusion-detection.distrinet-research.be/CNS2022/Dataset_Download.html).

SHA256 checksum of the ZIP file:
```
97fdb91d339e2d8cf5627f981b831e5e7e400b981c58181c451a38fd03c48883  CICIDS2017_improved.zip
```

## Get merged CSV dataset

### From Linux (requires `wget`, `unzip`, and `python3`)

From this directory, run:
```sh
sh get_dataset.sh
```
This script will download the ZIP file and extract it, then merge the CSV files into a single CSV file.


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