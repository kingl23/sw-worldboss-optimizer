from __future__ import annotations

import streamlit as st

from sw_helper.config.settings import WIZARD_NAMES
from sw_helper.ui.auth import require_access_or_stop
from sw_helper.siege.services.personal_data_service import (
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
        # fallback: selection_mode 미지원 환경
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

    # --- state keys ---
    run_key = "personal_data_run"
    wizard_key = "personal_wizard_select"
    last_wizard_key = "personal_last_wizard"

    # wizard 선택
    wizard_name = st.selectbox(
        "Wizard",
        options=[""] + WIZARD_NAMES,
        index=0,
        key=wizard_key,
    )

    # wizard 변경 시 이전 run 상태 리셋
    if st.session_state.get(last_wizard_key) != wizard_name:
        st.session_state[last_wizard_key] = wizard_name
        st.session_state[run_key] = False
        # 선택된 덱도 초기화(선택 테이블 state가 남는 것 방지)
        st.session_state.pop("personal_offense_table", None)
        st.session_state.pop("personal_offense_table_fallback", None)

    if not wizard_name:
        st.info("Wizard를 선택해 주세요.")
        return

    # 검색 버튼
    cols = st.columns([1, 3])
    with cols[0]:
        clicked = st.button("Search", type="primary", use_container_width=True, key="personal_search_btn")

    if clicked:
        # 버튼 클릭 시에만 access gate
        if not require_access_or_stop("personal_data"):
            return
        st.session_state[run_key] = True

    # 버튼 누르기 전에는 결과 숨김
    if not st.session_state.get(run_key, False):
        st.info("Search를 눌러 데이터를 조회하세요.")
        return

    # --- 이하 결과 렌더 ---
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
