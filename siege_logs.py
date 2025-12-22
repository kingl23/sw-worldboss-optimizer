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


def _sorted3(a: str, b: str, c: str):
    return sorted([x for x in [a, b, c] if x])


@st.cache_data(ttl=120)
def get_siege_loss_logs(match_id: str, o1: str, o2: str, o3: str, limit: int = 200) -> pd.DataFrame:

    a, b, c = _sorted3(o1, o2, o3)
    if not (a and b and c):
        return pd.DataFrame()

    q = (
        sb()
        .table("siege_logs")
        .select(
            "ts, wizard, opp_wizard, opp_guild, result, base, "
            "deck1_1,deck1_2,deck1_3, deck2_1,deck2_2,deck2_3"
        )
        .eq("match_id", match_id)
        .eq("result", "Lose")
    )

    perms = [
        (a, b, c),
        (a, c, b),
        (b, a, c),
        (b, c, a),
        (c, a, b),
        (c, b, a),
    ]
    or_clauses = [f"and(deck1_1.eq.{x},deck1_2.eq.{y},deck1_3.eq.{z})" for x, y, z in perms]
    q = q.or_(",".join(or_clauses))

    res = q.order("ts", desc=True).limit(int(limit)).execute()
    return pd.DataFrame(res.data or [])


# -------------------------
# UI helpers (Cards)
# -------------------------


def _fmt_team(r, a, b, c) -> str:
    parts = [r.get(a, ""), r.get(b, ""), r.get(c, "")]
    parts = [p for p in parts if p]
    return " / ".join(parts)


def render_matchups_master_detail(df: pd.DataFrame, limit: int, def_key: str):
    d = _normalize_matchups(df, limit)
    if d.empty:
        st.info("해당 방덱에 대한 매치업 데이터가 없습니다.")
        return

    # ✅ 상세보기 안 눌렀으면 None → 오른쪽은 빈칸
    if "selected_idx" not in st.session_state:
        st.session_state["selected_idx"] = None

    st.markdown(
        textwrap.dedent(
            """
            <style>
              .card {
                border: 1px solid rgba(49, 51, 63, 0.2);
                border-radius: 12px;
                padding: 12px 14px;
                background: rgba(255,255,255,0.02);
                margin-bottom: 8px;
              }
              .card-title { font-weight: 700; font-size: 15px; margin-bottom: 6px; }
              .card-row {
                display: flex; align-items: center; justify-content: space-between;
                gap: 10px; margin-top: 6px;
              }
              .meta { font-size: 12px; opacity: 0.85; }
              .pill {
                padding: 4px 10px; border-radius: 999px; font-size: 12px;
                font-weight: 700; display: inline-block; white-space: nowrap;
              }
              div.stButton > button { padding: 0.35rem 0.6rem; border-radius: 10px; }
            </style>
            """
        ).strip(),
        unsafe_allow_html=True,
    )

    left, right = st.columns([0.48, 0.52], gap="large")

    # -------------------------
    # 좌: 카드 1열 리스트 + 상세보기 버튼
    # -------------------------
    with left:
        st.subheader("추천 공덱")
        st.caption("상세보기를 누르면 오른쪽에 Lose 로그가 표시됩니다.")

        for idx, row in enumerate(d.to_dict(orient="records"), start=0):
            offense = row.get("offense", "")
            win = int(row.get("win", 0) or 0)
            lose = int(row.get("lose", 0) or 0)
            total = int(row.get("total", win + lose) or (win + lose))
            win_rate = float(row.get("win_rate", 0) or 0)

            pill_style = _badge_style(win_rate)
            summary = f"{win}W-{lose}L"
            wr_text = f"{win_rate:.0f}%"

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

            btn_cols = st.columns([0.72, 0.28])
            with btn_cols[1]:
                if st.button("상세보기", key=f"detail_btn_{idx}", use_container_width=True):
                    st.session_state["selected_idx"] = idx

    # -------------------------
    # 우: 상세 (선택 전 = 빈칸 / 선택 후 = Lose 로그)
    # -------------------------
    with right:
        sel = st.session_state.get("selected_idx", None)
        if sel is None:
            # ✅ 완전 빈칸
            st.empty()
            return

        sel = int(sel)
        sel = max(0, min(sel, len(d) - 1))
        row = d.iloc[sel].to_dict()

        offense = row.get("offense", "")
        win = int(row.get("win", 0) or 0)
        lose = int(row.get("lose", 0) or 0)
        total = int(row.get("total", win + lose) or (win + lose))
        win_rate = float(row.get("win_rate", 0) or 0)

        o1, o2, o3 = row.get("o1", ""), row.get("o2", ""), row.get("o3", "")

        st.subheader("상세")
        st.markdown(f"### #{sel+1} {offense}")
        st.write(f"- 결과: **{win}W-{lose}L** (총 {total}판)")
        st.write(f"- 승률: **{win_rate:.1f}%**")
        st.divider()

        st.markdown("#### Lose 로그 (Siege Logs)")
        logs = get_siege_loss_logs(def_key, o1, o2, o3, limit=200)

        if logs.empty:
            st.info("해당 조합의 Lose 로그가 없습니다.")
            return

        logs = logs.copy()
        logs["공격덱"] = logs.apply(lambda r: _fmt_team(r, "deck1_1", "deck1_2", "deck1_3"), axis=1)
        logs["방어덱"] = logs.apply(lambda r: _fmt_team(r, "deck2_1", "deck2_2", "deck2_3"), axis=1)

        logs = logs.rename(
            columns={
                "ts": "시간",
                "wizard": "공격자",
                "opp_wizard": "방어자",
                "opp_guild": "상대길드",
                "base": "거점",
            }
        )

        # 요구사항: 공격자 공격덱(3) / 방어자 방어덱(3) / 상대길드 나열
        cols = [c for c in ["시간", "상대길드", "공격자", "공격덱", "방어자", "방어덱", "거점"] if c in logs.columns]

        st.dataframe(
            logs[cols],
            use_container_width=True,
            hide_index=True,
        )



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

