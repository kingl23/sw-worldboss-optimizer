# ui/best_defense.py
import streamlit as st
import pandas as pd

from ui.auth import require_access_or_stop
from data.defense_data import (
    get_defense_deck_stats,
    get_defense_decks_vs_guild,
    get_opp_guild_options,
)


def render_best_defense_tab():
    st.subheader("Best Defense")

    # -------------------------
    # Section 1: All Defense Deck Stats (mode=1 always)
    # -------------------------
    st.markdown("### All Defense Deck Stats (Including Guild Groups)")
    st.caption("Top N = 0 shows all results (default 50).")

    c1, c2 = st.columns([0.25, 0.75], vertical_alignment="bottom")
    with c1:
        top_n_all = st.number_input(
            "Top N (All Stats)",
            min_value=0,
            max_value=500,
            value=50,
            step=10,
            key="def_all_topn",
        )
    with c2:
        run_all = st.button("Run (All Stats)", type="primary", key="def_all_run")

    if run_all:
        if not require_access_or_stop("siege_defense"):
            return
        df = get_defense_deck_stats(limit=int(top_n_all))
        df_display = df.rename(
            columns={
                "win": "Wins",
                "lose": "Losses",
                "win_rate": "Win Rate",
                "in32_win": "IN32 Wins",
                "in32_lose": "IN32 Losses",
                "in32_win_rate": "IN32 Win Rate",
                "in12_win": "IN12 Wins",
                "in12_lose": "IN12 Losses",
                "in12_win_rate": "IN12 Win Rate",
                "in4_win": "IN4 Wins",
                "in4_lose": "IN4 Losses",
                "in4_win_rate": "IN4 Win Rate",
            },
            errors="ignore",
        )
        st.dataframe(df_display, use_container_width=True, hide_index=True)

    st.divider()

    # -------------------------
    # Section 2: Defense Decks vs Opponent Guild
    # -------------------------
    st.markdown("### Defense Deck Stats by Opponent Guild")
    st.caption("Default Top N is 50.")

    # 옵션 로드(캐시)
    guilds = get_opp_guild_options()

    c3, c4, c5 = st.columns([0.5, 0.25, 0.25], vertical_alignment="bottom")
    with c3:
        opp_guild = st.selectbox(
            "Opponent Guild",
            options=[""] + guilds,
            index=0,
            key="def_vs_guild_name",
        )
    with c4:
        top_n_vs = st.number_input(
            "Top N (By Guild)",
            min_value=1,
            max_value=500,
            value=50,
            step=10,
            key="def_vs_topn",
        )
    with c5:
        run_vs = st.button("Run (By Guild)", type="primary", key="def_vs_run")

    if run_vs:
        if not require_access_or_stop("siege_defense"):
            return
        df2 = get_defense_decks_vs_guild(opp_guild=opp_guild, limit=int(top_n_vs))
        df2_display = df2.rename(
            columns={
                "win": "Wins",
                "lose": "Losses",
                "win_rate": "Win Rate",
            },
            errors="ignore",
        )
        st.dataframe(df2_display, use_container_width=True, hide_index=True)
