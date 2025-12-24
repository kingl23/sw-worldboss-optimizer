from __future__ import annotations

import pandas as pd
import streamlit as st

from domain.siege_stats import build_offense_stats_by_defense, build_worst_offense_list as _build_worst_offense_list
from services.supabase_client import get_supabase_client


def _or_val(v: str) -> str:
    s = (v or "").strip()
    s = s.replace('"', r'\"')
    return f'"{s}"'


def _fetch_siege_rows(select_cols: str) -> list[dict]:
    client = get_supabase_client()

    rows: list[dict] = []
    page_size = 1000
    start = 0

    while True:
        res = (
            client
            .table("siege_logs")
            .select(select_cols)
            .in_("result", ["Win", "Lose"])
            .range(start, start + page_size - 1)
            .execute()
        )

        batch = res.data or []
        if not batch:
            break

        rows.extend(batch)

        if len(batch) < page_size:
            break

        start += page_size

    return rows


@st.cache_data(ttl=300)
def build_worst_offense_list(cutoff: int = 4) -> pd.DataFrame:
    rows = _fetch_siege_rows("result, deck2_1, deck2_2, deck2_3")
    return _build_worst_offense_list(rows, cutoff=cutoff)


@st.cache_data(ttl=300)
def get_offense_stats_by_defense(def1: str, def2: str, def3: str, limit: int = 50) -> pd.DataFrame:
    def1 = (def1 or "").strip()
    def2 = (def2 or "").strip()
    def3 = (def3 or "").strip()
    if not (def1 and def2 and def3):
        return pd.DataFrame()

    def_perms = [(def1, def2, def3), (def1, def3, def2)]

    q = (
        get_supabase_client()
        .table("siege_logs")
        .select("result, deck1_1,deck1_2,deck1_3, deck2_1,deck2_2,deck2_3")
        .in_("result", ["Win", "Lose"])
    )

    or_clauses = [
        f"and(deck2_1.eq.{_or_val(a)},deck2_2.eq.{_or_val(b)},deck2_3.eq.{_or_val(c)})"
        for a, b, c in def_perms
    ]
    q = q.or_(",".join(or_clauses))

    res = q.execute()
    df = pd.DataFrame(res.data or [])
    if df.empty:
        return df

    return build_offense_stats_by_defense(df, limit=limit)
