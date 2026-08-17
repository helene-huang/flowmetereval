from pathlib import Path
import polars as pl
import pandas as pd

CURRENT_DIR: Path = Path(__file__).parent

FLOW_ID_COLUMN: str = 'Flow ID'

LABEL_COLUMN: str = 'Label'

DROP_COLUMNS: list[str] = [
    'id', 
    'Src IP',
    'Src Port',
    'Dst IP',
    'Timestamp',
    'Attempted Category'
]

TIMESTAMP_COLUMN: str = 'Timestamp'

# NOTE: Skill issue of previous experiment
FEATURE_COLUMNS_NO_DUPS: list[str] = [
    'Dst Port', 
    'Protocol', 
    'Flow Duration', 
    'Total Fwd Packet', 
    'Total Bwd packets', 
    'Total Length of Fwd Packet', 
    'Total Length of Bwd Packet', 
    'Fwd Packet Length Max', 
    'Fwd Packet Length Min', 
    'Fwd Packet Length Mean', 
    'Fwd Packet Length Std', 
    'Bwd Packet Length Max', 
    'Bwd Packet Length Min', 
    'Bwd Packet Length Mean', 
    'Bwd Packet Length Std', 
    'Flow Bytes/s', 
    'Flow Packets/s', 
    'Flow IAT Mean', 
    'Flow IAT Std', 
    'Flow IAT Max', 
    'Flow IAT Min', 
    'Fwd IAT Total', 
    'Fwd IAT Mean', 
    'Fwd IAT Std', 
    'Fwd IAT Max', 
    'Fwd IAT Min', 
    'Bwd IAT Total', 
    'Bwd IAT Mean', 
    'Bwd IAT Std', 
    'Bwd IAT Max', 
    'Bwd IAT Min', 
    'Fwd PSH Flags', 
    'Bwd PSH Flags', 
    'Fwd URG Flags', 
    'Bwd URG Flags', 
    'Fwd RST Flags', 
    'Bwd RST Flags', 
    'Fwd Header Length', 
    'Bwd Header Length', 
    'Fwd Packets/s', 
    'Bwd Packets/s', 
    'Packet Length Min', 
    'Packet Length Max', 
    'Packet Length Mean', 
    'Packet Length Std', 
    'FIN Flag Count', 
    'SYN Flag Count', 
    'RST Flag Count', 
    'PSH Flag Count', 
    'ACK Flag Count', 
    'URG Flag Count', 
    'CWR Flag Count', 
    'ECE Flag Count', 
    'Down/Up Ratio', 
    'Fwd Bytes/Bulk Avg', 
    'Fwd Packet/Bulk Avg', 
    'Fwd Bulk Rate Avg', 
    'Bwd Bytes/Bulk Avg', 
    'Bwd Packet/Bulk Avg', 
    'Bwd Bulk Rate Avg', 
    'Subflow Fwd Packets', 
    'Subflow Fwd Bytes', 
    'Subflow Bwd Packets', 
    'Subflow Bwd Bytes', 
    'FWD Init Win Bytes', 
    'Bwd Init Win Bytes', 
    'Fwd Act Data Pkts', 
    'Bwd Act Data Pkts', 
    'Fwd Seg Size Min', 
    'Bwd Seg Size Min', 
    'Active Mean', 
    'Active Std', 
    'Active Max', 
    'Active Min', 
    'Idle Mean', 
    'Idle Std', 
    'Idle Max', 
    'Idle Min', 
    'ICMP Code', 
    'ICMP Type', 
    'Fwd TCP Retrans. Count', 
    'Bwd TCP Retrans. Count', 
    'Total TCP Retrans. Count', 
    'Total Connection Flow Time', 
]

