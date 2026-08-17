import pandas as pd

def balance_dataset(X: pd.DataFrame, y: pd.Series, seed: int=42) -> tuple[pd.DataFrame, pd.Series]:
    """
    Rebalance the dataset by subsampling the benign/malicious samples to match the number of malicious/benign samples (downsample to whichever has the less flows).
    Useful for models that are sensitive to data imbalance (e.g. tree-based models).

    Args:
        X (pd.DataFrame): Dataframe of features.
        y (pd.Series): Series of labels.
        seed (int, optional): Random seed. Defaults to 42.

    Returns:
        tuple[pd.DataFrame, pd.Series]: Rebalanced dataset.
    """

    X_benign = X[y == 0]
    X_malicious = X[y == 1]

    if len(X_benign) > len(X_malicious):  
        X_benign = X_benign.sample(n=len(X_malicious), random_state=seed)
        X_benign = X_benign.sort_index()
    else:  
        X_malicious = X_malicious.sample(n=len(X_benign), random_state=seed)
        X_malicious = X_malicious.sort_index()

    X = pd.concat([X_benign, X_malicious], ignore_index=True)  # type: ignore
    assert isinstance(X, pd.DataFrame)
    y = pd.concat(
        [
            pd.Series([0] * len(X_benign)), 
            pd.Series([1] * len(X_malicious)),
        ], ignore_index=True)

    print(f"X.shape: {X.shape}")
    print(f"y.shape: {y.shape}")

    return X, y

