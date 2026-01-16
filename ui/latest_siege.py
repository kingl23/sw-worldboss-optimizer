from __future__ import annotations

from dataclasses import dataclass
import pandas as pd
import streamlit as st

from services.supabase_client import get_supabase_client
from ui.auth import require_access_or_stop
from ui.search_offense_deck import get_matchups, make_def_key, _normalize_matchups


@dataclass(frozen=True)
class MatchOption:
    match_id: str
    label: str
    sort_key: pd.Timestamp | None


def sb():
    return get_supabase_client()


def _q(value: str) -> str:
    value = (value or "").replace('"', '\\"')
    return f'"{value}"'


def _fmt_team(r, a: str, b: str, c: str) -> str:
    parts = [r.get(a, ""), r.get(b, ""), r.get(c, "")]
    parts = [p for p in parts if p]
    return " / ".join(parts)


@st.cache_data(ttl=300)
def get_match_options() -> list[MatchOption]:
    res = (
        sb()
        .table("siege_logs")
        .select("match_id, ts, updated_at, opp_guild")
        .execute()
    )
    df = pd.DataFrame(res.data or [])
    if df.empty or "match_id" not in df.columns:
        return []

    df["ts_dt"] = pd.to_datetime(df.get("ts"), errors="coerce")
    df["updated_dt"] = pd.to_datetime(df.get("updated_at"), errors="coerce")
    df["sort_dt"] = df["ts_dt"].fillna(df["updated_dt"])

    options: list[MatchOption] = []
    for match_id, group in df.groupby("match_id"):
        sort_dt = group["sort_dt"].min()
        date_str = "Unknown"
        if pd.notna(sort_dt):
            date_str = sort_dt.strftime("%Y%m%d")

        guilds = sorted({g for g in group.get("opp_guild", []) if g})
        if guilds:
            label = f"{date_str} vs {','.join(guilds)}"
        else:
            label = date_str

        options.append(MatchOption(match_id=str(match_id), label=label, sort_key=sort_dt))

    options.sort(key=lambda opt: opt.sort_key or pd.Timestamp.min, reverse=True)
    return options


@st.cache_data(ttl=120)
def get_match_lose_logs(match_id: str) -> pd.DataFrame:
    res = (
        sb()
        .table("siege_logs")
        .select(
            "match_id, log_id, ts, updated_at, wizard, opp_wizard, opp_guild, result, "
            "deck1_1,deck1_2,deck1_3, deck2_1,deck2_2,deck2_3"
        )
        .eq("match_id", match_id)
        .eq("result", "Lose")
        .execute()
    )
    df = pd.DataFrame(res.data or [])
    if df.empty:
        return df

    df["ts_dt"] = pd.to_datetime(df.get("ts"), errors="coerce")
    df["updated_dt"] = pd.to_datetime(df.get("updated_at"), errors="coerce")
    df["sort_dt"] = df["ts_dt"].fillna(df["updated_dt"])
    df = df.sort_values(["sort_dt"], ascending=True).reset_index(drop=True)
    return df


@st.cache_data(ttl=120)
def get_defense_log_count(def_key: str) -> int:
    parts = [p for p in (def_key or "").split("|") if p]
    if len(parts) < 3:
        return 0
    d1, d2, d3 = parts[0], parts[1], parts[2]

    def_perms = [(d1, d2, d3), (d1, d3, d2)]
    or_clauses = [
        f"and(deck2_1.eq.{_q(a)},deck2_2.eq.{_q(b)},deck2_3.eq.{_q(c)})"
        for a, b, c in def_perms
    ]

    res = (
        sb()
        .table("siege_logs")
        .select("log_id")
        .or_(",".join(or_clauses))
        .limit(11)
        .execute()
    )
    return len(res.data or [])


@st.cache_data(ttl=120)
def get_recommended_offense(def_key: str, limit: int = 10) -> pd.DataFrame:
    raw = get_matchups(def_key, limit=200)
    normalized = _normalize_matchups(raw, limit=200)
    if normalized.empty:
        return normalized

    normalized = normalized.sort_values(["win_rate", "total"], ascending=[False, False])
    return normalized.head(int(limit)).reset_index(drop=True)


def render_latest_siege_tab() -> None:
    st.subheader("Latest Siege")

    options = get_match_options()
    if not options:
        st.info("No siege matches found.")
        return

    labels = {opt.match_id: opt.label for opt in options}
    match_ids = [opt.match_id for opt in options]
    selected_match = st.selectbox(
        "Match",
        options=match_ids,
        format_func=lambda mid: labels.get(mid, mid),
        key="latest_siege_match",
    )

    if not selected_match:
        st.info("Select a match.")
        return

    if not require_access_or_stop("siege_battle"):
        return

    logs = get_match_lose_logs(selected_match)
    if logs.empty:
        st.info("No loss logs found for this match.")
        return

    st.markdown("소환사 | 공덱(3마리) | 방덱(3마리) | 상대길드 | 상대소환사 | 결과")

    for row in logs.to_dict(orient="records"):
        offense = _fmt_team(row, "deck1_1", "deck1_2", "deck1_3")
        defense = _fmt_team(row, "deck2_1", "deck2_2", "deck2_3")

        st.markdown(
            f"{row.get('wizard', '')} | {offense} | {defense} | "
            f"{row.get('opp_guild', '')} | {row.get('opp_wizard', '')} | {row.get('result', '')}"
        )

        def_key = make_def_key(row.get("deck2_1", ""), row.get("deck2_2", ""), row.get("deck2_3", ""))
        recs = get_recommended_offense(def_key, limit=10)

        opinions: list[str] = []
        if get_defense_log_count(def_key) <= 10:
            opinions.append("NEW 방덱")

        if not recs.empty:
            top_offense = set(recs["offense"].fillna("").tolist())
            if offense in top_offense:
                opinions.append("룬아티 스펙 확인")

        for opinion in opinions:
            st.write(opinion)

        st.markdown("Recommended Offense Decks")

        if recs.empty:
            st.info("No matchup data found for this defense deck.")
            continue

        display = recs[["offense", "win", "lose", "total", "win_rate"]].copy()
        display = display.rename(
            columns={
                "offense": "공덱",
                "win": "Win",
                "lose": "Lose",
                "total": "Total",
                "win_rate": "Win Rate",
            }
        )
        display["Win"] = pd.to_numeric(display["Win"], errors="coerce").fillna(0).astype(int)
        display["Lose"] = pd.to_numeric(display["Lose"], errors="coerce").fillna(0).astype(int)
        display["Total"] = pd.to_numeric(display["Total"], errors="coerce").fillna(0).astype(int)
        display["Win Rate"] = pd.to_numeric(display["Win Rate"], errors="coerce").fillna(0.0)

        st.dataframe(
            display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "공덱": st.column_config.TextColumn("공덱", width="large"),
                "Win": st.column_config.NumberColumn("Win", format="%d", width="small"),
                "Lose": st.column_config.NumberColumn("Lose", format="%d", width="small"),
                "Total": st.column_config.NumberColumn("Total", format="%d", width="small"),
                "Win Rate": st.column_config.NumberColumn("Win Rate", format="%.1f%%", width="small"),
            },
        )
