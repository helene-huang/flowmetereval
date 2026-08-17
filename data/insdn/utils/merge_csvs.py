import pandas as pd
from argparse import ArgumentParser
from pathlib import Path


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("input_folder")
    parser.add_argument("output")
    parser.add_argument('-P', '--pattern')

    args = parser.parse_args()
    input_folder = args.input_folder
    output = args.output
    pattern = args.pattern

    if not pattern:
        pattern = '*'

    csv_files = list(Path(input_folder).rglob(f'{pattern}.csv'))
    merge = pd.concat([pd.read_csv(f) for f in csv_files], ignore_index=True)
    merge.to_csv(output, index=False)