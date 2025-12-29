import textwrap
import streamlit as st
import pandas as pd
from ui.auth import require_access_or_stop

from data.siege_trend import build_cumulative_trend_df
from ui.siege_trend_chart import render_cumulative_trend_chart
from services.supabase_client import get_supabase_client
from services.siege_image_service import get_siege_image_url


# -------------------------
# Supabase helpers
# -------------------------
def sb():
    return get_supabase_client()


def make_def_key(a: str, b: str, c: str) -> str:
    # a는 leader(고정), b/c는 순서 무관
    rest = sorted([x for x in [b, c] if x])
    return "|".join([a] + rest)

@st.cache_data(ttl=120)
def get_siege_logs_for_defense(def_key: str, limit: int = 5000) -> pd.DataFrame:
    parts = [p for p in (def_key or "").split("|") if p]
    if len(parts) < 3:
        return pd.DataFrame()
    d1, d2, d3 = parts[0], parts[1], parts[2]

    q = (
        sb()
        .table("siege_logs")
        .select("match_id, ts, result, deck1_1,deck1_2,deck1_3, deck2_1,deck2_2,deck2_3")
        .in_("result", ["Win", "Lose"])
    )

    # 방덱은 2/3 자리 순서 무관
    def_perms = [(d1, d2, d3), (d1, d3, d2)]
    or_clauses = [
        f"and(deck2_1.eq.{_q(a)},deck2_2.eq.{_q(b)},deck2_3.eq.{_q(c)})"
        for a, b, c in def_perms
    ]

    res = q.or_(",".join(or_clauses)).order("match_id", desc=False).limit(int(limit)).execute()
    return pd.DataFrame(res.data or [])



# -------------------------
# Cached option loaders
# -------------------------
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


# -------------------------
# Matchups
# -------------------------
@st.cache_data(ttl=120)
def get_matchups(def_key: str, limit: int = 200):
    res = (
        sb()
        .table("defense_matchups")
        .select("o1,o2,o3,win,lose,total,win_rate")
        .eq("def_key", def_key)
        .order("total", desc=True)
        .order("win_rate", desc=True)
        .limit(int(limit))
        .execute()
    )
    return pd.DataFrame(res.data or [])


def _normalize_matchups(df: pd.DataFrame, limit: int) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    d = df.copy()

    # 필요한 컬럼 보장
    for col in ["o1", "o2", "o3", "win", "lose", "total", "win_rate"]:
        if col not in d.columns:
            d[col] = "" if col in ["o1", "o2", "o3"] else 0

    # 숫자 컬럼 안정화
    d["win"] = pd.to_numeric(d["win"], errors="coerce").fillna(0).astype(int)
    d["lose"] = pd.to_numeric(d["lose"], errors="coerce").fillna(0).astype(int)
    d["total"] = pd.to_numeric(d["total"], errors="coerce").fillna(d["win"] + d["lose"]).astype(int)

    if "win_rate" in d.columns:
        d["win_rate"] = pd.to_numeric(d["win_rate"], errors="coerce").fillna(0.0)
    else:
        d["win_rate"] = 0.0

    def to_offense(r):
        parts = [r.get("o1", ""), r.get("o2", ""), r.get("o3", "")]
        parts = [p for p in parts if p]
        return " / ".join(parts)

    d["offense"] = d.apply(to_offense, axis=1)

    # win_rate가 0으로만 들어오거나 total 기반 재계산이 필요한 경우를 대비
    # (이미 테이블에 win_rate가 있더라도, total==0 이거나 None이면 보정)
    def _calc_wr(r):
        t = int(r.get("total", 0) or 0)
        w = int(r.get("win", 0) or 0)
        if t <= 0:
            return 0.0
        return float(w) / float(t) * 100.0

    d["win_rate"] = d.apply(lambda r: _calc_wr(r) if (r.get("win_rate") is None) else float(r.get("win_rate") or 0), axis=1)

    d = d.sort_values(["total", "win_rate"], ascending=[False, False]).head(int(limit)).reset_index(drop=True)
    return d


def _sorted3(a: str, b: str, c: str):
    return sorted([x for x in [a, b, c] if x])


