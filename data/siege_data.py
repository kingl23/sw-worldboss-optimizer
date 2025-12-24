# data/siege_data.py
import pandas as pd

from domain.siege_stats import make_key_fixed
from services.siege_service import (
    build_worst_offense_list as _build_worst_offense_list,
    get_offense_stats_by_defense as _get_offense_stats_by_defense,
)

__all__ = [
    "make_key_fixed",
    "build_worst_offense_list",
    "get_offense_stats_by_defense",
]


def build_worst_offense_list(cutoff: int = 4) -> pd.DataFrame:
    return _build_worst_offense_list(cutoff=cutoff)


def get_offense_stats_by_defense(def1: str, def2: str, def3: str, limit: int = 50) -> pd.DataFrame:
    return _get_offense_stats_by_defense(def1=def1, def2=def2, def3=def3, limit=limit)
