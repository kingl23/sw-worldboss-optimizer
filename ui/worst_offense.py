# ui/worst_offense.py
import streamlit as st
from ui.auth import require_access_or_stop
from data.siege_data import build_worst_offense_list, get_offense_stats_by_defense
from data.siege_trend import build_cumulative_trend_df
from ui.search_offense_deck import get_siege_logs_for_defense, make_def_key
from ui.siege_trend_chart import render_cumulative_trend_chart
from ui.table_utils import apply_dataframe_style, build_deck_column, percent_to_float, to_numeric


def render_worst_offense_tab():
    st.subheader("Worst Offense List")
    apply_dataframe_style()

    with st.form("worst_off_form"):
        col1, col2 = st.columns(2)
        cutoff = col1.number_input("Minimum games (cutoff)", 1, 100, 4, 1, key="wo_cutoff")
        top_n  = col2.number_input("Display count (Top N)", 1, 200, 50, 5, key="wo_top_n")
        submitted = st.form_submit_button("Search")


    if submitted:    
        build_worst_offense_list.clear()
        if not require_access_or_stop("worst_offense"):
            return
        
        base = build_worst_offense_list(cutoff=int(cutoff))
        if base is None or base.empty:
            st.session_state["wo_df"] = None
        else:
            df = (
                base.sort_values(["win_rate", "total"], ascending=[False, False])
                .head(int(top_n))
                .copy()
                .reset_index(drop=True)
            )

            df["Unit #1"] = df["d1"]
            df["Unit #2"] = df["d2"]
            df["Unit #3"] = df["d3"]
            df["Total Games"] = df["total"]

            wins   = df["lose"].fillna(0).astype(int)   # attacker wins
            losses = df["win"].fillna(0).astype(int)    # attacker losses
            totalv = df["total"].fillna(0).astype(int)

            df["Win Rate"] = (wins / totalv.replace(0, 1) * 100).round(2).map(lambda x: f"{x:.2f}%")
            df["Wins"] = wins
            df["Losses"] = losses
            df["Summary"]  = wins.astype(str) + "W-" + losses.astype(str) + "L"

            st.session_state["wo_df"] = df

        st.session_state["wo_selected_idx"] = None

    df = st.session_state.get("wo_df", None)
    if df is None or df is False or (hasattr(df, "empty") and df.empty):
        st.info("Set the filters and click Search.")
        return

    df_display = df.copy()
    df_display["Defense Deck"] = build_deck_column(df_display, ["Unit #1", "Unit #2", "Unit #3"])
    df_display["Wins"] = to_numeric(df_display["Wins"])
    df_display["Losses"] = to_numeric(df_display["Losses"])
    df_display["Total Games"] = to_numeric(df_display["Total Games"])
    df_display["Win Rate"] = percent_to_float(df_display["Win Rate"])

    event = st.dataframe(
        df_display[["Defense Deck", "Wins", "Losses", "Win Rate", "Total Games"]],
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="worst_off_table",
        column_config={
            "Defense Deck": st.column_config.TextColumn("Defense Deck", width="large"),
            "Wins": st.column_config.NumberColumn("Wins", format="%d", width="small"),
            "Losses": st.column_config.NumberColumn("Losses", format="%d", width="small"),
            "Win Rate": st.column_config.NumberColumn("Win Rate", format="%.1f%%", width="small"),
            "Total Games": st.column_config.NumberColumn("Total Games", format="%d", width="small"),
        },
    )

    sel_rows = []
    if event is not None and hasattr(event, "selection"):
        sel_rows = event.selection.get("rows", []) or []

    if sel_rows:
        st.session_state["wo_selected_idx"] = int(sel_rows[0])

    sel = st.session_state.get("wo_selected_idx", None)
    if sel is None:
        return

    # Detail
    sel = max(0, min(int(sel), len(df) - 1))
    picked = df.iloc[sel]
    def1, def2, def3 = picked["Unit #1"], picked["Unit #2"], picked["Unit #3"]

    st.divider()
    st.subheader("Offense stats vs selected defense")
    st.write(f"Selected Defense Deck: **{def1} / {def2} / {def3}**")

    off_limit = st.number_input("Max offense rows", 5, 200, 50, 5, key="off_limit")
    off_df = get_offense_stats_by_defense(def1, def2, def3, limit=int(off_limit))

    if off_df is None or off_df.empty:
        st.info("No offense records found for this defense.")
        return

    off_df_display = off_df.rename(columns={"total": "Total Games", "wins": "Wins", "losses": "Losses"})
    off_df_display["Offense Deck"] = build_deck_column(off_df_display, ["Unit #1", "Unit #2", "Unit #3"])
    off_df_display["Wins"] = to_numeric(off_df_display["Wins"])
    off_df_display["Losses"] = to_numeric(off_df_display["Losses"])
    off_df_display["Total Games"] = to_numeric(off_df_display["Total Games"])
    off_df_display["Win Rate"] = percent_to_float(off_df_display["Win Rate"])
    st.dataframe(
        off_df_display[["Offense Deck", "Wins", "Losses", "Win Rate", "Summary", "Total Games"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Offense Deck": st.column_config.TextColumn("Offense Deck", width="large"),
            "Wins": st.column_config.NumberColumn("Wins", format="%d", width="small"),
            "Losses": st.column_config.NumberColumn("Losses", format="%d", width="small"),
            "Win Rate": st.column_config.NumberColumn("Win Rate", format="%.1f%%", width="small"),
            "Summary": st.column_config.TextColumn("Summary", width="small"),
            "Total Games": st.column_config.NumberColumn("Total Games", format="%d", width="small"),
        },
    )

    st.divider()
    st.subheader("Trend Analysis (Cumulative)")
    def_key = make_def_key(def1, def2, def3)
    logs_df = get_siege_logs_for_defense(def_key=def_key, limit=2000)
    trend_df = build_cumulative_trend_df(logs_df)
    if trend_df.empty:
        st.info("No trend data available for this defense deck.")
        return
    render_cumulative_trend_chart(trend_df)
