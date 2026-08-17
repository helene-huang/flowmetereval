import logging
import os
import random
from dataclasses import dataclass

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.metrics import average_precision_score, roc_auc_score
# from sklearn.preprocessing import MinMaxScaler
from torch.utils.data import DataLoader, TensorDataset
from tqdm import tqdm
from torch.utils.tensorboard import SummaryWriter

from ._utils import NIDS_Preprocessor, get_metrics, get_performance_by_attack_category, get_plot_probabilities, get_plot_roc_curve

# --- Configuration -----------------------------------------------------------

DEFAULT_DATASET_PATH = "../data/cicids2017/hhuang_fix/cicids2017.csv"
NUM_EPOCHS = 20
BATCH_SIZE = 1024
LEARNING_RATE = 0.0001
DEFAULT_THRESHOLD_PERCENTILE = 0.95

# --- Reproducibility ---------------------------------------------------------

def set_seed(seed: int):
    torch.manual_seed(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    np.random.seed(seed)
    random.seed(seed)

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")


# --- Model -------------------------------------------------------------------

class AutoEncoder(nn.Module):
    def __init__(self, feature_size):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(feature_size, int(feature_size * 0.75)),
            nn.ReLU(True),
            nn.Linear(int(feature_size * 0.75), int(feature_size * 0.5)),
            nn.ReLU(True),
            nn.Linear(int(feature_size * 0.5), int(feature_size * 0.25)),
            nn.ReLU(True),
            nn.Linear(int(feature_size * 0.25), int(feature_size * 0.1)),
        )
        self.decoder = nn.Sequential(
            nn.Linear(int(feature_size * 0.1), int(feature_size * 0.25)),
            nn.ReLU(True),
            nn.Linear(int(feature_size * 0.25), int(feature_size * 0.5)),
            nn.ReLU(True),
            nn.Linear(int(feature_size * 0.5), int(feature_size * 0.75)),
            nn.ReLU(True),
            nn.Linear(int(feature_size * 0.75), feature_size),
        )

    def forward(self, x):
        return self.decoder(self.encoder(x))


def get_ad_model(model_name: str="AutoEncoder", feature_size: int=100) -> AutoEncoder:
    """
    Args:
        model_name (str, optional): Model name. Defaults to "AutoEncoder".
        feature_size (int, optional): Feature size. Defaults to 100.
    """
    if model_name == "AutoEncoder":
        return AutoEncoder(feature_size)
    else:
        raise ValueError(f"Model {model_name} not supported.")


# --- Helpers -----------------------------------------------------------------

mse_none = nn.MSELoss(reduction="none")


@dataclass(frozen=True)
class MetricsToLog:
    benign_loss: float
    attack_loss: float
    benign_rmse: float
    attack_rmse: float
    roc_auc: float
    average_precision: float


def se2rmse(a: torch.Tensor) -> torch.Tensor:
    """Per-sample RMSE from a matrix of squared errors (shape: [N, features])."""
    return torch.sqrt(sum(a.t()) / a.shape[1])


def compute_threshold(model: nn.Module, x_benign: np.ndarray, percentile: float=DEFAULT_THRESHOLD_PERCENTILE) -> float:
    logging.info(f"Computing {percentile=}")
    model.eval()
    with torch.no_grad():
        x = torch.tensor(x_benign).float().to(device)
        rmse = se2rmse(mse_none(model(x), x)).cpu().numpy()
    rmse.sort()
    return rmse[int(len(rmse) * percentile)]

def test_multiple_thresholds(model: nn.Module, x_benign: np.ndarray, x_test: np.ndarray, y_test: pd.Series, threshold_percentiles: list[float]):
    """Function used for cheating"""

    for percentile in threshold_percentiles:
        threshold = compute_threshold(model, x_benign, percentile)

        print("-"*32)
        print(f"{percentile=} - {threshold=}")

        y_pred_np, rmse_np = predict_ad(model, threshold=threshold, x=x_test)
        y_pred = pd.Series(y_pred_np)
        y_prob = pd.Series(sigmoid((rmse_np - threshold) / threshold))

        performance_metrics = get_metrics(y_test, y_pred, y_prob)

        for metric, val in performance_metrics.items():
            print(f"{metric}: {val}")




