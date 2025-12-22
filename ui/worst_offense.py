# ui/worst_offense.py
import streamlit as st
from data.siege_data import build_worst_offense_list, get_offense_stats_by_defense


def render_worst_offense_tab():
    st.subheader("Worst Offense List")

    with st.form("worst_off_form"):
        col1, col2 = st.columns(2)
        cutoff = col1.number_input(
            "최소 경기 수 (cutoff)",
            min_value=1,
            max_value=100,
            value=4,
            step=1,
        )
        top_n = col2.number_input(
            "표시 개수 (Top N)",
            min_value=1,
            max_value=200,
            value=50,
            step=5,
        )
        submitted = st.form_submit_button("Search")

    if not submitted:
        st.info("조건을 설정한 뒤 Search를 눌러주세요.")
        return

    base = build_worst_offense_list(cutoff=int(cutoff))
    if base is None or base.empty:
        st.info("조건에 맞는 데이터가 없습니다.")
        return

    # 정렬/컷
    df = (
        base.sort_values(["win_rate", "total"], ascending=[False, False])
        .head(int(top_n))
        .copy()
        .reset_index(drop=True)
    )

    # 표시 컬럼 생성: Unit #1/2/3, Total
    df["Unit #1"] = df["d1"]
    df["Unit #2"] = df["d2"]
    df["Unit #3"] = df["d3"]
    df["Total"] = df["total"]

    # 공격자 기준 W/L 정상화 (네 build 함수 기준: win=공격자 Lose, lose=공격자 Win)
    wins = df["lose"].fillna(0).astype(int)    # 공격자 Win
    losses = df["win"].fillna(0).astype(int)   # 공격자 Lose
    total = df["total"].fillna(0).astype(int)

    df["Win Rate"] = (wins / total.replace(0, 1) * 100).round(2).map(lambda x: f"{x:.2f}%")
    df["Summary"] = wins.astype(str) + "W-" + losses.astype(str) + "L"

    # ✅ 리스트 테이블 (행 선택 가능)
    event = st.dataframe(
        df[["Unit #1", "Unit #2", "Unit #3", "Summary", "Win Rate", "Total"]],
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="worst_off_table",
    )

    # ✅ 선택된 행이 있으면 아래 블럭 출력
    sel_rows = []
    if event is not None and hasattr(event, "selection"):
        sel_rows = event.selection.get("rows", []) or []

    if not sel_rows:
        return

    i = int(sel_rows[0])
    if i < 0 or i >= len(df):
        return

    picked = df.iloc[i]  # ✅ output 말고 df
    def1 = picked["Unit #1"]
    def2 = picked["Unit #2"]
    def3 = picked["Unit #3"]

    st.divider()
    st.subheader("Offense stats vs selected defense")
    st.write(f"Selected Defense: **{def1} / {def2} / {def3}**")

    off_limit = st.number_input(
        "Max offense rows",
        min_value=5,
        max_value=200,
        value=50,
        step=5,
        key="off_limit",
    )

    off_df = get_offense_stats_by_defense(def1, def2, def3, limit=int(off_limit))
    if off_df is None or off_df.empty:
        st.info("No offense records found for this defense.")
        return

    st.dataframe(
        off_df[["Unit #1", "Unit #2", "Unit #3", "wins", "losses", "Win Rate", "Summary", "total"]],
        use_container_width=True,
        hide_index=True,
    )
