# Mateen

This code was adapted from this [repository](https://github.com/ICL-ml4csec/Mateen/)

No copyright notice was provided for the original code.

Paper reference:
```
@inproceedings{alotaibi24mateen,
  title={Mateen: Adaptive Ensemble Learning for Network Anomaly Detection},
  author={Alotaibi, Fahad and Maffeis, Sergio},
  booktitle={the 27th International Symposium on Research in Attacks, Intrusions and Defenses (RAID 2024)},
  year={2024},
  organization={Association for Computing Machinery}
}
```

## Run standalone

```sh
uv run standalone.py --dataset_path ../data/cicids2017/engelen_paper/cicids2017.csv --seed 0
```

## Example output

```
Loading dataset...
Train: 693702 samples | Test: 1406274 samples
Benign training samples: 686730

Detection threshold (p95 on benign train RMSE): 0.029273

TP: 315993  FP: 44033  TN: 851803  FN: 194445
Accuracy:           83.0419%
Precision:          87.7695%
Recall (TPR):       61.9062%
F1 Score:           72.6033%
True Negative Rate: 95.0847%
True Positive Rate: 61.9062%
Macro Recall:       78.4955%
Macro Precision:    84.5923%
Macro F1:           80.1619%
Balanced Accuracy:  78.4955%
AUC-ROC:            0.9372
```