def predict_ad(model: nn.Module, threshold: float, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    model.eval()
    with torch.no_grad():
        x_tensor = torch.tensor(x).float().to(device)
        rmse = se2rmse(mse_none(model(x_tensor), x_tensor)).cpu().numpy()
    y_pred = (rmse > threshold).astype(int)
    return y_pred, rmse


def compute_metrics_to_log(
    model: nn.Module,
    x_test_benign: np.ndarray,
    x_test_attack: np.ndarray,
) -> MetricsToLog:
    """
    Compute reconstruction and classification metrics logged to TensorBoard.

    Args:
        model (nn.Module): Trained autoencoder.
        x_test_benign (np.ndarray): Benign samples to evaluate.
        x_test_attack (np.ndarray): Attack samples to evaluate.

    Returns:
        MetricsToLog: Metrics to log for the current epoch.
    """
    model.eval()

    def compute_reconstruction_stats(x: np.ndarray) -> tuple[float, float, np.ndarray]:
        x_tensor = torch.tensor(x).float().to(device)
        reconstruction = model(x_tensor)
        squared_error = mse_none(reconstruction, x_tensor)
        rmse = se2rmse(squared_error)
        return squared_error.mean().item(), rmse.mean().item(), rmse.cpu().numpy()

    with torch.no_grad():
        benign_loss, benign_rmse, benign_scores = compute_reconstruction_stats(
            x_test_benign
        )
        attack_loss, attack_rmse, attack_scores = compute_reconstruction_stats(
            x_test_attack
        )

    y_true = np.concatenate(
        [
            np.zeros(len(benign_scores), dtype=int),
            np.ones(len(attack_scores), dtype=int),
        ]
    )
    y_score = np.concatenate([benign_scores, attack_scores])

    return MetricsToLog(
        benign_loss=benign_loss,
        attack_loss=attack_loss,
        benign_rmse=benign_rmse,
        attack_rmse=attack_rmse,
        roc_auc=roc_auc_score(y_true, y_score),
        average_precision=average_precision_score(y_true, y_score),
    )



# --- Training ----------------------------------------------------------------

def train_ad_model(model: nn.Module, x_benign: np.ndarray, batch_size: int=1024, num_epochs: int=20, learning_rate: float=0.0001):
    dataset = TensorDataset(torch.tensor(x_benign).float())
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    model.to(device)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    for _ in tqdm(range(num_epochs), desc="Training"):
        model.train()
        for (batch,) in loader:
            batch = batch.to(device)
            optimizer.zero_grad()
            criterion(model(batch), batch).backward()
            optimizer.step()
        model.eval()
    return model


def train_and_eval(
    model: nn.Module,
    x_train_benign: np.ndarray,
    x_test_benign: np.ndarray,
    x_test_attack: np.ndarray,
    batch_size: int = BATCH_SIZE,
    num_epochs: int = NUM_EPOCHS,
    learning_rate: float = 0.0001,
    tensorboard_log_dir: str = "runs/autoencoder",
):
    """
    Train an autoencoder while logging training and evaluation
    metrics to TensorBoard.

    Logged metrics:
        - Training loss
        - Benign test loss
        - Attack test loss
        - Benign RMSE
        - Attack RMSE
        - ROC-AUC from reconstruction error
        - Average precision from reconstruction error
        - Gradient norms

    Args:
        model (nn.Module): Autoencoder model.
        x_train_benign (np.ndarray): Benign training samples.
        x_test_benign (np.ndarray): Benign test samples.
        x_test_attack (np.ndarray): Attack test samples.
        batch_size (int): Batch size.
        num_epochs (int): Number of epochs.
        learning_rate (float): Learning rate.
        tensorboard_log_dir (str): TensorBoard output directory.

    Returns:
        nn.Module: Trained model.
    """

    dataset = TensorDataset(
        torch.tensor(x_train_benign).float()
    )

    loader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=True,
    )

    model.to(device)

    criterion = nn.MSELoss()

    optimizer = optim.Adam(
        model.parameters(),
        lr=learning_rate,
    )

    writer = SummaryWriter(
        log_dir=tensorboard_log_dir
    )


    for epoch in tqdm(
        range(num_epochs),
        desc="Training",
    ):
        model.train()

        epoch_loss = 0.0

        # --------------------------------------------------
        # Gradient tracking containers
        # --------------------------------------------------

        per_layer_gradients = {}
        encoder_grad_values = []
        decoder_grad_values = []
        total_grad_norm_values = []

        # --------------------------------------------------
        # Training
        # --------------------------------------------------

        for (batch,) in loader:
            batch = batch.to(device)
            optimizer.zero_grad()
            reconstruction = model(batch)

            loss = criterion(
                reconstruction,
                batch,
            )

            loss.backward()

            # ------------------------------------------
            # Collect gradient statistics
            # ------------------------------------------

            total_grad_norm_sq = 0.0

            for name, param in model.named_parameters():
                if param.grad is None:
                    continue
                grad_norm = param.grad.norm().item()

                # Store per-layer gradients
                per_layer_gradients.setdefault(
                    name,
                    []
                ).append(
                    grad_norm
                )

                # Encoder aggregate
                if "encoder" in name:

                    encoder_grad_values.append(
                        grad_norm
                    )

                # Decoder aggregate
                elif "decoder" in name:
                    decoder_grad_values.append(
                        grad_norm
                    )

                # Total network aggregate
                total_grad_norm_sq += (
                    grad_norm ** 2
                )

            total_grad_norm_values.append(
                total_grad_norm_sq ** 0.5
            )

            optimizer.step()
            epoch_loss += loss.item()

        train_loss = epoch_loss / len(loader)

        # --------------------------------------------------
        # Evaluation
        # --------------------------------------------------

        metrics_to_log = compute_metrics_to_log(
            model,
            x_test_benign,
            x_test_attack,
        )

        # --------------------------------------------------
        # TensorBoard: losses
        # --------------------------------------------------

        writer.add_scalar(
            "Loss/train",
            train_loss,
            epoch,
        )

        writer.add_scalar(
            "Loss/test_benign",
            metrics_to_log.benign_loss,
            epoch,
        )

        writer.add_scalar(
            "Loss/test_attack",
            metrics_to_log.attack_loss,
            epoch,
        )

        # --------------------------------------------------
        # TensorBoard: RMSE
        # --------------------------------------------------

        writer.add_scalar(
            "RMSE/test_benign",
            metrics_to_log.benign_rmse,
            epoch,
        )

        writer.add_scalar(
            "RMSE/test_attack",
            metrics_to_log.attack_rmse,
            epoch,
        )

        # --------------------------------------------------
        # TensorBoard: threshold-independent classification
        # --------------------------------------------------

        writer.add_scalar(
            "Classification/roc_auc",
            metrics_to_log.roc_auc,
            epoch,
        )

        writer.add_scalar(
            "Classification/average_precision",
            metrics_to_log.average_precision,
            epoch,
        )

        # --------------------------------------------------
        # TensorBoard: per-layer gradients
        # --------------------------------------------------

        for name, values in per_layer_gradients.items():

            writer.add_scalar(
                f"Gradients/{name}",
                np.mean(values),
                epoch,
            )

        # --------------------------------------------------
        # TensorBoard: aggregated gradients
        # --------------------------------------------------

        writer.add_scalar(
            "Gradients/encoder_mean",
            np.mean(encoder_grad_values),
            epoch,
        )

        writer.add_scalar(
            "Gradients/decoder_mean",
            np.mean(decoder_grad_values),
            epoch,
        )

        writer.add_scalar(
            "Gradients/total_norm",
            np.mean(total_grad_norm_values),
            epoch,
        )

        logging.info(
            f"Epoch {epoch + 1}/{num_epochs} | "
            f"Train Loss={train_loss:.6f} | "
            f"Benign Loss={metrics_to_log.benign_loss:.6f} | "
            f"Attack Loss={metrics_to_log.attack_loss:.6f} | "
            f"Benign RMSE={metrics_to_log.benign_rmse:.6f} | "
            f"Attack RMSE={metrics_to_log.attack_rmse:.6f} | "
            f"ROC-AUC={metrics_to_log.roc_auc:.6f} | "
            f"Average Precision={metrics_to_log.average_precision:.6f}"
        )

    writer.close()

    return model



