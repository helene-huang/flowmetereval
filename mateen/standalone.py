import argparse
import random

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.metrics import (
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.preprocessing import MinMaxScaler
from torch.utils.data import DataLoader, TensorDataset
from tqdm import tqdm

# --- Configuration -----------------------------------------------------------

#DEFAULT_DATASET_PATH = "../data/cicids2017/engelen_paper/cicids2017.csv"
DEFAULT_DATASET_PATH = "../data/cicids2017/hhuang_fix/cicids2017.csv"
TRAIN_SIZE = 693702
DEFAULT_SEED = 0
NUM_EPOCHS = 20
BATCH_SIZE = 1024
LEARNING_RATE = 0.0001
THRESHOLD_PERCENTILE = 0.95
DROP_NEW_FEATURES = True

# --- Reproducibility ---------------------------------------------------------

def set_seed(seed: int):
    torch.manual_seed(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    np.random.seed(seed)
    random.seed(seed)

device = "cuda" if torch.cuda.is_available() else "cpu"


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


# --- Helpers -----------------------------------------------------------------

mse_none = nn.MSELoss(reduction="none")


def se2rmse(a):
    """Per-sample RMSE from a matrix of squared errors (shape: [N, features])."""
    return torch.sqrt(sum(a.t()) / a.shape[1])


def compute_threshold(model, x_benign):
    model.eval()
    with torch.no_grad():
        x = torch.tensor(x_benign).float().to(device)
        rmse = se2rmse(mse_none(model(x), x)).cpu().numpy()
    rmse.sort()
    return rmse[int(len(rmse) * THRESHOLD_PERCENTILE)]


def predict(model, threshold, x):
    model.eval()
    with torch.no_grad():
        x_tensor = torch.tensor(x).float().to(device)
        rmse = se2rmse(mse_none(model(x_tensor), x_tensor)).cpu().numpy()
    y_pred = (rmse > threshold).astype(int)
    return y_pred, rmse


# --- Data --------------------------------------------------------------------

def load_data(dataset_path: str):
    print("Loading dataset...")
    df = pd.read_csv(dataset_path)
    df = df.drop(columns=[
        "id", "Flow ID", "Src IP", "Src Port", "Dst IP", "Timestamp", "Attempted Category"
        ], 
        errors="ignore"
    )

    if DROP_NEW_FEATURES:
        df = df.drop(
            columns=[
                'Fwd Segment Payload Length Max', 
                'Fwd Segment Payload Length Min', 
                'Fwd Segment Payload Length Mean', 
                'Fwd Segment Payload Length Std', 
                'Bwd Segment Payload Length Max', 
                'Bwd Segment Payload Length Min', 
                'Bwd Segment Payload Length Mean', 
                'Bwd Segment Payload Length Std', 
                'Segment Payload Length Max', 
                'Segment Payload Length Min', 
                'Segment Payload Length Mean', 
                'Segment Payload Length Std'
            ], 
            errors='ignore')
    df["Label"] = (~df["Label"].str.contains("BENIGN")).astype(int)

    train = df.iloc[:TRAIN_SIZE]
    test = df.iloc[TRAIN_SIZE:]

    y_train = np.array(train["Label"])
    y_test = np.array(test["Label"])
    x_train = np.nan_to_num(train.drop("Label", axis=1).astype(float).values)
    x_test = np.nan_to_num(test.drop("Label", axis=1).astype(float).values)

    scaler = MinMaxScaler().fit(x_train)
    x_train = scaler.transform(x_train)
    x_test = scaler.transform(x_test)

    print(f"Train: {len(x_train)} samples | Test: {len(x_test)} samples")
    return x_train, x_test, y_train, y_test


# --- Training ----------------------------------------------------------------

def train(model, x_benign):
    dataset = TensorDataset(torch.tensor(x_benign).float())
    loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)
    model.to(device)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    for _ in tqdm(range(NUM_EPOCHS), desc="Training"):
        model.train()
        for (batch,) in loader:
            batch = batch.to(device)
            optimizer.zero_grad()
            criterion(model(batch), batch).backward()
            optimizer.step()
        model.eval()
    return model


# --- Evaluation --------------------------------------------------------------

def evaluate(y_true, y_pred, probs):
    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel()

    accuracy = (tp + tn) / (tp + tn + fp + fn) * 100
    precision = tp / (tp + fp) * 100 if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) * 100 if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    tnr = tn / (tn + fp) * 100 if (tn + fp) > 0 else 0.0
    tpr = tp / (tp + fn) * 100 if (tp + fn) > 0 else 0.0
    macro_recall = recall_score(y_true, y_pred, average="macro") * 100
    macro_precision = precision_score(y_true, y_pred, average="macro") * 100
    macro_f1 = f1_score(y_true, y_pred, average="macro") * 100
    balanced_acc = balanced_accuracy_score(y_true, y_pred) * 100
    auc_roc = roc_auc_score(y_true, probs)

    print(f"\nTP: {tp}  FP: {fp}  TN: {tn}  FN: {fn}")
    print(f"Accuracy:           {accuracy:.4f}%")
    print(f"Precision:          {precision:.4f}%")
    print(f"Recall (TPR):       {recall:.4f}%")
    print(f"F1 Score:           {f1:.4f}%")
    print(f"True Negative Rate: {tnr:.4f}%")
    print(f"True Positive Rate: {tpr:.4f}%")
    print(f"Macro Recall:       {macro_recall:.4f}%")
    print(f"Macro Precision:    {macro_precision:.4f}%")
    print(f"Macro F1:           {macro_f1:.4f}%")
    print(f"Balanced Accuracy:  {balanced_acc:.4f}%")
    print(f"AUC-ROC:            {auc_roc:.4f}")


# --- Main --------------------------------------------------------------------

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset_path", type=str, default=DEFAULT_DATASET_PATH)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()

    set_seed(args.seed)
    x_train, x_test, y_train, y_test = load_data(dataset_path=args.dataset_path)

    x_benign = x_train[y_train == 0]
    print(f"Benign training samples: {len(x_benign)}")

    model = AutoEncoder(feature_size=x_train.shape[1])
    model = train(model, x_benign)

    threshold = compute_threshold(model, x_benign)
    print(f"\nDetection threshold (p{int(THRESHOLD_PERCENTILE * 100)} on benign train RMSE): {threshold:.6f}")

    y_pred, probs = predict(model, threshold, x_test)
    evaluate(y_test, y_pred, probs)


if __name__ == "__main__":
    main()
