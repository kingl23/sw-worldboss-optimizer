# ui/worst_offense.py
import streamlit as st
from ui.auth import require_access_or_stop
from services.siege_service import build_worst_offense_list, get_offense_stats_by_defense


def render_worst_offense_tab():
    st.subheader("Worst Offense List")

    with st.form("worst_off_form"):
        col1, col2 = st.columns(2)
        cutoff = col1.number_input("최소 경기 수 (cutoff)", 1, 100, 4, 1, key="wo_cutoff")
        top_n  = col2.number_input("표시 개수 (Top N)", 1, 200, 50, 5, key="wo_top_n")
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
            df["Total"]   = df["total"]

            wins   = df["lose"].fillna(0).astype(int)   # attacker wins
            losses = df["win"].fillna(0).astype(int)    # attacker losses
            totalv = df["total"].fillna(0).astype(int)

            df["Win Rate"] = (wins / totalv.replace(0, 1) * 100).round(2).map(lambda x: f"{x:.2f}%")
            df["Summary"]  = wins.astype(str) + "W-" + losses.astype(str) + "L"

            st.session_state["wo_df"] = df

        st.session_state["wo_selected_idx"] = None

    df = st.session_state.get("wo_df", None)
    if df is None or df is False or (hasattr(df, "empty") and df.empty):
        st.info("조건을 설정한 뒤 Search를 눌러주세요.")
        return

    event = st.dataframe(
        df[["Unit #1", "Unit #2", "Unit #3", "Summary", "Win Rate", "Total"]],
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="worst_off_table",
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
    st.write(f"Selected Defense: **{def1} / {def2} / {def3}**")

    off_limit = st.number_input("Max offense rows", 5, 200, 50, 5, key="off_limit")
    off_df = get_offense_stats_by_defense(def1, def2, def3, limit=int(off_limit))

    if off_df is None or off_df.empty:
        st.info("No offense records found for this defense.")
        return

    st.dataframe(
        off_df[["Unit #1", "Unit #2", "Unit #3", "wins", "losses", "Win Rate", "Summary", "total"]],
        use_container_width=True,
        hide_index=True,
    )
