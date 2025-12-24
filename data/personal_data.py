# data/personal_data.py
from __future__ import annotations

from typing import List

import pandas as pd
import streamlit as st
from supabase import create_client


# -------------------------
# Supabase
# -------------------------

def sb():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_ANON_KEY"],
    )


# -------------------------
# Key / Utils
# -------------------------

def make_deck_key(a: str, b: str, c: str) -> str:
    """
    a는 leader(고정), b/c는 순서 무관
    """
    a = (a or "").strip()
    b = (b or "").strip()
    c = (c or "").strip()

    if not a:
        return ""

    rest = sorted([x for x in [b, c] if x])
    if len(rest) != 2:
        return ""

    return "|".join([a] + rest)


def _format_team(r, a: str, b: str, c: str) -> str:
    parts = [r.get(a, ""), r.get(b, ""), r.get(c, "")]
    return " / ".join([p for p in parts if p])


# -------------------------
# Public APIs
# -------------------------

@st.cache_data(ttl=300)
def get_wizard_options() -> List[str]:
    client = sb()
    page_size = 1000
    start = 0
    names = set()

    while True:
        res = (
            client
            .table("siege_logs")
            .select("wizard, opp_wizard")
            .range(start, start + page_size - 1)
            .execute()
        )
        batch = res.data or []
        if not batch:
            break

        for r in batch:
            wiz = (r.get("wizard") or "").strip()
            opp = (r.get("opp_wizard") or "").strip()
            if wiz:
                names.add(wiz)
            if opp:
                names.add(opp)

        if len(batch) < page_size:
            break
        start += page_size

    return sorted(names)


