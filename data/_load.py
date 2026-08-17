import pandas as pd

from .cicids2017.engelen_paper.load import load_cicids2017_engelen_paper
from .cicids2017.hhuang_fix.load import load_cicids2017_hhuang_fix
from .cicids2017.engelen_latest.load import load_cicids2017_engelen_latest

from .insdn.hhuang_fix.load import load_insdn_hhuang_fix
from .insdn.engelen_latest.load import load_insdn_engelen_latest

def load_dataset(name: str, feature_list: list[str] | None=None) -> tuple[pd.DataFrame, pd.Series, pd.Series]:

    if name == "cicids2017_engelen_paper":
        return load_cicids2017_engelen_paper()

    if name == "cicids2017_hhuang_fix":
        return load_cicids2017_hhuang_fix(feature_list=feature_list)

    if name == "cicids2017_engelen_latest":
        return load_cicids2017_engelen_latest()

    if name == "insdn_hhuang_fix":
        return load_insdn_hhuang_fix(feature_list=feature_list)

    if name == "insdn_engelen_latest":
        return load_insdn_engelen_latest()

    raise ValueError(f"Unknown dataset {name}")

