from __future__ import annotations

from typing import Iterable, List
import streamlit as st
import pandas as pd

from services.supabase_client import get_supabase_client
from domain.defense_stats import (
    GUILD_GROUPS,
    build_defense_deck_stats,
    build_defense_decks_vs_guild,
    build_opp_guild_options,
)


def _iter_defense_logs(select_cols: str, page_size: int = 1000) -> Iterable[dict]:
    client = get_supabase_client()
    start = 0

    while True:
        res = (
            client
            .table("defense_logs")
            .select(select_cols)
            .range(start, start + page_size - 1)
            .execute()
        )
        batch = res.data or []
        if not batch:
            break

        for row in batch:
            yield row

        if len(batch) < page_size:
            break
        start += page_size


def _iter_defense_logs_with_result(select_cols: str, page_size: int = 1000) -> Iterable[dict]:
    client = get_supabase_client()
    start = 0

    while True:
        res = (
            client
            .table("defense_logs")
            .select(select_cols)
            .in_("result", ["Win", "Lose"])
            .range(start, start + page_size - 1)
            .execute()
        )
        batch = res.data or []
        if not batch:
            break

        for row in batch:
            yield row

        if len(batch) < page_size:
            break
        start += page_size


def _iter_defense_logs_vs_guild(opp_guild: str, select_cols: str, page_size: int = 1000) -> Iterable[dict]:
    client = get_supabase_client()
    start = 0

    while True:
        res = (
            client
            .table("defense_logs")
            .select(select_cols)
            .eq("opp_guild", opp_guild)
            .in_("result", ["Win", "Lose"])
            .range(start, start + page_size - 1)
            .execute()
        )
        batch = res.data or []
        if not batch:
            break

        for row in batch:
            yield row

        if len(batch) < page_size:
            break
        start += page_size


# -------------------------
# Public APIs (cached)
# -------------------------
@st.cache_data(ttl=300)
def get_opp_guild_options() -> List[str]:
    """
    defense_logs에서 opp_guild 유니크 목록(전량 스캔).
    """
    rows = _iter_defense_logs("opp_guild")
    return build_opp_guild_options(rows)


@st.cache_data(ttl=300)
def get_defense_deck_stats(limit: int = 50) -> pd.DataFrame:
    """
    (항상 mode=1 포맷)
    반환 컬럼:
      d1,d2,d3, win,lose, win_rate,
      in32_win,in32_lose,in32_win_rate,
      in12_win,in12_lose,in12_win_rate,
      in4_win,in4_lose,in4_win_rate
    정렬:
      base win_rate desc, base total desc, def_key asc
    """
    rows = _iter_defense_logs_with_result(
        "result, opp_guild, deck1_1, deck1_2, deck1_3",
    )
    return build_defense_deck_stats(rows, limit=limit, guild_groups=GUILD_GROUPS)


@st.cache_data(ttl=300)
def get_defense_decks_vs_guild(opp_guild: str, limit: int = 50) -> pd.DataFrame:
    """
    특정 opp_guild 상대로 한 방덱 통계.
    반환 컬럼: d1,d2,d3, win,lose, win_rate
    """
    rows = _iter_defense_logs_vs_guild(
        opp_guild=opp_guild,
        select_cols="result, opp_guild, deck1_1, deck1_2, deck1_3",
    )
    return build_defense_decks_vs_guild(rows, opp_guild=opp_guild, limit=limit)
