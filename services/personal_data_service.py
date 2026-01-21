from __future__ import annotations

from typing import Dict, List, Tuple

import pandas as pd
import streamlit as st

from services.supabase_client import get_supabase_client
from utils.deck_utils import make_deck_key, split_deck_key


FOUR_STAR_BASES = {39, 35, 29, 26, 22, 16, 13, 9, 3}


def _clean_name(value: str) -> str:
    return (value or "").strip()


def _make_deck_key(a: str, b: str, c: str) -> str:
    return make_deck_key(_clean_name(a), _clean_name(b), _clean_name(c))


def _pct(win: int, total: int) -> str:
    if total <= 0:
        return "0.0%"
    return f"{(win / total) * 100.0:.1f}%"


def _parse_base(value) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


@st.cache_data(ttl=300)
def get_record_summary(wizard_name: str) -> pd.DataFrame:
    wizard_name = _clean_name(wizard_name)
    if not wizard_name:
        return pd.DataFrame()

    totals = {
        "all": {"win": 0, "lose": 0},
        "four": {"win": 0, "lose": 0},
        "five": {"win": 0, "lose": 0},
    }

    client = get_supabase_client()
    page_size = 1000
    start = 0

    while True:
        res = (
            client
            .table("siege_logs")
            .select("result, base")
            .eq("wizard", wizard_name)
            .in_("result", ["Win", "Lose"])
            .range(start, start + page_size - 1)
            .execute()
        )
        batch = res.data or []
        if not batch:
            break

        for row in batch:
            result = _clean_name(row.get("result"))
            if result not in {"Win", "Lose"}:
                continue
            is_win = result == "Win"

            totals["all"]["win" if is_win else "lose"] += 1

            base_val = _parse_base(row.get("base"))
            key = "four" if (base_val in FOUR_STAR_BASES) else "five"
            totals[key]["win" if is_win else "lose"] += 1

        if len(batch) < page_size:
            break
        start += page_size

    rows = []
    for label, key in [("All", "all"), ("4★", "four"), ("5★", "five")]:
        win = totals[key]["win"]
        lose = totals[key]["lose"]
        total = win + lose
        rows.append(
            {
                "Category": label,
                "Total Games": int(total),
                "Wins": int(win),
                "Losses": int(lose),
                "Win Rate (%)": _pct(win, total),
            }
        )

    return pd.DataFrame(rows)


@st.cache_data(ttl=300)
def get_top_offense_decks(wizard_name: str, limit: int) -> pd.DataFrame:
    wizard_name = _clean_name(wizard_name)
    if not wizard_name:
        return pd.DataFrame()

    client = get_supabase_client()
    page_size = 1000
    start = 0

    deck_counts: Dict[str, Tuple[int, int]] = {}

    while True:
        res = (
            client
            .table("siege_logs")
            .select("result, deck1_1, deck1_2, deck1_3")
            .eq("wizard", wizard_name)
            .in_("result", ["Win", "Lose"])
            .range(start, start + page_size - 1)
            .execute()
        )
        batch = res.data or []
        if not batch:
            break

        for row in batch:
            key = _make_deck_key(row.get("deck1_1"), row.get("deck1_2"), row.get("deck1_3"))
            if not key:
                continue
            is_win = _clean_name(row.get("result")) == "Win"
            win, lose = deck_counts.get(key, (0, 0))
            if is_win:
                win += 1
            else:
                lose += 1
            deck_counts[key] = (win, lose)

        if len(batch) < page_size:
            break
        start += page_size

    rows: List[Dict[str, object]] = []
    for key, (win, lose) in deck_counts.items():
        total = win + lose
        d1, d2, d3 = split_deck_key(key)
        rows.append(
            {
                "key": key,
                "Unit #1": d1,
                "Unit #2": d2,
                "Unit #3": d3,
                "Wins": int(win),
                "Losses": int(lose),
                "Total Games": int(total),
                "Win Rate (%)": _pct(win, total),
                "_win_rate_num": (win / total) if total else 0.0,
            }
        )

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df = df.sort_values(
        by=["Total Games", "_win_rate_num", "key"],
        ascending=[False, False, True],
    )
    df = df.drop(columns=["_win_rate_num"]).head(int(limit)).reset_index(drop=True)
    return df


