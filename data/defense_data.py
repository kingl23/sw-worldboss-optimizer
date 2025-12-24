# data/defense_data.py
from __future__ import annotations

from typing import List
import pandas as pd

from domain.defense_stats import GUILD_GROUPS, make_def_key
from services.defense_service import (
    get_defense_deck_stats as _get_defense_deck_stats,
    get_defense_decks_vs_guild as _get_defense_decks_vs_guild,
    get_opp_guild_options as _get_opp_guild_options,
)

__all__ = [
    "GUILD_GROUPS",
    "make_def_key",
    "get_opp_guild_options",
    "get_defense_deck_stats",
    "get_defense_decks_vs_guild",
]


# -------------------------
# Public APIs (compat)
# -------------------------

def get_opp_guild_options() -> List[str]:
    """
    defense_logs에서 opp_guild 유니크 목록(전량 스캔).
    """
    return _get_opp_guild_options()


def get_defense_deck_stats(limit: int = 50) -> pd.DataFrame:
    return _get_defense_deck_stats(limit=limit)


def get_defense_decks_vs_guild(opp_guild: str, limit: int = 50) -> pd.DataFrame:
    return _get_defense_decks_vs_guild(opp_guild=opp_guild, limit=limit)