def _q(v: str) -> str:
    """
    postgrest or_ 문자열에서 안전하게 쓰기 위한 값 quoting.
    """
    v = (v or "").replace('"', '\\"')
    return f'"{v}"'


# -------------------------
# Siege loss logs (B안: match_id 필터 제거)
# -------------------------
@st.cache_data(ttl=120)
def get_siege_loss_logs(def_key: str, o1: str, o2: str, o3: str, limit: int = 200) -> pd.DataFrame:
    parts = [p for p in (def_key or "").split("|") if p]
    if len(parts) < 3:
        return pd.DataFrame()

    d1, d2, d3 = parts[0], parts[1], parts[2]

    if not (o1 and o2 and o3):
        return pd.DataFrame()

    base_select = (
        "match_id, ts, wizard, opp_wizard, opp_guild, result, base, "
        "deck1_1,deck1_2,deck1_3, deck2_1,deck2_2,deck2_3"
    )

    perms_off = [(o1, o2, o3), (o1, o3, o2)]
    perms_def = [(d1, d2, d3), (d1, d3, d2)]

    or_clauses = []
    for x, y, z in perms_off:
        for p, q2, r in perms_def:
            or_clauses.append(
                "and("
                f"deck1_1.eq.{_q(x)},deck1_2.eq.{_q(y)},deck1_3.eq.{_q(z)},"
                f"deck2_1.eq.{_q(p)},deck2_2.eq.{_q(q2)},deck2_3.eq.{_q(r)}"
                ")"
            )

    def _fetch_logs(select_fields: str) -> pd.DataFrame:
        res = (
            sb()
            .table("siege_logs")
            .select(select_fields)
            .eq("result", "Lose")
            .or_(",".join(or_clauses))
            .order("ts", desc=True)
            .limit(int(limit))
            .execute()
        )
        return pd.DataFrame(res.data or [])

    try:
        return _fetch_logs(f"match_id, log_id, {base_select.split('match_id, ', 1)[1]}")
    except Exception:
        return _fetch_logs(base_select)


# -------------------------
# UI helpers (Cards)
# -------------------------
def _fmt_team(r, a, b, c) -> str:
    parts = [r.get(a, ""), r.get(b, ""), r.get(c, "")]
    parts = [p for p in parts if p]
    return " / ".join(parts)


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


def render_matchups_master_detail(df: pd.DataFrame, limit: int, def_key: str):

    d = _normalize_matchups(df, limit)
    if d.empty:
        st.info("해당 방덱에 대한 매치업 데이터가 없습니다.")
        return

    st.markdown(
        textwrap.dedent(
            """
            <style>
              .card {
                border: 1px solid rgba(49, 51, 63, 0.2);
                border-radius: 12px;
                padding: 12px 14px;
                background: rgba(255,255,255,0.02);
                margin-bottom: 10px;
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
              /* expander 안쪽 여백을 살짝 줄임(선택) */
              div[data-testid="stExpander"] > details {
                border-radius: 12px;
              }
            </style>
            """
        ).strip(),
        unsafe_allow_html=True,
    )

    st.subheader("추천 공덱")
    st.caption("각 항목의 ‘상세보기’를 열면 바로 아래에 Lose 로그가 펼쳐집니다.")

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

        with st.expander("상세보기", expanded=False):
            st.markdown(f"### #{idx+1} {offense}")
            st.write(f"- 결과: **{win}W-{lose}L** (총 {total}판)")
            st.write(f"- 승률: **{win_rate:.1f}%**")

            image_url = get_siege_image_url(
                match_id=None,
                log_id=None,
                offense_units=(row.get("o1", ""), row.get("o2", ""), row.get("o3", "")),
            )
            if image_url:
                st.image(image_url, use_container_width=True)
            else:
                st.caption("No image available.")
            st.divider()

            st.markdown("#### Lose 로그 (Siege Logs)")

            o1, o2, o3 = row.get("o1", ""), row.get("o2", ""), row.get("o3", "")
            logs = get_siege_loss_logs(def_key, o1, o2, o3, limit=200)
            
            if logs.empty:
                st.info("해당 공덱/방덱 조합의 Lose 로그가 없습니다.")
                continue
            
            logs = logs.copy()
            
            logs["방어덱"] = logs.apply(lambda r: _fmt_team(r, "deck2_1", "deck2_2", "deck2_3"), axis=1)
            logs["log_identifier"] = logs.apply(
                lambda r: r.get("log_id") or r.get("id") or r.get("ts"),
                axis=1,
            )
            
            logs = logs.rename(
                columns={
                    "wizard": "공격자",
                    "opp_wizard": "방어자",
                    "opp_guild": "방어길드",
                }
            )

            cols = [c for c in ["공격자", "방어덱", "방어길드", "방어자"] if c in logs.columns]

            st.dataframe(
                logs[cols],
                use_container_width=True,
                hide_index=True,
            )

            st.markdown("#### 상세보기")
            for log_idx, log in logs.iterrows():
                attacker = log.get("공격자", "")
                defender = log.get("방어자", "")
                defense_deck = log.get("방어덱", "")
                guild = log.get("방어길드", "")
                base = log.get("base", "")

                with st.expander(f"상세보기 #{log_idx + 1}: {attacker} vs {defender}", expanded=False):
                    if base:
                        st.write(f"- 기지: **{base}**")
                    st.write(f"- 공격자: **{attacker}**")
                    st.write(f"- 방어자: **{defender}**")
                    if guild:
                        st.write(f"- 방어길드: **{guild}**")
                    if defense_deck:
                        st.write(f"- 방어덱: **{defense_deck}**")