@st.cache_data(ttl=300)
def get_top_defense_decks(wizard_name: str, limit: int) -> pd.DataFrame:
    wizard_name = _clean_name(wizard_name)
    if not wizard_name:
        return pd.DataFrame()

    client = get_supabase_client()
    page_size = 1000
    start = 0

    deck_counts: Dict[str, Tuple[int, int]] = {}

    while True:
        res = (
            client
            .table("defense_logs")
            .select("result, deck1_1, deck1_2, deck1_3, wizard")
            .eq("wizard", wizard_name)
            .in_("result", ["Win", "Lose"])
            .range(start, start + page_size - 1)
            .execute()
        )
        batch = res.data or []
        if not batch:
            break

        for row in batch:
            key = _make_deck_key(row.get("deck1_1"), row.get("deck1_2"), row.get("deck1_3"))
            if not key:
                continue
            is_win = _clean_name(row.get("result")) == "Win"
            win, lose = deck_counts.get(key, (0, 0))
            if is_win:
                win += 1
            else:
                lose += 1
            deck_counts[key] = (win, lose)

        if len(batch) < page_size:
            break
        start += page_size

    rows: List[Dict[str, object]] = []
    for key, (win, lose) in deck_counts.items():
        total = win + lose
        d1, d2, d3 = split_deck_key(key)
        rows.append(
            {
                "key": key,
                "Unit #1": d1,
                "Unit #2": d2,
                "Unit #3": d3,
                "Wins": int(win),
                "Losses": int(lose),
                "Total Games": int(total),
                "Win Rate (%)": _pct(win, total),
                "_win_rate_num": (win / total) if total else 0.0,
            }
        )

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df = df.sort_values(
        by=["Total Games", "_win_rate_num", "key"],
        ascending=[False, False, True],
    )
    df = df.drop(columns=["_win_rate_num"]).head(int(limit)).reset_index(drop=True)
    return df


@st.cache_data(ttl=300)
def get_offense_deck_details(wizard_name: str, offense_key: str, limit: int) -> pd.DataFrame:
    wizard_name = _clean_name(wizard_name)
    offense_key = _clean_name(offense_key)
    if not (wizard_name and offense_key):
        return pd.DataFrame()

    key_parts = offense_key.split("|")
    leader = key_parts[0] if key_parts else ""

    client = get_supabase_client()
    page_size = 1000
    start = 0

    rows: List[Dict[str, object]] = []

    while True:
        res = (
            client
            .table("siege_logs")
            .select(
                "ts, result, wizard, opp_wizard, opp_guild, "
                "deck1_1, deck1_2, deck1_3, deck2_1, deck2_2, deck2_3"
            )
            .eq("wizard", wizard_name)
            .eq("deck1_1", leader)
            .in_("result", ["Win", "Lose"])
            .range(start, start + page_size - 1)
            .execute()
        )
        batch = res.data or []
        if not batch:
            break

        for row in batch:
            key = _make_deck_key(row.get("deck1_1"), row.get("deck1_2"), row.get("deck1_3"))
            if key != offense_key:
                continue
            rows.append(row)

        if len(batch) < page_size:
            break
        start += page_size

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    if "ts" in df.columns:
        df = df.sort_values("ts", ascending=False)

    def _get_col(row, name: str) -> str:
        return _clean_name(row.get(name))

    mapped_rows = []
    for _, row in df.iterrows():
        mapped_rows.append(
            {
                "Offense Deck 1": _get_col(row, "deck1_1"),
                "Offense Deck 2": _get_col(row, "deck1_2"),
                "Offense Deck 3": _get_col(row, "deck1_3"),
                "Defense Deck 1": _get_col(row, "deck2_1"),
                "Defense Deck 2": _get_col(row, "deck2_2"),
                "Defense Deck 3": _get_col(row, "deck2_3"),
                "Defense Guild": _get_col(row, "opp_guild"),
                "Defender": _get_col(row, "opp_wizard"),
                "Result": _get_col(row, "result"),
            }
        )

    detail_df = pd.DataFrame(mapped_rows)
    return detail_df.head(int(limit)).reset_index(drop=True)


def _empty_hour_distribution() -> pd.DataFrame:
    hours = list(range(12, 24))
    return pd.DataFrame({"Hour": hours, "Count": [0] * len(hours)})


@st.cache_data(ttl=120)
def get_attack_log_hour_distribution(wizard_name: str, timezone: str = "Asia/Seoul") -> pd.DataFrame:
    wizard_name = _clean_name(wizard_name)
    if not wizard_name:
        return _empty_hour_distribution()

    client = get_supabase_client()
    page_size = 1000
    start = 0
    ts_values: List[str] = []

    while True:
        res = (
            client
            .table("siege_logs")
            .select("ts")
            .eq("wizard", wizard_name)
            .range(start, start + page_size - 1)
            .execute()
        )
        batch = res.data or []
        if not batch:
            break

        ts_values.extend([row.get("ts") for row in batch if row.get("ts")])

        if len(batch) < page_size:
            break
        start += page_size

    if not ts_values:
        return _empty_hour_distribution()

    ts_series = pd.to_datetime(pd.Series(ts_values), errors="coerce")
    if ts_series.dt.tz is None:
        ts_series = ts_series.dt.tz_localize(timezone)
    else:
        ts_series = ts_series.dt.tz_convert(timezone)
    hours = ts_series.dt.hour.dropna()

    hour_range = list(range(12, 24))
    counts = hours.value_counts().reindex(hour_range, fill_value=0).sort_index()

    return pd.DataFrame({"Hour": counts.index.astype(int), "Count": counts.values.astype(int)})
