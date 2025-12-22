import textwrap
import streamlit as st
import pandas as pd
from supabase import create_client


def sb():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_ANON_KEY"])


def require_access_or_stop(context: str):
    allowed = set(st.secrets.get("ACCESS_KEYS", []))
    key = st.session_state.get("access_key_input", "")
    if key not in allowed:
        st.warning(f"Access Key required for {context}.")
        st.stop()


def make_def_key(a: str, b: str, c: str) -> str:
    # a는 leader(고정), b/c는 순서 무관
    rest = sorted([x for x in [b, c] if x])
    return "|".join([a] + rest)


@st.cache_data(ttl=3600)
def get_first_units():
    res = sb().table("defense_list").select("a").execute()
    return sorted({r["a"] for r in (res.data or []) if r.get("a")})


@st.cache_data(ttl=3600)
def get_second_units(a: str):
    res = sb().table("defense_list").select("b,c").eq("a", a).execute()
    s = set()
    for r in (res.data or []):
        if r.get("b"):
            s.add(r["b"])
        if r.get("c"):
            s.add(r["c"])
    s.discard("")
    return sorted(s)


@st.cache_data(ttl=3600)
def get_third_units(a: str, b: str):
    res = sb().table("defense_list").select("b,c").eq("a", a).execute()
    s = set()
    for r in (res.data or []):
        bb, cc = r.get("b"), r.get("c")
        if bb == b and cc:
            s.add(cc)
        if cc == b and bb:
            s.add(bb)
    s.discard("")
    return sorted(s)


@st.cache_data(ttl=120)
def get_matchups(def_key: str, limit: int = 200):
    res = (
        sb()
        .table("defense_matchups")
        .select("o1,o2,o3,win,lose,total,win_rate")
        .eq("def_key", def_key)
        .order("total", desc=True)
        .order("win_rate", desc=True)
        .limit(limit)
        .execute()
    )
    return pd.DataFrame(res.data or [])

@st.cache_data(ttl=120)
def get_matchup_details(def_key: str, o1: str, o2: str, o3: str, limit: int = 50):
    res = (
        sb()
        .table("defense_battles")
        .select("battle_time, result, attacker, note")
        .eq("def_key", def_key)
        .eq("o1", o1).eq("o2", o2).eq("o3", o3)
        .order("battle_time", desc=True)
        .limit(limit)
        .execute()
    )
    return pd.DataFrame(res.data or [])


# -------------------------
# UI helpers (Cards)
# -------------------------

def _badge_style(win_rate: float) -> str:
    try:
        wr = float(win_rate)
    except Exception:
        wr = 0.0

    if wr >= 70:
        return "background:#00cc44;color:#fff;"
    if wr >= 50:
        return "background:#66ff66;color:#000;"
    if wr >= 30:
        return "background:#ffff00;color:#000;"
    return "background:#ff0000;color:#fff;"


def _normalize_matchups(df: pd.DataFrame, limit: int) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    d = df.copy()

    def to_offense(r):
        parts = [r.get("o1", ""), r.get("o2", ""), r.get("o3", "")]
        parts = [p for p in parts if p]
        return " / ".join(parts)

    d["offense"] = d.apply(to_offense, axis=1)

    if "total" not in d.columns:
        d["total"] = d.get("win", 0) + d.get("lose", 0)

    if "win_rate" not in d.columns:
        d["win_rate"] = d.apply(
            lambda r: (r.get("win", 0) / r["total"] * 100) if r["total"] else 0,
            axis=1,
        )

    d = d.sort_values(["total", "win_rate"], ascending=[False, False]).head(int(limit))
    d = d.reset_index(drop=True)
    return d


