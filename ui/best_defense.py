# ui/best_defense.py
import streamlit as st

from ui.auth import require_access_or_stop
from data.defense_data import (
    get_defense_deck_stats,
    get_defense_decks_vs_guild,
    get_opp_guild_options,
)
from ui.table_utils import apply_dataframe_style, build_deck_column, percent_to_float, to_numeric


def render_best_defense_tab():
    st.subheader("Best Defense")
    apply_dataframe_style()

    # -------------------------
    # Section 1: All Defense Deck Stats (mode=1 always)
    # -------------------------
    st.markdown("### Overall Defense Deck Stats (Including Guild Groups)")
    st.caption("Top N=0 shows all results (default 50).")

    c1, c2 = st.columns([0.25, 0.75], vertical_alignment="bottom")
    with c1:
        top_n_all = st.number_input(
            "Top N (overall)",
            min_value=0,
            max_value=500,
            value=50,
            step=10,
            key="def_all_topn",
        )
    with c2:
        run_all = st.button("Run (overall)", type="primary", key="def_all_run")

    if run_all:
        if not require_access_or_stop("siege_defense"):
            return
        df = get_defense_deck_stats(limit=int(top_n_all))
        if "error" in df.columns:
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            df_display = df.copy()
            df_display["Defense Deck"] = build_deck_column(df_display, ["d1", "d2", "d3"])
            df_display = df_display.rename(
                columns={
                    "win": "Wins",
                    "lose": "Losses",
                    "win_rate": "Win Rate",
                    "in32_win": "In32 Wins",
                    "in32_lose": "In32 Losses",
                    "in32_win_rate": "In32 Win Rate",
                    "in12_win": "In12 Wins",
                    "in12_lose": "In12 Losses",
                    "in12_win_rate": "In12 Win Rate",
                    "in4_win": "In4 Wins",
                    "in4_lose": "In4 Losses",
                    "in4_win_rate": "In4 Win Rate",
                }
            )

            win_rate_cols = ["Win Rate", "In32 Win Rate", "In12 Win Rate", "In4 Win Rate"]
            for col in win_rate_cols:
                if col in df_display.columns:
                    df_display[col] = percent_to_float(df_display[col])

            numeric_cols = ["Wins", "Losses", "In32 Wins", "In32 Losses", "In12 Wins", "In12 Losses", "In4 Wins", "In4 Losses"]
            for col in numeric_cols:
                if col in df_display.columns:
                    df_display[col] = to_numeric(df_display[col])

            ordered_cols = [
                "Defense Deck",
                "Wins",
                "Losses",
                "Win Rate",
                "In32 Wins",
                "In32 Losses",
                "In32 Win Rate",
                "In12 Wins",
                "In12 Losses",
                "In12 Win Rate",
                "In4 Wins",
                "In4 Losses",
                "In4 Win Rate",
            ]
            ordered_cols = [col for col in ordered_cols if col in df_display.columns]

            st.dataframe(
                df_display[ordered_cols],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Defense Deck": st.column_config.TextColumn("Defense Deck", width="large"),
                    "Wins": st.column_config.NumberColumn("Wins", format="%d", width="small"),
                    "Losses": st.column_config.NumberColumn("Losses", format="%d", width="small"),
                    "Win Rate": st.column_config.NumberColumn("Win Rate", format="%.1f%%", width="small"),
                    "In32 Wins": st.column_config.NumberColumn("In32 Wins", format="%d", width="small"),
                    "In32 Losses": st.column_config.NumberColumn("In32 Losses", format="%d", width="small"),
                    "In32 Win Rate": st.column_config.NumberColumn("In32 Win Rate", format="%.1f%%", width="small"),
                    "In12 Wins": st.column_config.NumberColumn("In12 Wins", format="%d", width="small"),
                    "In12 Losses": st.column_config.NumberColumn("In12 Losses", format="%d", width="small"),
                    "In12 Win Rate": st.column_config.NumberColumn("In12 Win Rate", format="%.1f%%", width="small"),
                    "In4 Wins": st.column_config.NumberColumn("In4 Wins", format="%d", width="small"),
                    "In4 Losses": st.column_config.NumberColumn("In4 Losses", format="%d", width="small"),
                    "In4 Win Rate": st.column_config.NumberColumn("In4 Win Rate", format="%.1f%%", width="small"),
                },
            )

    st.divider()

    # -------------------------
    # Section 2: Defense Decks vs Opponent Guild
    # -------------------------
    st.markdown("### Defense Deck Stats by Opponent Guild")
    st.caption("Top N default: 50")

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
            "Top N (by guild)",
            min_value=1,
            max_value=500,
            value=50,
            step=10,
            key="def_vs_topn",
        )
    with c5:
        run_vs = st.button("Run (by guild)", type="primary", key="def_vs_run")

    if run_vs:
        if not require_access_or_stop("siege_defense"):
            return
        df2 = get_defense_decks_vs_guild(opp_guild=opp_guild, limit=int(top_n_vs))
        if "error" in df2.columns:
            st.dataframe(df2, use_container_width=True, hide_index=True)
        else:
            df2_display = df2.copy()
            df2_display["Defense Deck"] = build_deck_column(df2_display, ["d1", "d2", "d3"])
            df2_display = df2_display.rename(
                columns={
                    "win": "Wins",
                    "lose": "Losses",
                    "win_rate": "Win Rate",
                }
            )
            df2_display["Win Rate"] = percent_to_float(df2_display["Win Rate"])
            df2_display["Wins"] = to_numeric(df2_display["Wins"])
            df2_display["Losses"] = to_numeric(df2_display["Losses"])

            ordered_cols = ["Defense Deck", "Wins", "Losses", "Win Rate"]

            st.dataframe(
                df2_display[ordered_cols],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Defense Deck": st.column_config.TextColumn("Defense Deck", width="large"),
                    "Wins": st.column_config.NumberColumn("Wins", format="%d", width="small"),
                    "Losses": st.column_config.NumberColumn("Losses", format="%d", width="small"),
                    "Win Rate": st.column_config.NumberColumn("Win Rate", format="%.1f%%", width="small"),
                },
            )
