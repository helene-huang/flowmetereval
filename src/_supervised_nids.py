"""
Copyright (C) 2026, CEA

This program is free software; you can redistribute it and/or modify
it under the terms of the Creative Commons Attribution-NonCommercial-ShareAlike 4.0
International License.

You should have received a copy of the license along with this
program. If not, see <https://creativecommons.org/licenses/by-nc-sa/4.0/>.
"""

import logging
import os

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from ._utils import NIDS_Preprocessor, get_metrics, get_plot_roc_curve, get_plot_probabilities, get_performance_by_attack_category

# ============================================================
# Models
# ============================================================

def get_supervised_model(model_name: str="RandomForest", seed: int=42) -> RandomForestClassifier:
    """
    Default hyperparameters from: https://github.com/hihey54/pragmaticAssessment/blob/80b8691854cf5c04e054db9dfd11faead45b263e/pragmatic_assessment/evaluation/supportFunctions.py

    Args:
        model_name (str, optional): Model name. Defaults to "RandomForest".
        seed (int, optional): Random seed. Defaults to 42.
    """
    if model_name == "RandomForest":
        return RandomForestClassifier(
            n_estimators=200, 
            criterion='gini', 
            max_depth=None, 
            min_samples_split=2, 
            min_samples_leaf=1, 
            min_weight_fraction_leaf=0.0, 
            #max_features='auto', # auto was replaced by sqrt as default
            max_leaf_nodes=None, 
            min_impurity_decrease=0.0, 
            bootstrap=True, 
            oob_score=False, 
            n_jobs=-1, 
            verbose=0, 
            warm_start=False, 
            class_weight=None, 
            ccp_alpha=0.0, 
            max_samples=None,
            random_state=seed
        )
    else:
        raise ValueError(f"Model {model_name} not supported.")



# ============================================================
# Eval
# ============================================================

def eval_supervised_model(
        X_train: pd.DataFrame, 
        y_train: pd.Series, 
        X_test: pd.DataFrame, 
        y_test: pd.Series,
        attack_cat_test: pd.Series,
        model_name: str="RandomForest",
        seed: int=42,
        plot_roc_curve: bool=True,
        plot_probabilities: bool=True,
        compute_importances: bool=True,
        results_path: str | None=None,
    ) -> tuple[dict[str, float], dict[str, dict[str, float]]]:
    """
    Evaluate a supervised model on a given dataset.
    
    Args:
        X_train (pd.DataFrame): Training data.
        y_train (pd.Series): Training labels.
        X_test (pd.DataFrame): Testing data.
        y_test (pd.Series): Testing labels.
        attack_cat_test (pd.Series): Attack category of the testing data.
        model_name (str, optional): Model name. Defaults to "RandomForest".
        seed (int, optional): Random seed. Defaults to 42.
        plot_roc_curve (bool, optional): Whether to plot the ROC curve. Defaults to True.
        plot_probabilities (bool, optional): Whether to plot the probabilities. Defaults to True.
        compute_importances (bool, optional): Whether to compute feature importances. Defaults to True.
        results_path (str | None, optional): Path to save the results. Defaults to None.
    
    Returns:
        tuple[dict[str, float], dict[str, dict[str, float]]]: Tuple of dictionaries of metrics and performance metrics by attack category.
    """

    if results_path is not None:
        if not os.path.exists(results_path):
            os.makedirs(results_path)

    preprocessor = NIDS_Preprocessor()
    X_train = preprocessor.fit_transform(X_train)
    X_test = preprocessor.transform(X_test)

    logging.debug(f"X_train.head(): {X_train.head()}")
    logging.debug(f"X_test.head(): {X_test.head()}")

    model = get_supervised_model(model_name, seed)
    model.fit(X_train, y_train)
    y_pred = pd.Series(model.predict(X_test))

    probs = model.predict_proba(X_test)

    y_prob: pd.Series | None = None
    if isinstance(probs, np.ndarray):
        y_prob = pd.Series(probs[:, 1])
    else:
        logging.warning("Something went wrong with the prediction of probabilities.")
        logging.warning(f"Probs: {probs}")

    if y_prob is not None and plot_roc_curve:
        get_plot_roc_curve(y_test, y_prob, results_path)

    if y_prob is not None and plot_probabilities:
        get_plot_probabilities(y_test, y_prob, results_path)

    if compute_importances:
        if isinstance(model, RandomForestClassifier):
            importances = model.feature_importances_
            importances = pd.Series(importances, index=X_train.columns, name="importance")
            if results_path is not None:
                importances.to_csv(os.path.join(results_path, "feature_importances.csv"))

    performance_metrics = get_metrics(y_test, y_pred, y_prob)
    performance_by_category = get_performance_by_attack_category(y_pred, y_prob, attack_cat_test)

    if results_path is not None:
        pd.Series(performance_metrics, name="value").to_csv(os.path.join(results_path, "metrics.csv"))
        pd.Series(performance_by_category["accuracy"], name="value").to_csv(os.path.join(results_path, "accuracy_by_attack_category.csv"))
        if y_prob is not None:
            pd.Series(performance_by_category["probs"], name="value").to_csv(os.path.join(results_path, "probs_by_attack_category.csv"))

    return performance_metrics, performance_by_category


