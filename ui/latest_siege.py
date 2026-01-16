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


def _parse_match_id_parts(match_id: str | int) -> tuple[str, str, str, str] | None:
    match_str = str(match_id or "")
    if len(match_str) < 8 or not match_str[:8].isdigit():
        return None
    yyyy = match_str[0:4]
    mm = match_str[4:6]
    ww = match_str[6:8]
    suffix = match_str[8:] or "0"
    if not (yyyy.isdigit() and mm.isdigit() and ww.isdigit()):
        return None
    return yyyy, mm, ww, suffix


def _match_label_from_week_encoding(
    match_id: str | int,
    match_order_map: dict[str, int],
) -> str | None:
    parts = _parse_match_id_parts(match_id)
    if not parts:
        return None
    yyyy, mm, ww, _ = parts
    try:
        year = int(yyyy)
        month = int(mm)
        week_index = int(ww)
    except ValueError:
        return None
    match_order = match_order_map.get(str(match_id), 0)
    order_label = "1차" if match_order == 0 else "2차"
    return f"{year}년 {month}월 {week_index}주차 {order_label}"


@st.cache_data(ttl=300)
def get_match_options() -> list[MatchOption]:
    batch_size = 1000
    offset = 0
    rows: list[dict] = []
    while True:
        res = (
            sb()
            .table("siege_logs")
            .select("match_id, ts, updated_at, opp_guild")
            .range(offset, offset + batch_size - 1)
            .execute()
        )
        batch = res.data or []
        rows.extend(batch)
        if len(batch) < batch_size:
            break
        offset += batch_size

    df = pd.DataFrame(rows)
    if df.empty or "match_id" not in df.columns:
        return []

    df["ts_dt"] = pd.to_datetime(df.get("ts"), errors="coerce", utc=True)
    df["updated_dt"] = pd.to_datetime(df.get("updated_at"), errors="coerce", utc=True)

    match_order_map: dict[str, int] = {}
    df["match_parts"] = df["match_id"].apply(_parse_match_id_parts)
    valid_parts = df[df["match_parts"].notna()].copy()
    if not valid_parts.empty:
        valid_parts["year_month_week"] = valid_parts["match_parts"].apply(lambda p: (p[0], p[1], p[2]))
        valid_parts["suffix_num"] = valid_parts["match_parts"].apply(
            lambda p: int(p[3]) if str(p[3]).isdigit() else 0
        )
        for _, group in valid_parts.groupby("year_month_week"):
            ids = group[["match_id", "suffix_num"]].drop_duplicates()
            ordered = ids.sort_values("suffix_num", ascending=True)["match_id"].tolist()
            for idx, mid in enumerate(ordered):
                match_order_map[str(mid)] = 0 if idx == 0 else 1

    options: list[MatchOption] = []
    for match_id, group in df.groupby("match_id"):
        label_prefix = _match_label_from_week_encoding(match_id, match_order_map)
        sort_dt = None
        if not label_prefix:
            ts_min = group["ts_dt"].dropna().min()
            if pd.isna(ts_min):
                sort_dt = group["updated_dt"].dropna().min()
            else:
                sort_dt = ts_min
            if pd.notna(sort_dt):
                label_prefix = sort_dt.tz_convert("Asia/Seoul").strftime("%Y%m%d")
        if not label_prefix:
            label_prefix = "Unknown"

        guilds = sorted({g for g in group.get("opp_guild", []) if g})
        if guilds:
            label = f"{label_prefix} vs {','.join(guilds)}"
        else:
            label = label_prefix

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


def _build_opinion_badges_html(opinions: list[str]) -> str:
    if not opinions:
        return ""
    return " ".join([f"<span class='opinion-badge'>{op}</span>" for op in opinions])


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
    st.caption(f"Matches found: {len(match_ids)}")

    with st.expander("Debug", expanded=False):
        preview = [
            f"{labels.get(mid, mid)} ({mid})"
            for mid in match_ids[:10]
        ]
        if preview:
            st.write("\n".join(preview))
        else:
            st.write("No matches available.")

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
          .result-badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 999px;
            background: rgba(255, 99, 71, 0.15);
            border: 1px solid rgba(255, 99, 71, 0.4);
            font-weight: 600;
            font-size: 12px;
          }
          .summary-muted {
            color: rgba(250, 250, 250, 0.7);
            font-size: 13px;
          }
          .result-stack {
            display: flex;
            flex-wrap: nowrap;
            gap: 6px;
            justify-content: flex-end;
            align-items: center;
            white-space: nowrap;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )
    for row in logs.to_dict(orient="records"):
        offense = _fmt_team(row, "deck1_1", "deck1_2", "deck1_3")
        defense = _fmt_team(row, "deck2_1", "deck2_2", "deck2_3")
        def_key = make_def_key(row.get("deck2_1", ""), row.get("deck2_2", ""), row.get("deck2_3", ""))
        recs = get_recommended_offense(def_key)
        recs_display = recs[recs["win_rate"] >= 90.0] if not recs.empty else recs

        opinions: list[str] = []
        if get_defense_log_count(def_key) <= 10:
            opinions.append("NEW 방덱")

        if not recs_display.empty:
            top_offense = set(recs_display["offense"].fillna("").tolist())
            if offense in top_offense:
                opinions.append("룬아티 스펙 확인")

        with st.container():
            col_left, col_mid, col_result = st.columns([1.2, 4.0, 1.8])
            col_left.markdown(f"**{row.get('wizard', '')}**")
            col_mid.markdown(
                f"공덱: **{offense}** vs 방덱: **{defense}**  \n"
                f"<span class='summary-muted'>{row.get('opp_guild', '')} / {row.get('opp_wizard', '')}</span>",
                unsafe_allow_html=True,
            )
            badges_html = _build_opinion_badges_html(opinions)
            col_result.markdown(
                f"<div class='result-stack'>"
                f"<span class='result-badge'>{row.get('result', '')}</span>{badges_html}"
                f"</div>",
                unsafe_allow_html=True,
            )

            with st.expander("Recommended Offense", expanded=False):
                if recs.empty:
                    st.caption("No matchup data found for this defense deck.")
                elif recs_display.empty:
                    st.caption("90% 이상 추천 공덱 없음")
                else:
                    display = recs_display[["offense", "win_rate"]].copy()
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
