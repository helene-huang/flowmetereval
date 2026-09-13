uv run run_experiment.py rf cicids2017_hhuang_fix --feature_list_path "./feature_files/engelen_no_duplicates.txt" --seed 1
uv run run_experiment.py rf cicids2017_hhuang_fix --feature_list_path "./feature_files/engelen_no_duplicates.txt" --seed 2

uv run run_experiment.py ae cicids2017_hhuang_fix --feature_list_path "./feature_files/engelen_no_duplicates.txt" --seed 1 --epochs 1
uv run run_experiment.py ae cicids2017_hhuang_fix --feature_list_path "./feature_files/engelen_no_duplicates.txt" --seed 2 --epochs 1
