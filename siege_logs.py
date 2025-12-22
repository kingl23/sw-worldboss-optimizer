import streamlit as st
import pandas as pd
from supabase import create_client

# ---------------------------
# Supabase client
# ---------------------------
def sb():
    if "SUPABASE_URL" not in st.secrets or "SUPABASE_ANON_KEY" not in st.secrets:
        st.error("Streamlit Secrets에 SUPABASE_URL / SUPABASE_ANON_KEY가 필요합니다.")
        st.stop()
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_ANON_KEY"])


# ---------------------------
# DefenseList 기반 종속 드롭다운
# defense_list 테이블 스키마 가정:
#  - a (text) : 1번 유닛(고정 자리)
#  - b (text) : 2/3 유닛 후보
#  - c (text) : 2/3 유닛 후보
# ---------------------------
@st.cache_data(ttl=3600)
def defense_list_exists() -> bool:
    # defense_list에 1개라도 select 가능하면 존재한다고 판단
    try:
        res = sb().table("defense_list").select("a").limit(1).execute()
        _ = res.data  # 접근만 해도 OK
        return True
    except Exception:
        return False


@st.cache_data(ttl=3600)
def get_first_units():
    """
    helperDefenseList!D열:
    SORT(UNIQUE(FILTER(A <> "")))
    """
    res = sb().table("defense_list").select("a").neq("a", "").execute()
    units = sorted({r["a"] for r in (res.data or []) if r.get("a")})
    return units


@st.cache_data(ttl=3600)
def get_second_units(a: str):
    """
    helperDefenseList!E열:
    A가 선택된 상태에서, {B;C}에서 유니크+정렬
    """
    res = sb().table("defense_list").select("b,c").eq("a", a).execute()
    units = set()
    for r in (res.data or []):
        b = r.get("b")
        c = r.get("c")
        if b:
            units.add(b)
        if c:
            units.add(c)
    units.discard("")
    return sorted(units)


@st.cache_data(ttl=3600)
def get_third_units(a: str, b_selected: str):
    """
    helperDefenseList!F열:
    A, B(=두번째 선택)이 정해진 상태에서
      if b==선택 => c
      if c==선택 => b
    를 유니크+정렬
    """
    res = sb().table("defense_list").select("b,c").eq("a", a).execute()
    units = set()
    for r in (res.data or []):
        b = r.get("b")
        c = r.get("c")
        if b == b_selected and c:
            units.add(c)
        if c == b_selected and b:
            units.add(b)
    units.discard("")
    return sorted(units)


# ---------------------------
# Siege logs query
# siege_logs 테이블: deck1_1..3, deck2_1..3 존재 가정
# 매칭 규칙: 첫 자리는 고정(A), 뒤 2개는 순서 무관(B,C)
# ---------------------------
def _or_clause_for_deck(prefix: str, a: str, b: str, c: str) -> str:
    """
    PostgREST OR 문자열:
    (prefix_1=a AND prefix_2=b AND prefix_3=c) OR (prefix_1=a AND prefix_2=c AND prefix_3=b)
    """
    p1 = f"and({prefix}_1.eq.{a},{prefix}_2.eq.{b},{prefix}_3.eq.{c})"
    p2 = f"and({prefix}_1.eq.{a},{prefix}_2.eq.{c},{prefix}_3.eq.{b})"
    return f"{p1},{p2}"


@st.cache_data(ttl=120)
def query_siege_logs(a: str, b: str, c: str, mode: str, limit: int):
    q = (
        sb()
        .table("siege_logs")
        .select(
            "match_id,log_id,ts,wizard,opp_wizard,opp_guild,result,base,"
            "deck1_1,deck1_2,deck1_3,deck2_1,deck2_2,deck2_3"
        )
        .order("match_id", desc=True)
        .limit(limit)
    )

    if mode == "deck1":
        q = q.or_(_or_clause_for_deck("deck1", a, b, c))
    elif mode == "deck2":
        q = q.or_(_or_clause_for_deck("deck2", a, b, c))
    else:
        clause = _or_clause_for_deck("deck1", a, b, c) + "," + _or_clause_for_deck("deck2", a, b, c)
        q = q.or_(clause)

    res = q.execute()
    data = res.data or []
    return pd.DataFrame(data)


# ---------------------------
# UI
# ---------------------------
def render_siege_tab():
    st.header("Siege")

    # defense_list 테이블이 아직 없으면 안내
    if not defense_list_exists():
        st.error("Supabase에 defense_list 테이블이 없습니다. 먼저 defense_list(a,b,c) 데이터를 DB에 적재해야 합니다.")
        st.info("defense_list가 준비되면 드롭다운(1→2→3)과 조합 검색이 동작합니다.")
        st.stop()

    col1, col2, col3 = st.columns(3)

    first_options = [""] + get_first_units()
    with col1:
        u1 = st.selectbox("Unit #1 (고정)", options=first_options)

    second_options = [""]
    if u1:
        second_options += get_second_units(u1)
    with col2:
        u2 = st.selectbox("Unit #2", options=second_options)

    third_options = [""]
    if u1 and u2:
        third_options += get_third_units(u1, u2)
    with col3:
        u3 = st.selectbox("Unit #3", options=third_options)

    st.divider()

    mode = st.radio(
        "검색 대상 덱",
        options=["deck1", "deck2", "both"],
        horizontal=True,
        format_func=lambda x: {"deck1": "Deck 1", "deck2": "Deck 2", "both": "Deck 1 or 2"}[x],
    )

    limit = st.number_input("최대 조회 행 수", min_value=100, max_value=20000, value=5000, step=100)

    if st.button("Search", type="primary"):
        if not u1 or not u2 or not u3:
            st.warning("유닛 3개를 모두 선택하세요.")
            return
        if len({u1, u2, u3}) < 3:
            st.warning("서로 다른 유닛 3개를 선택하세요.")
            return

        df = query_siege_logs(u1, u2, u3, mode, int(limit))
        st.subheader(f"Result: {len(df):,} rows")

        if df.empty:
            st.info("해당 조합의 로그가 없습니다.")
            return

        cols = [
            "match_id", "log_id", "ts",
            "wizard", "opp_wizard", "opp_guild", "result", "base",
            "deck1_1", "deck1_2", "deck1_3",
            "deck2_1", "deck2_2", "deck2_3",
        ]
        df = df[[c for c in cols if c in df.columns]]

        st.dataframe(df, use_container_width=True)
