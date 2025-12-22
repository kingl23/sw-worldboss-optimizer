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


# -------------------------
# UI helpers (Cards)
# -------------------------
def _badge_style(win_rate: float) -> str:
    try:
        wr = float(win_rate)
    except Exception:
        wr = 0.0

    # 필요하면 기준 조정 가능
    if wr >= 70:
        return "background:#00cc44;color:#fff;"
    if wr >= 50:
        return "background:#66ff66;color:#000;"
    if wr >= 30:
        return "background:#ffff00;color:#000;"
    return "background:#ff0000;color:#fff;"


def _render_offense_cards(df: pd.DataFrame, limit: int):
    if df is None or df.empty:
        st.info("해당 방덱에 대한 매치업 데이터가 없습니다.")
        return

    d = df.copy()

    # offense 표시용
    def to_offense(r):
        parts = [r.get("o1", ""), r.get("o2", ""), r.get("o3", "")]
        parts = [p for p in parts if p]
        return " / ".join(parts)

    d["offense"] = d.apply(to_offense, axis=1)

    # 필드 보정
    if "total" not in d.columns:
        d["total"] = d.get("win", 0) + d.get("lose", 0)
    if "win_rate" not in d.columns:
        d["win_rate"] = d.apply(
            lambda r: (r["win"] / r["total"] * 100) if r["total"] else 0,
            axis=1,
        )

    d = d.sort_values(["total", "win_rate"], ascending=[False, False]).head(int(limit))

    st.markdown(
        """
        <style>
        .card-grid {
          display: grid;
          grid-template-columns: repeat(2, minmax(320px, 1fr));
          gap: 12px;
          margin-top: 10px;
        }
        @media (max-width: 900px) {
          .card-grid { grid-template-columns: 1fr; }
        }
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
        .pill {
          padding: 4px 10px;
          border-radius: 999px;
          font-size: 12px;
          font-weight: 700;
          display: inline-block;
          white-space: nowrap;
        }
        .meta {
          font-size: 12px;
          opacity: 0.85;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # 카드 영역
    blocks = ['<div class="card-grid">']
    for i, row in enumerate(d.to_dict(orient="records"), start=1):
        offense = row.get("offense", "")
        win = int(row.get("win", 0))
        lose = int(row.get("lose", 0))
        total = int(row.get("total", win + lose))
        win_rate = float(row.get("win_rate", 0))

        pill_style = _badge_style(win_rate)
        summary = f"{win}W-{lose}L"
        wr_text = f"{win_rate:.0f}%"

        blocks.append(
            f"""
            <div class="card">
              <div class="card-title">{i}. {offense}</div>
              <div class="card-row">
                <span class="meta">{summary} · {total} games</span>
                <span class="pill" style="{pill_style}">{wr_text}</span>
              </div>
            </div>
            """
        )
    blocks.append("</div>")
    st.markdown("".join(blocks), unsafe_allow_html=True)

    # 펼치기(상세) – 지금은 placeholder, 나중에 여기만 채우면 됨
    st.divider()
    st.caption("상세 보기 (추후 확장)")

    for i, row in enumerate(d.to_dict(orient="records"), start=1):
        offense = row.get("offense", "")
        with st.expander(f"#{i} 상세: {offense}", expanded=False):
            st.write("여기에 나중에 상세 내용을 넣으면 됩니다.")


def render_siege_tab():
    st.subheader("Siege")

    col1, col2, col3 = st.columns(3)

    u1 = col1.selectbox("Unit #1 (Leader)", [""] + get_first_units())

    u2_opts = [""] + (get_second_units(u1) if u1 else [])
    u2 = col2.selectbox("Unit #2", u2_opts)

    u3_opts = [""] + (get_third_units(u1, u2) if (u1 and u2) else [])
    u3 = col3.selectbox("Unit #3", u3_opts)

    # limit + search 같은 행
    left, right = st.columns([6, 1.5], vertical_alignment="bottom")
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

        # defense key 제거, 자연어만
        st.markdown(f"**Defense:** {u1} / {u2} / {u3}")

        _render_offense_cards(df, limit=int(limit))
    else:
        st.info("유닛 3개를 선택한 후 Search를 눌러주세요.")
