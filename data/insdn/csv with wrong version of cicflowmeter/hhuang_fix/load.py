from pathlib import Path
import polars as pl
import pandas as pd

from data.insdn.engelen_latest.load import FEATURE_COLUMNS_DUPS, FEATURE_COLUMNS_NO_DUPS

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




FEATURE_COLUMNS: list[str] = [
    'Dst Port', 
    'Protocol', 
    'Flow Duration', 
    'Total Fwd Packet', 
    'Total Bwd packets', 
    'Fwd Segment Payload Length Total',
    'Bwd Segment Payload Length Total',
    'Fwd Segment Payload Length Max', 
    'Fwd Segment Payload Length Min', 
    'Fwd Segment Payload Length Mean', 
    'Fwd Segment Payload Length Std', 
    'Bwd Segment Payload Length Max', 
    'Bwd Segment Payload Length Min', 
    'Bwd Segment Payload Length Mean', 
    'Bwd Segment Payload Length Std', 
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
    'Segment Payload Length Min', 
    'Segment Payload Length Max', 
    'Segment Payload Length Mean', 
    'Segment Payload Length Std',
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
    'Fwd Segment Header Length Min',
    'Bwd Segment Header Length Min',
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

def load_insdn_hhuang_fix(feature_list: list[str] | None=None) -> tuple[pd.DataFrame, pd.Series, pd.Series]:

    csv_path: Path = CURRENT_DIR / "insdn.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"File {csv_path} does not exist.")

    df: pl.DataFrame = pl.read_csv(csv_path)

    df = df.sort(by=[TIMESTAMP_COLUMN])
    
    df_ = df.to_pandas()

    # these are added to assess the impact of feature duplication
    if "Segment Payload Length Variance" in feature_list:
        df_.loc[:,"Segment Payload Length Variance"] = df_["Segment Payload Length Std"]**2

    if "Segment Payload Length Avg" in feature_list:
        df_.loc[:, "Segment Payload Length Avg"] = df_["Segment Payload Length Mean"]
    
    if "Fwd Segment Payload Length Avg" in feature_list:
        df_.loc[:, "Fwd Segment Payload Length Avg"] = df_["Fwd Segment Payload Length Mean"]

    if "Bwd Segment Payload Length Avg" in feature_list:
        df_.loc[:, "Bwd Segment Payload Length Avg"] = df_["Bwd Segment Payload Length Mean"]

    feature_list = feature_list or FEATURE_COLUMNS

    X: pd.DataFrame = df_[feature_list]
    #X: pd.DataFrame = df.select(FEATURE_COLUMNS).with_columns((pl.col('Segment Payload Length Std')**2).alias('Segment Payload Length Std 2')).to_pandas()
    attack_labels: pd.Series = df_[LABEL_COLUMN]
    y: pd.Series = pd.Series(1*(attack_labels != "BENIGN"))

    return X, y, attack_labels


