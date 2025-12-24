from __future__ import annotations

import streamlit as st

from config.settings import WIZARD_NAMES
from services.personal_data_service import (
    get_offense_deck_details,
    get_record_summary,
    get_top_defense_decks,
    get_top_offense_decks,
)


def _deck_label(row) -> str:
    return f"{row['몬1']} / {row['몬2']} / {row['몬3']}"


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
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        labels = [_deck_label(row) for _, row in df.iterrows()]
        label_map = {label: key for label, key in zip(labels, df["key"].tolist())}
        selected_label = st.selectbox(
            "덱 선택",
            options=[""] + labels,
            index=0,
            key=f"{table_key}_fallback",
        )
        if selected_label:
            return label_map[selected_label]
        return None


def render_personal_data_tab():
    st.subheader("Personal Data")

    wizard_name = st.selectbox(
        "Wizard",
        options=[""] + WIZARD_NAMES,
        index=0,
        key="personal_wizard_select",
    )

    if not wizard_name:
        st.info("Wizard를 선택해 주세요.")
        return

    st.markdown("### 전적 요약")
    summary_df = get_record_summary(wizard_name)
    if summary_df.empty:
        st.info("전적 요약 데이터가 없습니다.")
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
        st.info("Top Offense 덱 데이터가 없습니다.")
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
        st.info("Top Defense 덱 데이터가 없습니다.")
    else:
        st.dataframe(
            def_df.drop(columns=["key"]).reset_index(drop=True),
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    st.markdown("### Offense 덱 상세 로그")
    if not selected_key:
        st.info("Top Offense 덱에서 한 줄을 선택하면 상세 로그가 표시됩니다.")
        return

    detail_limit = st.number_input(
        "상세 로그 Limit",
        min_value=1,
        max_value=500,
        value=100,
        step=10,
        key="personal_detail_limit",
    )

    detail_df = get_offense_deck_details(wizard_name, selected_key, int(detail_limit))
    if detail_df.empty:
        st.info("선택한 덱의 상세 로그가 없습니다.")
        return

    st.dataframe(detail_df, use_container_width=True, hide_index=True)
