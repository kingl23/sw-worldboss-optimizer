from __future__ import annotations

import streamlit as st

from config.settings import WIZARD_NAMES
from ui.auth import require_access_or_stop
from services.personal_data_service import (
    get_offense_deck_details,
    get_record_summary,
    get_top_defense_decks,
    get_top_offense_decks,
)


def _deck_label(row) -> str:
    return f"{row['Unit #1']} / {row['Unit #2']} / {row['Unit #3']}"


def _select_offense_key(df, table_key: str) -> str | None:
    df = df.reset_index(drop=True)
    df_display = df.drop(columns=["key"]).reset_index(drop=True)

    try:
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            selection_mode="single-row",
            on_select="rerun",
            key=table_key,
        )
        selection = st.session_state.get(table_key, {}).get("selection", {})
        rows = selection.get("rows", [])
        if rows:
            return df.iloc[rows[0]]["key"]
        return None
    except TypeError:
        # fallback: selection_mode 미지원 환경
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        labels = [_deck_label(row) for _, row in df.iterrows()]
        label_map = {label: key for label, key in zip(labels, df["key"].tolist())}
        selected_label = st.selectbox(
            "Select Deck",
            options=[""] + labels,
            index=0,
            key=f"{table_key}_fallback",
        )
        if selected_label:
            return label_map[selected_label]
        return None


def render_personal_data_tab():
    st.subheader("Personal Data")

    # --- state keys ---
    run_key = "personal_data_run"
    wizard_key = "personal_wizard_select"
    last_wizard_key = "personal_last_wizard"

    # wizard selection
    wizard_name = st.selectbox(
        "Wizard",
        options=[""] + WIZARD_NAMES,
        index=0,
        key=wizard_key,
    )

    # reset when wizard changes
    if st.session_state.get(last_wizard_key) != wizard_name:
        st.session_state[last_wizard_key] = wizard_name
        st.session_state[run_key] = False
        # reset selected deck state
        st.session_state.pop("personal_offense_table", None)
        st.session_state.pop("personal_offense_table_fallback", None)

    if not wizard_name:
        st.info("Select a wizard.")
        return

    # search button
    cols = st.columns([1, 3])
    with cols[0]:
        clicked = st.button("Search", type="primary", use_container_width=True, key="personal_search_btn")

    if clicked:
        # 버튼 클릭 시에만 access gate
        if not require_access_or_stop("personal_data"):
            return
        st.session_state[run_key] = True

    # hide results until search runs
    if not st.session_state.get(run_key, False):
        st.info("Click Search to load data.")
        return

    # --- 이하 결과 렌더 ---
    st.markdown("### Record Summary")
    summary_df = get_record_summary(wizard_name)
    if summary_df.empty:
        st.info("No record summary data available.")
    else:
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### Top Offense Decks")
    off_limit = st.number_input(
        "Top Offense Limit",
        min_value=1,
        max_value=200,
        value=10,
        step=1,
        key="personal_offense_limit",
    )
    off_df = get_top_offense_decks(wizard_name, int(off_limit))
    selected_key = None
    if off_df.empty:
        st.info("No top offense deck data available.")
    else:
        selected_key = _select_offense_key(off_df, "personal_offense_table")

    st.divider()

    st.markdown("### Top Defense Decks")
    def_limit = st.number_input(
        "Top Defense Limit",
        min_value=1,
        max_value=200,
        value=10,
        step=1,
        key="personal_defense_limit",
    )
    def_df = get_top_defense_decks(wizard_name, int(def_limit))
    if def_df.empty:
        st.info("No top defense deck data available.")
    else:
        st.dataframe(
            def_df.drop(columns=["key"]).reset_index(drop=True),
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    st.markdown("### Offense Deck Detail Logs")
    if not selected_key:
        st.info("Select a row from Top Offense Decks to see detail logs.")
        return

    detail_limit = st.number_input(
        "Detail Log Limit",
        min_value=1,
        max_value=500,
        value=100,
        step=10,
        key="personal_detail_limit",
    )

    detail_df = get_offense_deck_details(wizard_name, selected_key, int(detail_limit))
    if detail_df.empty:
        st.info("No detail logs available for the selected deck.")
        return

    st.dataframe(detail_df, use_container_width=True, hide_index=True)
