# ui/worst_offense.py
import streamlit as st
from data.siege_data import build_worst_offense_list, get_offense_stats_by_defense

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



# 기존 리스트 테이블 (행 선택 가능)
event = st.dataframe(
    output[["Unit #1", "Unit #2", "Unit #3", "Summary", "Win Rate", "Total"]],
    use_container_width=True,
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row",
    key="worst_def_table",
)

# 선택된 행이 있으면 아래에 블럭 출력
sel_rows = event.selection.get("rows", []) if event and hasattr(event, "selection") else []
if sel_rows:
    i = int(sel_rows[0])
    picked = output.iloc[i]

    def1 = picked["Unit #1"]
    def2 = picked["Unit #2"]
    def3 = picked["Unit #3"]

    st.divider()
    st.subheader("Offense stats vs selected defense")
    st.write(f"Selected Defense: **{def1} / {def2} / {def3}**")

    # (선택) 여기서 limit를 별도 입력으로 받을 수도 있음
    off_limit = st.number_input("Max offense rows", min_value=5, max_value=200, value=50, step=5, key="off_limit")

    off_df = get_offense_stats_by_defense(def1, def2, def3, limit=int(off_limit))
    if off_df.empty:
        st.info("No offense records found for this defense.")
    else:
        st.dataframe(
            off_df[["Unit #1", "Unit #2", "Unit #3", "wins", "losses", "Win Rate", "Summary", "total"]],
            use_container_width=True,
            hide_index=True,
        )