@st.cache_data(ttl=300)
def get_personal_offense_stats(wizard: str, limit: int = 50) -> pd.DataFrame:
    wizard = (wizard or "").strip()
    if not wizard:
        return pd.DataFrame()

    client = sb()
    page_size = 1000
    start = 0
    rows = []

    while True:
        res = (
            client
            .table("siege_logs")
            .select("result, deck1_1, deck1_2, deck1_3")
            .eq("wizard", wizard)
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

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df["deck_key"] = df.apply(
        lambda r: make_deck_key(r.get("deck1_1", ""), r.get("deck1_2", ""), r.get("deck1_3", "")),
        axis=1,
    )
    df = df[df["deck_key"] != ""]
    if df.empty:
        return df

    agg = (
        df.groupby("deck_key")
        .agg(
            wins=("result", lambda x: (x == "Win").sum()),
            losses=("result", lambda x: (x == "Lose").sum()),
        )
        .reset_index()
    )

    agg["total"] = agg["wins"] + agg["losses"]
    agg["win_rate"] = agg.apply(
        lambda r: (r["wins"] / r["total"] * 100.0) if r["total"] else 0.0,
        axis=1,
    )
    agg[["Unit #1", "Unit #2", "Unit #3"]] = agg["deck_key"].str.split("|", expand=True)
    agg["Summary"] = agg["wins"].astype(int).astype(str) + "W-" + agg["losses"].astype(int).astype(str) + "L"
    agg["Win Rate"] = agg["win_rate"].map(lambda x: f"{x:.1f}%")

    agg = agg.sort_values(["total", "win_rate"], ascending=[False, False]).head(int(limit)).reset_index(drop=True)

    return agg[["Unit #1", "Unit #2", "Unit #3", "wins", "losses", "Win Rate", "Summary", "total"]]


@st.cache_data(ttl=300)
def get_personal_defense_stats(wizard: str, limit: int = 50) -> pd.DataFrame:
    wizard = (wizard or "").strip()
    if not wizard:
        return pd.DataFrame()

    client = sb()
    page_size = 1000
    start = 0
    rows = []

    while True:
        res = (
            client
            .table("siege_logs")
            .select("result, deck2_1, deck2_2, deck2_3")
            .eq("opp_wizard", wizard)
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

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df["deck_key"] = df.apply(
        lambda r: make_deck_key(r.get("deck2_1", ""), r.get("deck2_2", ""), r.get("deck2_3", "")),
        axis=1,
    )
    df = df[df["deck_key"] != ""]
    if df.empty:
        return df

    agg = (
        df.groupby("deck_key")
        .agg(
            wins=("result", lambda x: (x == "Lose").sum()),
            losses=("result", lambda x: (x == "Win").sum()),
        )
        .reset_index()
    )

    agg["total"] = agg["wins"] + agg["losses"]
    agg["win_rate"] = agg.apply(
        lambda r: (r["wins"] / r["total"] * 100.0) if r["total"] else 0.0,
        axis=1,
    )
    agg[["Unit #1", "Unit #2", "Unit #3"]] = agg["deck_key"].str.split("|", expand=True)
    agg["Summary"] = agg["wins"].astype(int).astype(str) + "W-" + agg["losses"].astype(int).astype(str) + "L"
    agg["Win Rate"] = agg["win_rate"].map(lambda x: f"{x:.1f}%")

    agg = agg.sort_values(["total", "win_rate"], ascending=[False, False]).head(int(limit)).reset_index(drop=True)

    return agg[["Unit #1", "Unit #2", "Unit #3", "wins", "losses", "Win Rate", "Summary", "total"]]


@st.cache_data(ttl=120)
def get_personal_offense_logs(wizard: str, deck_key: str, limit: int = 200) -> pd.DataFrame:
    wizard = (wizard or "").strip()
    deck_key = (deck_key or "").strip()
    if not wizard or not deck_key:
        return pd.DataFrame()

    client = sb()
    page_size = 500
    start = 0
    rows = []

    while len(rows) < int(limit):
        res = (
            client
            .table("siege_logs")
            .select(
                "ts, result, opp_guild, opp_wizard, deck1_1,deck1_2,deck1_3, deck2_1,deck2_2,deck2_3"
            )
            .eq("wizard", wizard)
            .in_("result", ["Win", "Lose"])
            .order("ts", desc=True)
            .range(start, start + page_size - 1)
            .execute()
        )

        batch = res.data or []
        if not batch:
            break

        df = pd.DataFrame(batch)
        df["deck_key"] = df.apply(
            lambda r: make_deck_key(r.get("deck1_1", ""), r.get("deck1_2", ""), r.get("deck1_3", "")),
            axis=1,
        )
        matched = df[df["deck_key"] == deck_key]
        if not matched.empty:
            rows.extend(matched.to_dict(orient="records"))

        if len(batch) < page_size:
            break
        start += page_size

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows).head(int(limit)).copy()

    df["공덱"] = df.apply(lambda r: _format_team(r, "deck1_1", "deck1_2", "deck1_3"), axis=1)
    df["방덱"] = df.apply(lambda r: _format_team(r, "deck2_1", "deck2_2", "deck2_3"), axis=1)
    df = df.rename(
        columns={
            "opp_guild": "방어길드",
            "opp_wizard": "방어자",
            "result": "결과",
        }
    )

    return df[["공덱", "방덱", "방어길드", "방어자", "결과"]]


@st.cache_data(ttl=120)
def get_personal_defense_logs(wizard: str, deck_key: str, limit: int = 200) -> pd.DataFrame:
    wizard = (wizard or "").strip()
    deck_key = (deck_key or "").strip()
    if not wizard or not deck_key:
        return pd.DataFrame()

    client = sb()
    page_size = 500
    start = 0
    rows = []

    while len(rows) < int(limit):
        res = (
            client
            .table("siege_logs")
            .select(
                "ts, result, opp_guild, opp_wizard, deck1_1,deck1_2,deck1_3, deck2_1,deck2_2,deck2_3"
            )
            .eq("opp_wizard", wizard)
            .in_("result", ["Win", "Lose"])
            .order("ts", desc=True)
            .range(start, start + page_size - 1)
            .execute()
        )

        batch = res.data or []
        if not batch:
            break

        df = pd.DataFrame(batch)
        df["deck_key"] = df.apply(
            lambda r: make_deck_key(r.get("deck2_1", ""), r.get("deck2_2", ""), r.get("deck2_3", "")),
            axis=1,
        )
        matched = df[df["deck_key"] == deck_key]
        if not matched.empty:
            rows.extend(matched.to_dict(orient="records"))

        if len(batch) < page_size:
            break
        start += page_size

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows).head(int(limit)).copy()

    df["공덱"] = df.apply(lambda r: _format_team(r, "deck1_1", "deck1_2", "deck1_3"), axis=1)
    df["방덱"] = df.apply(lambda r: _format_team(r, "deck2_1", "deck2_2", "deck2_3"), axis=1)
    df = df.rename(
        columns={
            "opp_guild": "방어길드",
            "opp_wizard": "방어자",
            "result": "결과",
        }
    )

    return df[["공덱", "방덱", "방어길드", "방어자", "결과"]]