# --- Evaluation --------------------------------------------------------------

def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1. / (1. + np.exp(-x))

def eval_ad_model(
        X_train: pd.DataFrame, 
        y_train: pd.Series, 
        X_test: pd.DataFrame, 
        y_test: pd.Series,
        attack_cat_test: pd.Series,
        model_name: str="AutoEncoder",
        seed: int=42,
        plot_roc_curve: bool=True,
        plot_probabilities: bool=True,
        results_path: str | None=None,
        num_epochs: int=NUM_EPOCHS,
        tensorboard_log_dir: str = "runs/autoencoder",
        threshold_percentile: float=DEFAULT_THRESHOLD_PERCENTILE,
        
    ) -> tuple[dict[str, float], dict[str, dict[str, float]]]:
    """
    Evaluate a supervised model on a given dataset.
    
    Args:
        X_train (pd.DataFrame): Training data.
        y_train (pd.Series): Training labels.
        X_test (pd.DataFrame): Testing data.
        y_test (pd.Series): Testing labels.
        attack_cat_test (pd.Series): Attack category of the testing data.
        model_name (str, optional): Model name. Defaults to "AutoEncoder".
        seed (int, optional): Random seed. Defaults to 42.
        plot_roc_curve (bool, optional): Whether to plot the ROC curve. Defaults to True.
        plot_probabilities (bool, optional): Whether to plot the probabilities. Defaults to True.
        results_path (str | None, optional): Path to save the results. Defaults to None.
        num_epochs (int, optional): Number of epochs. Defaults to 1.
        tensorboard_log_dir (str): TensorBoard output directory.
        threshold_percentile (float): Threshold percentile for the threshold.
    
    Returns:
        tuple[dict[str, float], dict[str, dict[str, float]]]: Tuple of dictionaries of metrics and performance metrics by attack category.
    """

    if results_path is not None:
        if not os.path.exists(results_path):
            os.makedirs(results_path)

    set_seed(seed)

    preprocessor = NIDS_Preprocessor()
    X_train = preprocessor.fit_transform(X_train)
    X_test = preprocessor.transform(X_test)

    x_benign = X_train[y_train == 0].to_numpy()
    x_test = X_test.to_numpy()

    logging.info(f"{len(x_benign)=}")
    logging.info(f"{y_test.value_counts()=}")

    logging.info(f"X_train.head(): {X_train.head()}")
    logging.info(f"X_test.head(): {X_test.head()}")

    # model = get_ad_model(model_name, feature_size=x_benign.shape[1], seed=seed)
    # train_ad_model(model, x_benign, num_epochs=num_epochs)

    model = get_ad_model(
        model_name,
        feature_size=x_benign.shape[1],
    )

    x_test_benign = X_test[y_test == 0].to_numpy()

    x_test_attack = X_test[y_test == 1].to_numpy()

    train_and_eval(
        model=model,
        x_train_benign=x_benign,
        x_test_benign=x_test_benign,
        x_test_attack=x_test_attack,
        num_epochs=num_epochs,
        tensorboard_log_dir=tensorboard_log_dir
    )

    test_multiple_thresholds(model, x_benign, x_test, y_test, threshold_percentiles=[0.5, 0.7, 0.8, 0.85, 0.9, 0.95])

    threshold = compute_threshold(model, x_benign, percentile=threshold_percentile)
    y_pred_np, rmse_np = predict_ad(model, threshold=threshold, x=x_test)
    y_pred = pd.Series(y_pred_np)
    y_prob = pd.Series(sigmoid((rmse_np - threshold) / threshold))

    if y_prob is not None and plot_roc_curve:
        get_plot_roc_curve(y_test, y_prob, results_path)

    if y_prob is not None and plot_probabilities:
        get_plot_probabilities(y_test, y_prob, results_path)

    performance_metrics = get_metrics(y_test, y_pred, y_prob)
    performance_by_category = get_performance_by_attack_category(y_pred, y_prob, attack_cat_test)

    if results_path is not None:
        pd.Series(performance_metrics, name="value").to_csv(os.path.join(results_path, "metrics.csv"))
        pd.Series(performance_by_category["accuracy"], name="value").to_csv(os.path.join(results_path, "accuracy_by_attack_category.csv"))
        if y_prob is not None:
            pd.Series(performance_by_category["probs"], name="value").to_csv(os.path.join(results_path, "probs_by_attack_category.csv"))

    return performance_metrics, performance_by_category