def render_matchups_master_detail(df: pd.DataFrame, limit: int, def_key: str):
    d = _normalize_matchups(df, limit)
    if d.empty:
        st.info("해당 방덱에 대한 매치업 데이터가 없습니다.")
        return

    # 선택 상태 초기화
    if "selected_idx" not in st.session_state:
        st.session_state["selected_idx"] = 0

    # CSS: 좌측 카드 1열 리스트 + 버튼 스타일
    st.markdown(
        textwrap.dedent(
            """
            <style>
              .card-list { display: flex; flex-direction: column; gap: 10px; }
              .card {
                border: 1px solid rgba(49, 51, 63, 0.2);
                border-radius: 12px;
                padding: 12px 14px;
                background: rgba(255,255,255,0.02);
              }
              .card-title {
                font-weight: 700;
                font-size: 15px;
                margin-bottom: 6px;
              }
              .card-row {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 10px;
                margin-top: 6px;
              }
              .meta { font-size: 12px; opacity: 0.85; }
              .pill {
                padding: 4px 10px;
                border-radius: 999px;
                font-size: 12px;
                font-weight: 700;
                display: inline-block;
                white-space: nowrap;
              }
              /* Streamlit button spacing tighten */
              div.stButton > button {
                padding: 0.35rem 0.6rem;
                border-radius: 10px;
              }
            </style>
            """
        ).strip(),
        unsafe_allow_html=True,
    )

    # 전체 레이아웃: 좌(마스터) / 우(디테일)
    left, right = st.columns([0.48, 0.52], gap="large")

    with left:
        st.subheader("추천 공덱")
        st.caption("카드의 '상세보기'를 누르면 오른쪽에 상세가 표시됩니다.")

        # 카드 1열 리스트: 각 카드 아래에 '상세보기' 버튼을 둬서 클릭 이벤트를 안정적으로 처리
        for idx, row in enumerate(d.to_dict(orient="records"), start=0):
            offense = row.get("offense", "")
            win = int(row.get("win", 0) or 0)
            lose = int(row.get("lose", 0) or 0)
            total = int(row.get("total", win + lose) or (win + lose))
            win_rate = float(row.get("win_rate", 0) or 0)

            pill_style = _badge_style(win_rate)
            summary = f"{win}W-{lose}L"
            wr_text = f"{win_rate:.0f}%"

            # 카드 본문 (HTML)
            st.markdown(
                textwrap.dedent(
                    f"""
                    <div class="card">
                      <div class="card-title">#{idx+1} {offense}</div>
                      <div class="card-row">
                        <span class="meta">{summary} · {total} games</span>
                        <span class="pill" style="{pill_style}">{wr_text}</span>
                      </div>
                    </div>
                    """
                ).strip(),
                unsafe_allow_html=True,
            )

            # 카드 액션: 상세보기 버튼
            cols = st.columns([0.7, 0.3])
            with cols[1]:
                if st.button("상세보기", key=f"detail_btn_{idx}", use_container_width=True):
                    st.session_state["selected_idx"] = idx

    with right:
        idx = int(st.session_state.get("selected_idx", 0))
        idx = max(0, min(idx, len(d) - 1))
        row = d.iloc[idx].to_dict()

        offense = row.get("offense", "")
        win = int(row.get("win", 0) or 0)
        lose = int(row.get("lose", 0) or 0)
        total = int(row.get("total", win + lose) or (win + lose))
        win_rate = float(row.get("win_rate", 0) or 0)

        st.subheader("상세")
        st.markdown(f"### #{idx+1} {offense}")
        st.write(f"- 결과: **{win}W-{lose}L** (총 {total}판)")
        st.write(f"- 승률: **{win_rate:.1f}%**")

        o1, o2, o3 = row.get("o1", ""), row.get("o2", ""), row.get("o3", "")

        # 예시: 원천 로그 테이블이 있으면 아래를 활성화
        # details_df = get_matchup_details(def_key, o1, o2, o3, limit=30)
        # if details_df.empty:
        #     st.info("상세 전투 로그가 없습니다.")
        # else:
        #     st.dataframe(details_df, use_container_width=True, hide_index=True)

        st.info("상세 데이터(전투 로그/룬/스피드 튜닝 등)를 연결하면 이 영역에 표시됩니다.")
        st.write({"def_key": def_key, "offense_units": [o1, o2, o3]})



def render_siege_tab():
    st.subheader("Siege")

    col1, col2, col3 = st.columns(3)

    u1 = col1.selectbox("Unit #1 (Leader)", [""] + get_first_units())
    u2_opts = [""] + (get_second_units(u1) if u1 else [])
    u2 = col2.selectbox("Unit #2", u2_opts)
    u3_opts = [""] + (get_third_units(u1, u2) if (u1 and u2) else [])
    u3 = col3.selectbox("Unit #3", u3_opts)

    # number_input 폭 줄이기 CSS
    st.markdown(
        """
        <style>
          div[data-testid="stNumberInput"] { max-width: 220px; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([0.35, 0.65], vertical_alignment="bottom")
    with left:
        limit = st.number_input("최대 추천 공덱 수", min_value=5, max_value=200, value=10, step=5)
    with right:
        search = st.button("Search", type="primary")

    if search:
        require_access_or_stop("Siege Search")

        if not (u1 and u2 and u3):
            st.warning("유닛 3개를 모두 선택하세요.")
            st.stop()

        def_key = make_def_key(u1, u2, u3)
        df = get_matchups(def_key, int(limit))

        render_matchups_master_detail(df, limit=int(limit), def_key=def_key)


    else:
        st.info("유닛 3개를 선택한 후 Search를 눌러주세요.")

