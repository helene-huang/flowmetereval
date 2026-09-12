"""
Copyright (C) 2026, CEA

This program is free software; you can redistribute it and/or modify
it under the terms of the Creative Commons Attribution-NonCommercial-ShareAlike 4.0
International License.

You should have received a copy of the license along with this
program. If not, see <https://creativecommons.org/licenses/by-nc-sa/4.0/>.
"""

import argparse
import logging
import os
from argparse import Namespace

import pandas as pd

from data.load import load_dataset
from data.utils import balance_dataset
from src.nids import eval_supervised_model, eval_ad_model

MODEL_CHOICES = ["rf", "ae"]

DATASET_CHOICES = [
    "cicids2017_engelen_paper",
    "cicids2017_engelen_latest", 
    "cicids2017_hhuang_fix",
    "insdn_engelen_latest", 
    "insdn_hhuang_fix",
]

DEFAULT_SEED = 0
DEFAULT_NUM_EPOCHS = 2

def get_args() -> Namespace:

    parser = argparse.ArgumentParser()
    parser.add_argument("model", type=str, choices=MODEL_CHOICES, help="Model to run.")
    parser.add_argument("dataset", type=str, choices=DATASET_CHOICES, help="Dataset to use.")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode.")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Random seed.")

    parser.add_argument("--feature_list_path", type=str, default="./feature_files/feature_file_example.txt", help="Path to the feature list file.")
    parser.add_argument("--epochs", type=int, default=DEFAULT_NUM_EPOCHS, help="Number of epochs (used only in `ad` experiments).")

    return parser.parse_args()


def read_feature_list(feature_list_path: str) -> list[str]:
    """
    Read a list of features from a file.

    Args:
        feature_list_path (str): Path to the feature list file.

    Returns:
        list[str]: List of features.
    """
    with open(feature_list_path, "r") as f:
        feature_list = [feature.strip() for feature in f.read().splitlines()]
    feature_list = [feature for feature in feature_list if not feature.startswith("#")]
    return feature_list


def temporal_split(X: pd.DataFrame, y: pd.Series, attack_cat: pd.Series, train_size: float):

    num_train: int = int(train_size * len(X))
    X_train = X.iloc[:num_train]
    y_train = y.iloc[:num_train]
    attack_cat_train = attack_cat.iloc[:num_train].reset_index(drop=True)

    X_test = X.iloc[num_train:].reset_index(drop=True)
    y_test = y.iloc[num_train:].reset_index(drop=True)
    attack_cat_test = attack_cat.iloc[num_train:].reset_index(drop=True)
    return X_train, X_test, y_train, y_test, attack_cat_train, attack_cat_test


def stratified_temporal_split(X: pd.DataFrame, y: pd.Series, attack_cat: pd.Series, train_size: float):
    """
    For each class independently, take the first 80% of its flows for train and the last 20% for test, preserving the original temporal order within each category.
    """
    _ = y  # silence warning

    X = X.reset_index(drop=True)
    attack_cat = attack_cat.reset_index(drop=True)

    attack_cat_group = attack_cat.groupby(
        attack_cat,
        sort=False, 
        dropna=False
    )

    within_category_positions = attack_cat_group.cumcount()

    category_size = attack_cat_group.transform("size")

    train_count = (category_size * train_size).astype(int)

    train_mask = within_category_positions < train_count
    test_mask =  ~train_mask

    y_binary = 1*(
        ~attack_cat.astype("string").str.lower().isin(["normal", "benign"])
    )

    X_train = X.loc[train_mask].reset_index(drop=True)
    X_test = X.loc[test_mask].reset_index(drop=True)

    y_train = y_binary.loc[train_mask].reset_index(drop=True)
    y_test = y_binary.loc[test_mask].reset_index(drop=True)

    attack_cat_train = attack_cat.loc[train_mask].reset_index(drop=True)
    attack_cat_test = attack_cat.loc[test_mask].reset_index(drop=True)

    return X_train, X_test, y_train, y_test, attack_cat_train, attack_cat_test


