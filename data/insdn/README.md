# How to create InSDN CSVs

## Prerequisites
Ensure that the user has Docker permissions and that the service is running
```sh
sudo usermod -aG docker $USER
newgrp docker
sudo systemctl restart docker
```

Ensure that the user can read/write/execute all the files from this repository
```sh
cd ../..
chmod -R 777 .
```

## How to run
### Tutorial
NOTE: all the PCAP files must be at the root of the `./raw` directory.
Also, the script must be run from this directory to keep the relative path logic working.

To copy all the PCAP files from the nested directories of InSDN, you can do
```sh
cp ./raw/*/*/*.pcap ./raw
cp ./raw/*/*/*/*.pcap ./raw
```

To generate InSDN using the different versions of CICFlowMeter, you must load a configuration contained in a `.env` file.
```sh
./create_dataset.sh path/to/.env
```
The file must contain the following information:
* CIC_CONF: relative path to `.mk` file (root folder is /cicflowmeter)
* DATA_DIR: relative path to the folder that will contain the different stages of the dataset

### Detailed description
* First, each PCAP is loaded from `$DATA_DIR/raw`, fixed and reordered.
* Then, the CICFlowMeter image is built and run according to the configuration provided by `$CIC_CONF`. More details on these configurations can be found at this [link](../../cicflowmeter/README.md). The CSV files are generated in the folder `$DATA_DIR/unlabeled`.
* The files of `$DATA_DIR/unlabeled` are split into the following directories: `$DATA_DIR/unlabeled/OVS`, `$DATA_DIR/unlabeled/Normal`, `$DATA_DIR/unlabeled/metasploitable-2`.
* Based on the structure of the [original PCAP directory](https://aseados.ucd.ie/datasets/SDN/InSDN_PCAPS_Groups/), a label is assigned to each unique CSV, and the files are moved under `$DATA_DIR/labeled`.
* All the CSV files of the folders `$DATA_DIR/labeled/OVS`, `$DATA_DIR/labeled/Normal` and `$DATA_DIR/labeled/metasploitable-2` are used to produce the three CSVs `$DATA_DIR/final/OVS.csv`, `$DATA_DIR/final/Normal.csv` and `$DATA_DIR/final/metasploitable-2.csv`.
* Lastly, `$DATA_DIR/final/insdn.csv` is produced by merging the three previous CSV files.
### Assumptions made during extraction and preparation
Details of the original work were insufficient to reproduce that of Elsayed et al. exactly. Some assumptions had to be made to produce these versions of InSDN, which may explain the differences from the original work.
* The exact labeling approach and the accuracy of the labels are unknown: we assumed that PCAP files under a folder whose name refers to an attack contained only malicious traffic related to that attack.
* The version of CICFlowMeter used in the original work was unknown, so we were not able to reproduce the original datasets and confirm the correctness of our approach.
* No information was disclosed concerning the merging strategy of the different PCAP files: were majority classes sampled originally? Were tests performed on a single CSV file among Normal.csv, OVS.csv and metasploitable-2.csv, or were they merged into a single one (i.e., insdn.csv)? Using our approach, the number of DDoS flows increased strongly. This was to be expected, since a fixed version of CICFlowMeter was used, but the growth factor is large enough that we suspect the authors may have performed sampling in their original work.
* No information was disclosed about whether the data collected from the ONOS interfaces and the host interfaces were merged together: since we had no information on this point, we merged all the files, which led to several descriptions of the same traffic from different viewpoints.

Because of all these assumptions, we consider that our dataset might be very different from the original InSDN, even though the same PCAP files were used to generate it.
## How to load
```python
from data.load import load_dataset
X, y, _ = load_dataset('insdn_hhuang_fix')
```
## References
* Elsayed, M. S., Le-Khac, N. A., & Jurcut, A. D. (2020). InSDN: A novel SDN intrusion dataset. IEEE Access, 8, 165263-165284.
* https://aseados.ucd.ie/datasets/SDN/
