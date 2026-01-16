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
def get_recommended_offense(def_key: str) -> pd.DataFrame:
    raw = get_matchups(def_key, limit=200)
    normalized = _normalize_matchups(raw, limit=200)
    if normalized.empty:
        return normalized

    top10_by_total = normalized.sort_values(["total"], ascending=[False]).head(10)
    top10_by_total = top10_by_total.sort_values(["win_rate", "total"], ascending=[False, False])
    return top10_by_total.head(5).reset_index(drop=True)


def _render_opinion_badges(opinions: list[str]) -> None:
    if not opinions:
        return
    badges = " ".join([f"<span class='opinion-badge'>{op}</span>" for op in opinions])
    st.markdown(badges, unsafe_allow_html=True)


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

    st.markdown(
        """
        <style>
          .opinion-badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 999px;
            background: rgba(255, 215, 0, 0.15);
            border: 1px solid rgba(255, 215, 0, 0.4);
            font-weight: 600;
            font-size: 12px;
            margin-right: 6px;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("**소환사 | 공덱(3마리) | 방덱(3마리) | 상대길드 | 상대소환사 | 결과**")

    for row in logs.to_dict(orient="records"):
        offense = _fmt_team(row, "deck1_1", "deck1_2", "deck1_3")
        defense = _fmt_team(row, "deck2_1", "deck2_2", "deck2_3")
        expander_title = (
            f"{row.get('wizard', '')} | {offense} -> {defense} | "
            f"{row.get('opp_guild', '')}/{row.get('opp_wizard', '')} | {row.get('result', '')}"
        )
        with st.expander(expander_title, expanded=True):
            cols = st.columns([1.4, 2.2, 2.2, 1.6, 1.6, 0.8])
            cols[0].write(row.get("wizard", ""))
            cols[1].write(offense)
            cols[2].write(defense)
            cols[3].write(row.get("opp_guild", ""))
            cols[4].write(row.get("opp_wizard", ""))
            cols[5].write(row.get("result", ""))

            def_key = make_def_key(row.get("deck2_1", ""), row.get("deck2_2", ""), row.get("deck2_3", ""))
            recs = get_recommended_offense(def_key)

            opinions: list[str] = []
            if get_defense_log_count(def_key) <= 10:
                opinions.append("NEW 방덱")

            if not recs.empty:
                top_offense = set(recs["offense"].fillna("").tolist())
                if offense in top_offense:
                    opinions.append("룬아티 스펙 확인")

            _render_opinion_badges(opinions)

            st.markdown("Recommended Offense Decks")

            if recs.empty:
                st.info("No matchup data found for this defense deck.")
                continue

            display = recs[["offense", "win_rate"]].copy()
            display = display.rename(columns={"offense": "공덱(3마리)", "win_rate": "승률"})
            display["승률"] = pd.to_numeric(display["승률"], errors="coerce").fillna(0.0)

            st.dataframe(
                display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "공덱(3마리)": st.column_config.TextColumn("공덱(3마리)", width="large"),
                    "승률": st.column_config.NumberColumn("승률", format="%.1f%%", width="small"),
                },
            )
        st.divider()