def get_results_path(dataset_name: str, seed: int, feature_list_path: str, root_path: str="results") -> str:
    """
    Get the results path for a given dataset, seed, and feature list path.
    Example: given dataset_name='cicids2017_engelen_paper', seed=0, feature_list_path='feature_file.txt', the results path will be 'cicids2017_engelen_paper_0_feature_file'.

    Args:
        dataset_name (str): Name of the dataset.
        seed (int): Random seed.
        feature_list_path (str): Path to the feature list file.

    Returns:
        str: Path to the results directory.
    """
    feature_file_name = os.path.basename(feature_list_path).split(".")[0]
    results_path = os.path.join(root_path, f"{dataset_name}", f"{feature_file_name}_seed{seed}")
    return results_path


def exp1_eval_supervised_model(seed: int, feature_list_path: str, dataset_name: str) -> None:
    """
    Scenario: 'Abundant' case with temporal split in Apruzzese et al. (2023) 'SoK: Pragmatic Assessment of Network Intrusion Detection Systems'
    """

    

    train_size: float = 0.8
    balance_train: bool = True
    
    logging.info(f"Loading dataset {dataset_name}.")
    
    feature_list: list[str] = read_feature_list(feature_list_path)
    logging.info(f"Feature list (input): {feature_list}")

    results_path = get_results_path(dataset_name, seed, feature_list_path)
    logging.debug(f"{results_path}")

    X, y, attack_cat = load_dataset(name=dataset_name, feature_list=feature_list)

    logging.debug(f"X features (should match feature_list): {X.columns.tolist()}")
    logging.debug(f"Label distribution: {attack_cat.value_counts()}")

    # X_train, X_test, y_train, y_test, attack_cat_train, attack_cat_test = temporal_split(X, y, attack_cat, train_size)
    X_train, X_test, y_train, y_test, attack_cat_train, attack_cat_test = stratified_temporal_split(X, y, attack_cat, train_size)
    
    if balance_train:
        logging.info("Balancing training data.")
        X_train, y_train = balance_dataset(X_train, y_train, seed=seed)


    logging.info(f"X_train.shape: {X_train.shape}")
    logging.info(f"y_train.shape: {y_train.shape}")
    logging.info(f"X_test.shape: {X_test.shape}")
    logging.info(f"y_test.shape: {y_test.shape}")

    logging.debug(f"X_train.head(): {X_train.head()}")
    logging.debug(f"y_train.head(): {y_train.head()}")
    logging.debug(f"X_test.head(): {X_test.head()}")
    logging.debug(f"y_train.value_counts(): {y_train.value_counts()}")
    logging.debug(f"{attack_cat_train.value_counts()=}")
    logging.debug(f"y_test.value_counts(): {y_test.value_counts()}")
    logging.debug(f"{attack_cat_test.value_counts()=}")

    performance_metrics, performance_by_category = eval_supervised_model(
        X_train, 
        y_train, 
        X_test, 
        y_test, 
        attack_cat_test, 
        model_name="RandomForest",
        seed=seed, 
        results_path=results_path,
        plot_roc_curve=True,
        plot_probabilities=True,
        compute_importances=True,
    )

    for metric_name, metric_value in performance_metrics.items():
        logging.info(f"{metric_name}: {metric_value}")

    for category, category_metrics in performance_by_category.items():
        for metric_name, metric_value in category_metrics.items():
            logging.info(f"{category} - {metric_name}: {metric_value}")


