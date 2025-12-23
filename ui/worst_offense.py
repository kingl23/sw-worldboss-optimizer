# ui/worst_offense.py
import streamlit as st
from ui.auth import require_access_or_stop
from data.siege_data import build_worst_offense_list, get_offense_stats_by_defense

def _norm(s: str) -> str:
    if s is None:
        return ""
    s = str(s)
    s = s.replace("\u200b", "")          # zero-width space
    s = re.sub(r"\s+", " ", s).strip()   # normalize whitespace
    return s


def render_worst_offense_tab():
    st.subheader("Worst Offense List")

    with st.form("worst_off_form"):
        col1, col2 = st.columns(2)
        cutoff = col1.number_input("최소 경기 수 (cutoff)", 1, 100, 4, 1, key="wo_cutoff")
        top_n  = col2.number_input("표시 개수 (Top N)", 1, 200, 50, 5, key="wo_top_n")
        submitted = st.form_submit_button("Search")



    # =========================
    # Debug helper (편하게)
    # =========================
    with st.expander("Debug: 특정 방덱/조합이 왜 안 보이는지 확인", expanded=False):
        st.caption("def_key 또는 유닛 3개를 입력해서 DB/쿼리 결과에서 어디서 빠지는지 한 번에 확인합니다.")

        c1, c2 = st.columns(2)
        dbg_def_key = c1.text_input("def_key로 검색", value="", key="dbg_def_key")
        dbg_units = c2.text_input("유닛 3개로 검색 (예: 암에전,암토템,풍젠이츠)", value="", key="dbg_units")

        run_dbg = st.button("Run Debug", key="dbg_run")

        if run_dbg:
            require_access_or_stop("Worst Offense Debug")

            # 1) base(=build_worst_offense_list 결과) 준비
            base = build_worst_offense_list(cutoff=int(st.session_state.get("wo_cutoff", 4)))

            # 입력 파싱
            u1=u2=u3=""
            if dbg_units.strip():
                parts = [p.strip() for p in dbg_units.split(",")]
                if len(parts) >= 1: u1 = parts[0]
                if len(parts) >= 2: u2 = parts[1]
                if len(parts) >= 3: u3 = parts[2]

            # 2) base에서 찾기(문자열 정규화 포함)
            base_hit = None
            if base is not None and not base.empty:
                tmp = base.copy()
                for col in ["def_key","d1","d2","d3","off_key","o1","o2","o3"]:
                    if col in tmp.columns:
                        tmp[col] = tmp[col].map(_norm)

                if dbg_def_key.strip() and "def_key" in tmp.columns:
                    key = _norm(dbg_def_key)
                    base_hit = tmp[tmp["def_key"] == key]
                elif u1 and "d1" in tmp.columns:
                    base_hit = tmp[(tmp["d1"] == _norm(u1)) & (tmp["d2"] == _norm(u2)) & (tmp["d3"] == _norm(u3))]

            st.markdown("### 1) build_worst_offense_list() 결과(base)에서 존재?")
            if base_hit is None or base_hit.empty:
                st.error("base 결과에 없음 → (쿼리/조인/필터)에서 이미 탈락")
            else:
                st.success(f"base에 {len(base_hit)}건 존재")
                st.dataframe(base_hit.head(50), use_container_width=True)

            # 3) DB에서 직접 조회(가장 확실)
            st.markdown("### 2) DB(defense_list / defense_matchups)에서 직접 존재 확인")
            # 아래 두 함수는 data 레이어에 '직접 SQL 실행' 헬퍼가 있어야 합니다.
            # 없다면, 기존 supabase client 사용 방식에 맞춰서 동일하게 구현하면 됩니다.
            from data.siege_data import debug_lookup_defense  # 새로 만들 함수(아래 참고)

            db_res = debug_lookup_defense(def_key=dbg_def_key.strip() or None, d1=u1 or None, d2=u2 or None, d3=u3 or None)
            st.json(db_res)



    
    # ✅ Search 눌렀을 때만 DB 조회해서 session에 저장
    if submitted:        
        require_access_or_stop("Worst Offense Search")
        
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

        # 선택도 초기화(원하면 유지해도 됨)
        st.session_state["wo_selected_idx"] = None

    # ✅ rerun(행 선택) 시에도 session에 저장된 df로 계속 렌더
    df = st.session_state.get("wo_df", None)
    if df is None or df is False or (hasattr(df, "empty") and df.empty):
        st.info("조건을 설정한 뒤 Search를 눌러주세요.")
        return

    # 리스트 표시 + 선택
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

    # 상세 출력
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
