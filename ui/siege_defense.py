# ui/siege_defense.py
import streamlit as st
import pandas as pd

from ui.auth import require_access_or_stop
from data.defense_data import (
    get_defense_deck_stats,
    get_defense_decks_vs_guild,
    get_opp_guild_options,
)


def render_siege_defense_tab():
    st.subheader("Siege Defense")

    # -------------------------
    # Section 1: All Defense Deck Stats (mode=1 always)
    # -------------------------
    st.markdown("### 전체 방덱 통계 (길드그룹 포함)")
    st.caption("Top N=0이면 전체 출력됩니다. (기본 50)")

    c1, c2 = st.columns([0.25, 0.75], vertical_alignment="bottom")
    with c1:
        top_n_all = st.number_input(
            "Top N (전체 통계)",
            min_value=0,
            max_value=500,
            value=50,
            step=10,
            key="def_all_topn",
        )
    with c2:
        run_all = st.button("Run (전체 통계)", type="primary", key="def_all_run")

    if run_all:
        require_access_or_stop("siege_defense")
        df = get_defense_deck_stats(limit=int(top_n_all))
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.divider()

    # -------------------------
    # Section 2: Defense Decks vs Opponent Guild
    # -------------------------
    st.markdown("### 길드별(상대) 방덱 통계")
    st.caption("Top N 기본 50")

    # 옵션 로드(캐시)
    guilds = get_opp_guild_options()

    c3, c4, c5 = st.columns([0.5, 0.25, 0.25], vertical_alignment="bottom")
    with c3:
        opp_guild = st.selectbox(
            "Opp Guild",
            options=[""] + guilds,
            index=0,
            key="def_vs_guild_name",
        )
    with c4:
        top_n_vs = st.number_input(
            "Top N (길드별)",
            min_value=1,
            max_value=500,
            value=50,
            step=10,
            key="def_vs_topn",
        )
    with c5:
        run_vs = st.button("Run (길드별)", type="primary", key="def_vs_run")

    if run_vs:
        require_access_or_stop("siege_defense")
        df2 = get_defense_decks_vs_guild(opp_guild=opp_guild, limit=int(top_n_vs))
        st.dataframe(df2, use_container_width=True, hide_index=True)
