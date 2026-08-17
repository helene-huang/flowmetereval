import logging
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from sklearn.metrics import accuracy_score, recall_score, f1_score, roc_auc_score, roc_curve
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OrdinalEncoder, StandardScaler

# ============================================================
# Preprocessor
# ============================================================

class NIDS_Preprocessor:
    """
    NIDS_Preprocessor class for preprocessing data before training a model.

    Attributes:
        feature_columns (list[str]): List of feature columns.
        categorical_columns (list[str]): List of categorical columns, must be a subset of the feature columns. If this list is not passed to the constructor, categorical columns are inferred from the training data.
        encoder (OrdinalEncoder): OrdinalEncoder object for encoding categorical columns.
        scaler (StandardScaler): StandardScaler object for scaling numerical columns.
        is_fitted (bool): Flag indicating whether the NIDS_Preprocessor is fitted.

    Args:
        feature_columns (list[str]): List of feature columns.
        categorical_columns (list[str], Optional): Optional list of categorical columns, must be a subset of the feature columns. If None, categorical columns are inferred from the training data.
    """

    def __init__(
            self, 
            feature_columns: list[str] | None=None, 
            categorical_columns: list[str] | None=None
        ) -> None:
        """
        Args:
            feature_columns (list[str]): List of feature columns.
            categorical_columns (list[str], Optional): Optional list of categorical columns, must be a subset of the feature columns. If None, categorical columns are inferred from the training data.
        """

        self.feature_columns = feature_columns


        self.encoder = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)
        self.scaler = StandardScaler()

        self.categorical_columns = categorical_columns
        self.is_fitted = False


    def fit(self, X: pd.DataFrame):
        """
        Args:
            X (pd.DataFrame): data used to fit the NIDS_Preprocessor
        """
        X = X.copy()

        if self.feature_columns is None:
            self.feature_columns = X.columns

        X = X.reindex(columns=self.feature_columns)

        if self.categorical_columns is not None:
            assert set(self.categorical_columns).issubset(set(self.feature_columns))
        else:
            self.categorical_columns = self.find_non_numeric_columns(X)

        if len(self.categorical_columns) > 0:
            X[self.categorical_columns] = X[self.categorical_columns].astype(str)
            X[self.categorical_columns] = self.encoder.fit_transform(X[self.categorical_columns])

        X = X.astype(float)
        X = X.replace([np.inf, -np.inf], np.nan)
        X = X.fillna(0)
        self.scaler.fit(X)

        logging.debug(f"{self.__class__.__name__}: NIDS_Preprocessor feature columns: {self.feature_columns}")

        self.is_fitted = True
    
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Args:
            X (pd.DataFrame): data to be transformed.
        """
        assert self.is_fitted
        assert self.feature_columns is not None
        assert self.categorical_columns is not None

        X = X.copy()
        X = X.reindex(columns=self.feature_columns, fill_value=0)

        if len(self.categorical_columns) > 0:
            X[self.categorical_columns] = X[self.categorical_columns].astype(str)
            X[self.categorical_columns] = self.encoder.transform(X[self.categorical_columns])

        X = X.astype(float, errors='ignore')
        X = X.replace([np.inf, -np.inf], np.nan)
        X = X.fillna(0)
        X.iloc[:] = self.scaler.transform(X)
        return X

    def fit_transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Args:
            X (pd.DataFrame): data first used to fit the NIDS_Preprocessor and subsequently transformed.
        """
        self.fit(X)
        return self.transform(X)
    
    @staticmethod
    def find_non_numeric_columns(X: pd.DataFrame) -> list[str]:
        return [col for col in X.columns if not pd.api.types.is_numeric_dtype(X[col].dropna())]

# ============================================================
# Metrics
# ============================================================

def get_metrics(y_true: pd.Series, y_pred: pd.Series, y_prob: pd.Series | None=None) -> dict[str, float]:
    """
    Get metrics for a given set of predictions.

    Args:
        y_true (pd.Series): True labels.
        y_pred (pd.Series): Predicted labels.
        y_prob (pd.Series | None, optional): Predicted probabilities. Defaults to None.

    Returns:
        dict: Dictionary of metrics.
    """
    metrics = {
        "accuracy": accuracy_score(y_true, y_pred),
        "tpr": recall_score(y_true, y_pred),
        "fpr": 1.-recall_score(y_true, y_pred, pos_label=0),
        "f1": f1_score(y_true, y_pred),
    }
    if y_prob is not None:
        metrics["roc_auc"] = roc_auc_score(y_true, y_prob)

    return metrics

# ============================================================
# Plots
# ============================================================

def get_plot_roc_curve(y_true: pd.Series, y_prob: pd.Series, results_path: str | None=None) -> None:
    """
    Plot ROC curve.

    Args:
        y_true (pd.Series): True labels.
        y_prob (pd.Series): Predicted probabilities.
    """
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    auc = roc_auc_score(y_true, y_prob)

    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, label=f"AUC: {auc:.3f}")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve")
    plt.legend(loc="lower right")
    if results_path is not None:
        pd.DataFrame({"fpr": fpr, "tpr": tpr}).to_csv(os.path.join(results_path, "roc_curve.csv"), index=False)
        plt.savefig(os.path.join(results_path, "roc_curve.pdf"))
    plt.draw()


def get_plot_probabilities(y_true: pd.Series, y_prob: pd.Series, results_path: str | None=None) -> None:
    """
    Plot probabilities.

    Args:
        y_true (pd.Series): True labels.
        y_prob (pd.Series): Predicted probabilities.
    """

    prob_good = y_prob[y_true == 0]
    prob_bad = y_prob[y_true == 1]

    bins = np.linspace(0, 1, 100).tolist()

    plt.figure(figsize=(8, 6))
    plt.hist(prob_good, bins=bins, alpha=0.5, label="Good")
    plt.hist(prob_bad, bins=bins, alpha=0.5, label="Bad")
    plt.xlabel("Probability")
    plt.ylabel("Label")
    plt.title("Probabilities")
    plt.legend(loc="lower right")
    if results_path is not None:
        plt.savefig(os.path.join(results_path, "predicted_probabilities.pdf"))
    plt.draw()


def get_performance_by_attack_category(y_pred: pd.Series, y_prob: pd.Series | None, attack_cat: pd.Series) -> dict[str, dict[str, float]]:
    accuracy_by_attack_category = {}
    probs_by_attack_category = {}
    for attack_cat_value in attack_cat.unique():
        if attack_cat_value == "BENIGN":
            continue
        accuracy_by_attack_category[attack_cat_value] = y_pred[attack_cat == attack_cat_value].mean()
        if y_prob is not None:
            probs_by_attack_category[attack_cat_value] = y_prob[attack_cat == attack_cat_value].mean()
    performance_by_attack_category = {"accuracy": accuracy_by_attack_category}
    if y_prob is not None:
        performance_by_attack_category["probs"] = probs_by_attack_category
    return performance_by_attack_category

