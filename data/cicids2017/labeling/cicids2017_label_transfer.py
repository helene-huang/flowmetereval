import argparse
import os
import pandas as pd


parser = argparse.ArgumentParser()
parser.add_argument("--path", type=str, default="../engelen_latest/")
args = parser.parse_args()

LABEL_PATH: str = "../engelen_paper/"
VERSION_PATH: str = args.path
UNLABELED_PATH: str = os.path.join(VERSION_PATH, "unlabeled")

labeled_files = ["monday.csv", "tuesday.csv", "wednesday.csv", "thursday.csv", "friday.csv"]
unlabeled_files = ["Monday-WorkingHours.pcap_Flow.csv", "Tuesday-WorkingHours.pcap_Flow.csv", "Wednesday-workingHours.pcap_Flow.csv", "Thursday-WorkingHours.pcap_Flow.csv", "Friday-WorkingHours.pcap_Flow.csv"]
# unlabeled_files = ["monday.csv", "tuesday.csv", "wednesday.csv", "thursday.csv", "friday.csv"]

# labeled_files = ["friday.csv"]
# unlabeled_files = ["friday.csv"]
# unlabeled_files = ["Friday-WorkingHours.pcap_Flow.csv"]


labeled_paths = [os.path.join(LABEL_PATH, file) for file in labeled_files]
unlabeled_paths = [os.path.join(UNLABELED_PATH, file) for file in unlabeled_files]

def transfer_labels(labeled_path: str, unlabeled_path: str):

    new_labeled_path = os.path.join(VERSION_PATH, os.path.basename(labeled_path))

    labeled_df = pd.read_csv(labeled_path, usecols=["Timestamp", "Flow ID", "Label"], low_memory=False)
    unlabeled_df = pd.read_csv(unlabeled_path, low_memory=False)
    #unlabeled_df = pd.read_csv(unlabeled_path, low_memory=False, on_bad_lines="skip", encoding_errors="replace")
    unlabeled_df = unlabeled_df.drop(columns=["Label"])
    labeled_df["GGID"] = labeled_df["Timestamp"] + labeled_df["Flow ID"]
    unlabeled_df["GGID"] = unlabeled_df["Timestamp"] + unlabeled_df["Flow ID"]

    #print(unlabeled_df["GGID"].head())
    #exit()

    print("Labeled dataframe shape:", labeled_df.shape)
    print("Unlabeled dataframe shape:", unlabeled_df.shape)

    # inner join on "Flow ID" and transfer "Label" column from labeled_df to unlabeled_df
    #new_labeled_df = labeled_df.merge(unlabeled_df, on="Flow ID", how="inner")
    mapping = labeled_df.drop_duplicates("GGID").set_index("GGID")["Label"]
    unlabeled_df["Label"] = unlabeled_df["GGID"].map(mapping)

    # count Nans in "Label" column
    nan_count = unlabeled_df["Label"].isna().sum()
    print("Number of NaNs in Label column:", nan_count)

    # drop rows with NaNs in "Label" column
    unlabeled_df = unlabeled_df.dropna(subset=["Label"])
    print("Unlabeled dataframe shape after dropping NaNs:", unlabeled_df.shape)
    unlabeled_df =unlabeled_df.drop(columns="GGID")

    new_labeled_df = unlabeled_df.copy()

    print("New labeled dataframe shape:", new_labeled_df.shape)
    print("Saving to path:", new_labeled_path)
    new_labeled_df.to_csv(new_labeled_path, index=False)


for labeled_path, unlabeled_path in zip(labeled_paths, unlabeled_paths):
    print("Labeled path: ", labeled_path)
    print("Unlabeled path: ", unlabeled_path)
    print("Transferring...")
    transfer_labels(labeled_path, unlabeled_path)


