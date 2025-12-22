# ui/worst_offense.py
import streamlit as st
from data.siege_data import build_worst_offense_list


def render_worst_offense_tab():
    st.subheader("Worst offense List")

    with st.form("worst_def_form"):
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

    df = build_worst_offense_list(cutoff=int(cutoff))

    if df.empty:
        st.info("조건에 맞는 방덱 데이터가 없습니다.")
        return

    df = (
        df.sort_values(
            ["win_rate", "total"],
            ascending=[False, False]
        )
        .head(int(top_n))
        .copy()
    )


    wins = df["lose"]
    losses = df["win"]
    
    df["Win Rate"] = (wins / df["total"] * 100).round(2).astype(str) + "%"
    df["Summary"] = wins.astype(int).astype(str) + "W-" + losses.astype(int).astype(str) + "L"
    
    output = df.rename(
        columns={
            "d1": "Unit #1",
            "d2": "Unit #2",
            "d3": "Unit #3",
            "total": "Total",
        }
    )
    
    st.dataframe(
        output[["Unit #1", "Unit #2", "Unit #3", "Summary", "Win Rate", "Total"]],
        use_container_width=True,
        hide_index=True,
    )

