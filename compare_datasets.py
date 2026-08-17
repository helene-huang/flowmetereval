from data.load import load_dataset

def main():

    
    X1, y1, _ = load_dataset(name="cicids2017_engelen_latest")
    X2, y2, _ = load_dataset(name="cicids2017_hhuang_fix")

    for col1, col2 in zip(X1.columns, X2.columns):
        print(f"{col1}, {col2}: {(X1[col1] - X2[col2]).abs().sum()}")

    print(f"y1 - y2: {(y1 - y2).abs().sum()}")


if __name__ == "__main__":
    main()
