from pathlib import Path

CURR_DIR: Path = Path(__file__).resolve().parent
filenames: list[str] = ["monday.csv", "tuesday.csv", "wednesday.csv", "thursday.csv", "friday.csv"]
filepaths: list[Path] = [CURR_DIR / filename for filename in filenames]
output_filepath: Path = CURR_DIR / "cicids2017.csv"

def main() -> None:
    """
    NOTE: This script assumes all csv files are in the root directory and have the same header
    """
    with open(output_filepath, "w") as output_file:
        for i, filepath in enumerate(filepaths):
            with open(filepath, "r") as input_file:
                for j, line in enumerate(input_file):
                    if i != 0 and j == 0:
                        # skip header for all but first file
                        continue
                    output_file.write(line)

if __name__ == '__main__':
    main()
