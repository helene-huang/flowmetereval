# CIC-IDS 2017 (Version released by Engelen et al. 2022)

The dataset can be downloaded at this [link](https://intrusion-detection.distrinet-research.be/CNS2022/Dataset_Download.html)

SHA256 checksum of the ZIP file:
```
97fdb91d339e2d8cf5627f981b831e5e7e400b981c58181c451a38fd03c48883  CICIDS2017_improved.zip
```

## Get merged CSV dataset

### From Linux (need `wget`, `unzip`, and `python3` installed)

From this directory, run:
```sh
sh get_dataset.sh
```
This script will download the ZIP file and extract it, then merge the CSV files into a single CSV file.


