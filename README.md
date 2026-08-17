# Flowmeter Evaluation

Test suite for flowmeter evaluation.

## Clone submodules

```sh
git submodule update --init --recursive
```

## Install dependencies

Using [uv](https://github.com/astral-sh/uv):

```sh
uv sync --all-extras
```

## Download data 

### Original dataset ($D_{\text{base}}$) by Engelen et al.

Navigate to `./data/cicids2017/engelen_paper/` and run

```sh
get_data.sh
```

### Generate other versions of CIC-IDS dataset $D_{\text{latest}}$, $D_{\text{fix}}$, $D_{\text{ext}}$)

- Download raw PCAP files from the CIC website: [link](https://cicresearch.ca/CICDataset/CIC-IDS-2017/)
- Follow the instructions in the README file in 
    - `./data/cicids2017/engelen_latest/`
    

## Run code

### Simple experiment with RandomForests

```sh
uv run main.py --dataset <dataset_name>
```

Replace `<dataset_name>` with either of the following:
- `cicids2017_engelen_paper`
- `cicids2017_engelen_latest`
- `cicids2017_hhuang_fix`


### Pragmatic assessment

Run the notebooks in order (requires `jupyter`):

- [pragmatic_assessment/preprocessing_ids17.ipynb](pragmatic_assessment/preprocessing_ids17.ipynb)
- [pragmatic_assessment/assessment_IDS17.ipynb](pragmatic_assessment/assessment_IDS17.ipynb)

### Mateen (Anomaly detection)

Navigate to `./mateen/` and run

```sh
uv run standalone.py --dataset_path=../data/cicids2017/engelen_paper/cicids2017.csv
```
