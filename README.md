# Correcting CICFlowMeter Features for Interpretable NIDS Evaluation

This repository contains the code for reproducing the paper
"When Packet Length Is Not Packet Length: Correcting CICFlowMeter Features for Interpretable NIDS Evaluation"
by Huang et al.


## Clone submodules

```sh
git submodule update --init --recursive
```

## Install dependencies

Using [uv](https://github.com/astral-sh/uv):

```sh
uv sync --all-extras
```

## Data acquisition

See [./data/README.md](./data/README.md)

## Run small experiment

Useful to verify that everything is set up correctly:

```sh
sh scripts/experiments/small_experiment.sh
```

## Reproduce results of the paper

1) Run the experiment scripts (this takes a long time):
```sh
sh scripts/experiments/experiment_cicids2017_rf.sh
sh scripts/experiments/experiment_cicids2017_ae.sh
sh scripts/experiments/experiment_insdn_rf.sh
sh scripts/experiments/experiment_insdn_ae.sh
```

2) Obtain global results:
```sh
uv run analysis/analyze_results.py --result-dir ./results/rf --dataset cicids2017
uv run analysis/analyze_results.py --result-dir ./results/ae --dataset cicids2017
uv run analysis/analyze_results.py --result-dir ./results/rf --dataset insdn
uv run analysis/analyze_results.py --result-dir ./results/ae --dataset insdn
```

3) Calculate performance statistics shown in Tables 5 and 6 of the paper:

```sh
uv run analysis/generate_overall_results_table.py --result-dir ./results/rf
uv run analysis/generate_overall_results_table.py --result-dir ./results/ae
```

4) Calculate p-values for significance in Tables 5 and 6 of the paper:

```sh
uv run analysis/get_pval_pivot_table.py --result-dir ./results/rf
uv run analysis/get_pval_pivot_table.py --result-dir ./results/ae
```

### Reference

```bibtex
@inproceedings{huang2026packet,
  title={When Packet Length Is Not Packet Length: Correcting CICFlowMeter Features for Interpretable NIDS Evaluation},
  author={Huang, Hélène and Bois, Sébastien and Marchioro, Thomas},
  booktitle={European Symposium on Research in Computer Security},
  year={2026},
  organization={Springer}
}
```