def render_siege_tab():
    st.subheader("Siege")

    # --- UI: select boxes ---
    col1, col2, col3 = st.columns(3)

    u1 = col1.selectbox("Unit #1 (Leader)", [""] + get_first_units(), key="siege_u1")
    u2_opts = [""] + (get_second_units(u1) if u1 else [])
    u2 = col2.selectbox("Unit #2", u2_opts, key="siege_u2")
    u3_opts = [""] + (get_third_units(u1, u2) if (u1 and u2) else [])
    u3 = col3.selectbox("Unit #3", u3_opts, key="siege_u3")

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
        limit = st.number_input("최대 추천 공덱 수", min_value=5, max_value=200, value=10, step=5, key="siege_limit")
    with right:
        search_clicked = st.button("Search", type="primary", key="siege_search_btn")

    if "siege_last_def_key" not in st.session_state:
        st.session_state["siege_last_def_key"] = None
    if "siege_last_df" not in st.session_state:
        st.session_state["siege_last_df"] = None
    if "siege_last_limit" not in st.session_state:
        st.session_state["siege_last_limit"] = None
    if "siege_trend" not in st.session_state:
        st.session_state["siege_trend"] = None

    if search_clicked:
        if not require_access_or_stop("siege_battle"):
            return
        if not (u1 and u2 and u3):
            st.warning("유닛 3개를 모두 선택하세요.")
            st.stop()
    
        def_key = make_def_key(u1, u2, u3)
    
        st.session_state["siege_last_def_key"] = def_key
        st.session_state["siege_last_limit"] = int(limit)
        st.session_state["siege_last_df"] = get_matchups(def_key, int(limit))
    
        logs_df = get_siege_logs_for_defense(def_key=def_key, limit=2000)
        st.session_state["siege_trend"] = build_cumulative_trend_df(logs_df)
    
        st.session_state["selected_idx"] = None
        st.session_state["selected_def_key"] = def_key



    current_def_key = make_def_key(u1, u2, u3) if (u1 and u2 and u3) else None
    last_def_key = st.session_state.get("siege_last_def_key")
    last_df = st.session_state.get("siege_last_df")
    last_limit = st.session_state.get("siege_last_limit")

    if current_def_key and last_def_key == current_def_key and isinstance(last_df, pd.DataFrame):
        render_matchups_master_detail(last_df, limit=int(last_limit or limit), def_key=current_def_key)
    
        st.divider()
        st.subheader("Trend Analysis (Cumulative)")
    
        trend = st.session_state.get("siege_trend")
        if isinstance(trend, pd.DataFrame) and not trend.empty:
            render_cumulative_trend_chart(trend)
        else:
            st.info("Search를 눌러 추세를 생성하세요.")

    
        return


    st.info("유닛 3개를 선택한 후 Search를 눌러주세요.")