FEATURE_COLUMNS_DUPS: list[str] = [
    'Dst Port', 
    'Protocol', 
    'Flow Duration', 
    'Total Fwd Packet', 
    'Total Bwd packets', 
    'Total Length of Fwd Packet', 
    'Total Length of Bwd Packet', 
    'Fwd Packet Length Max', 
    'Fwd Packet Length Min', 
    'Fwd Packet Length Mean', 
    'Fwd Packet Length Std', 
    'Bwd Packet Length Max', 
    'Bwd Packet Length Min', 
    'Bwd Packet Length Mean', 
    'Bwd Packet Length Std', 
    'Flow Bytes/s', 
    'Flow Packets/s', 
    'Flow IAT Mean', 
    'Flow IAT Std', 
    'Flow IAT Max', 
    'Flow IAT Min', 
    'Fwd IAT Total', 
    'Fwd IAT Mean', 
    'Fwd IAT Std', 
    'Fwd IAT Max', 
    'Fwd IAT Min', 
    'Bwd IAT Total', 
    'Bwd IAT Mean', 
    'Bwd IAT Std', 
    'Bwd IAT Max', 
    'Bwd IAT Min', 
    'Fwd PSH Flags', 
    'Bwd PSH Flags', 
    'Fwd URG Flags', 
    'Bwd URG Flags', 
    'Fwd RST Flags', 
    'Bwd RST Flags', 
    'Fwd Header Length', 
    'Bwd Header Length', 
    'Fwd Packets/s', 
    'Bwd Packets/s', 
    'Packet Length Min', 
    'Packet Length Max', 
    'Packet Length Mean', 
    'Packet Length Std',
    'Packet Length Variance',
    'FIN Flag Count', 
    'SYN Flag Count', 
    'RST Flag Count', 
    'PSH Flag Count', 
    'ACK Flag Count', 
    'URG Flag Count', 
    'CWR Flag Count', 
    'ECE Flag Count', 
    'Down/Up Ratio',
    'Average Packet Size',
    'Fwd Segment Size Avg',
    'Bwd Segment Size Avg', 
    'Fwd Bytes/Bulk Avg', 
    'Fwd Packet/Bulk Avg', 
    'Fwd Bulk Rate Avg', 
    'Bwd Bytes/Bulk Avg', 
    'Bwd Packet/Bulk Avg', 
    'Bwd Bulk Rate Avg', 
    'Subflow Fwd Packets', 
    'Subflow Fwd Bytes', 
    'Subflow Bwd Packets', 
    'Subflow Bwd Bytes', 
    'FWD Init Win Bytes', 
    'Bwd Init Win Bytes', 
    'Fwd Act Data Pkts', 
    'Bwd Act Data Pkts', 
    'Fwd Seg Size Min', 
    'Bwd Seg Size Min', 
    'Active Mean', 
    'Active Std', 
    'Active Max', 
    'Active Min', 
    'Idle Mean', 
    'Idle Std', 
    'Idle Max', 
    'Idle Min', 
    'ICMP Code', 
    'ICMP Type', 
    'Fwd TCP Retrans. Count', 
    'Bwd TCP Retrans. Count', 
    'Total TCP Retrans. Count', 
    'Total Connection Flow Time', 
]


def load_insdn_engelen_latest() -> tuple[pd.DataFrame, pd.Series, pd.Series]:

    csv_path: Path = CURRENT_DIR / "insdn.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"File {csv_path} does not exist.")

    df: pl.DataFrame = pl.read_csv(csv_path)

    # df = df.with_columns(
    #     pl.col("Timestamp").str.to_datetime()
    # )

    # df = df.with_columns(
    #     pl.when(pl.col("Label") != "Normal")
    #     .then(pl.col("Timestamp") + pl.duration(days=10))
    #     .otherwise(pl.col("Timestamp"))
    #     .alias("Timestamp")
    # )

    df = df.sort(by=[TIMESTAMP_COLUMN])

    X: pd.DataFrame = df.select(FEATURE_COLUMNS_DUPS).to_pandas()

    attack_labels: pd.Series = df[LABEL_COLUMN].to_pandas()
    y: pd.Series = pd.Series(1*(attack_labels != "Normal"))

    return X, y, attack_labels


