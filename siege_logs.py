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
        if r.get("b"): s.add(r["b"])
        if r.get("c"): s.add(r["c"])
    s.discard("")
    return sorted(s)

@st.cache_data(ttl=3600)
def get_third_units(a: str, b: str):
    res = sb().table("defense_list").select("b,c").eq("a", a).execute()
    s = set()
    for r in (res.data or []):
        bb, cc = r.get("b"), r.get("c")
        if bb == b and cc: s.add(cc)
        if cc == b and bb: s.add(bb)
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

def render_siege_tab():
    st.subheader("Siege")

    col1, col2, col3 = st.columns(3)

    u1 = col1.selectbox("Unit #1 (Leader)", [""] + get_first_units())

    u2_opts = [""] + (get_second_units(u1) if u1 else [])
    u2 = col2.selectbox("Unit #2", u2_opts)

    u3_opts = [""] + (get_third_units(u1, u2) if (u1 and u2) else [])
    u3 = col3.selectbox("Unit #3", u3_opts)

    limit = st.number_input("최대 추천 공덱 수", min_value=5, max_value=200, value=10, step=5)

    if st.button("Search", type="primary"):
        require_access_or_stop("Siege Search")

        if not (u1 and u2 and u3):
            st.warning("유닛 3개를 모두 선택하세요.")
            st.stop()

        def_key = make_def_key(u1, u2, u3)
        df = get_matchups(def_key, int(limit))

        st.markdown(f"**Defense key:** `{def_key}`")
        if df.empty:
            st.info("해당 방덱에 대한 매치업 데이터가 없습니다.")
            return

        # 보기용 컬럼
        df["offense"] = df.apply(lambda r: " / ".join([r["o1"], r.get("o2") or "", r.get("o3") or ""]).strip(" /"), axis=1)
        df = df[["offense", "win", "lose", "total", "win_rate"]]
        st.dataframe(df, use_container_width=True)
