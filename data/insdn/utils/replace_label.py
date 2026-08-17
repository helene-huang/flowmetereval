import pandas as pd
from pathlib import Path
from argparse import ArgumentParser

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('input_folder')
    args = parser.parse_args()
    input_folder = Path(args.input_folder)

    for f in input_folder.rglob("*.csv"):
        df = pd.read_csv(f)
        df['Label'] = df['Label'].apply(lambda x : 'U2R' if x == 'R2L' else x)
        df.to_csv(f, index=False)