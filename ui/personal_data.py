# ui/personal_data.py
import streamlit as st

from ui.auth import require_access_or_stop
from data.personal_data import (
    get_wizard_options,
    get_personal_offense_stats,
    get_personal_defense_stats,
    get_personal_offense_logs,
    get_personal_defense_logs,
)


def _init_state():
    if "personal_data_run" not in st.session_state:
        st.session_state["personal_data_run"] = False
    if "personal_data_last_wizard" not in st.session_state:
        st.session_state["personal_data_last_wizard"] = ""
    if "personal_data_off_df" not in st.session_state:
        st.session_state["personal_data_off_df"] = None
    if "personal_data_def_df" not in st.session_state:
        st.session_state["personal_data_def_df"] = None
    if "personal_data_selected_off_idx" not in st.session_state:
        st.session_state["personal_data_selected_off_idx"] = None
    if "personal_data_selected_def_idx" not in st.session_state:
        st.session_state["personal_data_selected_def_idx"] = None


def _reset_on_wizard_change(wizard: str):
    last = st.session_state.get("personal_data_last_wizard", "")
    if wizard != last:
        st.session_state["personal_data_run"] = False
        st.session_state["personal_data_last_wizard"] = wizard
        st.session_state["personal_data_off_df"] = None
        st.session_state["personal_data_def_df"] = None
        st.session_state["personal_data_selected_off_idx"] = None
        st.session_state["personal_data_selected_def_idx"] = None


def render_personal_data_tab():
    st.subheader("Personal Data")

    _init_state()

    col1, col2 = st.columns([0.7, 0.3], vertical_alignment="bottom")
    with col1:
        wizard = st.selectbox("Wizard", [""] + get_wizard_options(), key="personal_data_wizard")
    with col2:
        top_n = st.number_input("Top N", min_value=5, max_value=200, value=50, step=5, key="personal_data_top_n")

    _reset_on_wizard_change(wizard)

    load_clicked = st.button("Load", type="primary", key="personal_data_load")

    if load_clicked:
        if not require_access_or_stop("personal_data"):
            return
        if not wizard:
            st.warning("Wizard를 선택하세요.")
            return

        st.session_state["personal_data_run"] = True
        st.session_state["personal_data_off_df"] = get_personal_offense_stats(wizard, limit=int(top_n))
        st.session_state["personal_data_def_df"] = get_personal_defense_stats(wizard, limit=int(top_n))
        st.session_state["personal_data_selected_off_idx"] = None
        st.session_state["personal_data_selected_def_idx"] = None

    if not st.session_state.get("personal_data_run"):
        st.info("Wizard를 선택한 뒤 Load를 눌러주세요.")
        return

    off_df = st.session_state.get("personal_data_off_df")
    def_df = st.session_state.get("personal_data_def_df")

    st.subheader("Top Offense")
    if off_df is None or (hasattr(off_df, "empty") and off_df.empty):
        st.info("공격 기록이 없습니다.")
    else:
        event = st.dataframe(
            off_df[["Unit #1", "Unit #2", "Unit #3", "Summary", "Win Rate", "total"]],
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            key="personal_offense_table",
        )

        sel_rows = []
        if event is not None and hasattr(event, "selection"):
            sel_rows = event.selection.get("rows", []) or []
        if sel_rows:
            st.session_state["personal_data_selected_off_idx"] = int(sel_rows[0])

    sel_off = st.session_state.get("personal_data_selected_off_idx")
    if off_df is not None and sel_off is not None and not off_df.empty:
        sel_off = max(0, min(int(sel_off), len(off_df) - 1))
        picked = off_df.iloc[sel_off]
        deck_key = "|".join([picked["Unit #1"], picked["Unit #2"], picked["Unit #3"]])

        st.divider()
        st.subheader("Offense Logs")
        st.caption(f"Selected Offense: {picked['Unit #1']} / {picked['Unit #2']} / {picked['Unit #3']}")

        log_limit = st.number_input("Max offense log rows", 10, 500, 200, 10, key="personal_offense_log_limit")
        logs = get_personal_offense_logs(wizard, deck_key, limit=int(log_limit))

        if logs.empty:
            st.info("해당 공덱 로그가 없습니다.")
        else:
            st.dataframe(logs, use_container_width=True, hide_index=True)

    st.divider()

    st.subheader("Top Defense")
    if def_df is None or (hasattr(def_df, "empty") and def_df.empty):
        st.info("방어 기록이 없습니다.")
    else:
        event = st.dataframe(
            def_df[["Unit #1", "Unit #2", "Unit #3", "Summary", "Win Rate", "total"]],
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            key="personal_defense_table",
        )

        sel_rows = []
        if event is not None and hasattr(event, "selection"):
            sel_rows = event.selection.get("rows", []) or []
        if sel_rows:
            st.session_state["personal_data_selected_def_idx"] = int(sel_rows[0])

    sel_def = st.session_state.get("personal_data_selected_def_idx")
    if def_df is not None and sel_def is not None and not def_df.empty:
        sel_def = max(0, min(int(sel_def), len(def_df) - 1))
        picked = def_df.iloc[sel_def]
        deck_key = "|".join([picked["Unit #1"], picked["Unit #2"], picked["Unit #3"]])

        st.divider()
        st.subheader("Defense Logs")
        st.caption(f"Selected Defense: {picked['Unit #1']} / {picked['Unit #2']} / {picked['Unit #3']}")

        log_limit = st.number_input("Max defense log rows", 10, 500, 200, 10, key="personal_defense_log_limit")
        logs = get_personal_defense_logs(wizard, deck_key, limit=int(log_limit))

        if logs.empty:
            st.info("해당 방덱 로그가 없습니다.")
        else:
            st.dataframe(logs, use_container_width=True, hide_index=True)