def exp2_eval_ad_model(seed: int, feature_list_path: str, dataset_name: str, num_epochs: int) -> None:


    logging.info(f"Loading dataset {dataset_name}.")
    
    feature_list: list[str] = read_feature_list(feature_list_path)
    logging.info(f"Feature list (input): {feature_list}")

    results_path = get_results_path(dataset_name, seed, feature_list_path, root_path="results_ad")

    X, y, attack_cat = load_dataset(name=dataset_name, feature_list=feature_list)

    logging.debug(f"X features (should match feature_list): {X.columns.tolist()}")
    logging.debug(f"Label distribution: {attack_cat.value_counts()}")


    if "insdn" in dataset_name.lower():  # NOTE: This is horrible but couldn't find a better solution :(
        X_benign = X[y == 0].reset_index(drop=True)
        y_benign = y[y == 0].reset_index(drop=True)  # this is equivalent to pd.Series(np.zeros(len(X_benign)))
        attack_cat_benign = attack_cat[y == 0].reset_index(drop=True) 
        X_attack = X[y != 0].reset_index(drop=True)
        y_attack = y[y != 0].reset_index(drop=True)
        attack_cat_attack = attack_cat[y != 0].reset_index(drop=True)

        train_size = 0.9
        num_train_benign = int(train_size*len(X_benign))

        X_train = X_benign[:num_train_benign]
        y_train = y_benign[:num_train_benign]
        attack_cat_train = attack_cat_benign[:num_train_benign]
        
        X_test_benign = X_benign[num_train_benign:]
        y_test_benign = y_benign[num_train_benign:]
        attack_cat_test_benign = attack_cat_benign[num_train_benign:]
        X_test = pd.concat((X_test_benign, X_attack), ignore_index=True)
        y_test = pd.concat((y_test_benign, y_attack), ignore_index=True)
        attack_cat_test = pd.concat((attack_cat_test_benign, attack_cat_attack), ignore_index=True)

        # percentile
        threshold_percentile = 0.8


    else:  # cicids2017
        num_train: int = 693702  # use same split as the Mateen paper
        X_train = X.iloc[:num_train]
        y_train = y.iloc[:num_train]

        X_test = X.iloc[num_train:].reset_index(drop=True)
        y_test = y.iloc[num_train:].reset_index(drop=True)
        attack_cat_test = attack_cat.iloc[num_train:].reset_index(drop=True)
        threshold_percentile = 0.95

    logging.info(f"X_train.shape: {X_train.shape}")
    logging.info(f"y_train.shape: {y_train.shape}")
    logging.info(f"X_test.shape: {X_test.shape}")
    logging.info(f"y_test.shape: {y_test.shape}")

    logging.debug(f"X_train.head(): {X_train.head()}")
    logging.debug(f"y_train.head(): {y_train.head()}")
    logging.debug(f"X_test.head(): {X_test.head()}")
    logging.debug(f"y_train.value_counts(): {y_train.value_counts()}")
    logging.debug(f"y_test.value_counts(): {y_test.value_counts()}")

    normalized_feature_list_path: str = str(feature_list_path.split("/")[-1].removesuffix(".txt"))

    tensorboard_log_dir: str = os.path.join("runs", f"{dataset_name}_config_{normalized_feature_list_path}_seed{seed}")
    logging.info(f"{tensorboard_log_dir=}")

    print(f"{results_path=}")
    performance_metrics, _ = eval_ad_model(
        X_train, 
        y_train, 
        X_test, 
        y_test, 
        attack_cat_test, 
        model_name="AutoEncoder",
        seed=seed, 
        results_path=results_path,
        plot_roc_curve=True,
        plot_probabilities=True,
        num_epochs=num_epochs,
        # tensorboard_log_dir=os.path.join("runs", results_path.split("/")[-1])
        tensorboard_log_dir=tensorboard_log_dir,
        threshold_percentile=threshold_percentile,
    )

    for metric_name, metric_value in performance_metrics.items():
        logging.info(f"{metric_name}: {metric_value}")




def main() -> None:

    args = get_args()

    # args -> variables for static type checking
    model_name: str = args.model
    dataset_name: str = args.dataset
    debug: bool = args.debug
    seed: int = args.seed
    feature_list_path: str = args.feature_list_path
    num_epochs: int = args.epochs

    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # disable matplotlib and PIL debug messages
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)
    if model_name == "rf":
        exp1_eval_supervised_model(seed, feature_list_path, dataset_name)
    elif model_name == "ae":
        exp2_eval_ad_model(seed, feature_list_path, dataset_name, num_epochs)
    else:
        raise ValueError(f"Unknown model: {model_name}")

if __name__ == "__main__":
    main()
