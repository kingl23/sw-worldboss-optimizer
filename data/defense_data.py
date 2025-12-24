from __future__ import annotations

from typing import Dict, List, Optional, Tuple
import streamlit as st
import pandas as pd
from supabase import create_client


def sb():
    """Create a Supabase client from Streamlit secrets."""
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_ANON_KEY"],
    )


GUILD_GROUPS = {
    "in4": {
        "오후", "Barcode", "으르렁", "시차",
    },
    "in12": {
        "동아리", "사람", "파죽지세", "명성", "default value",
        "겨울왕국&", "밤공기좋은날에", "자율주행", "NewJeans",
    },
    "in32": {
        "고추전쟁", "Moe's Bar", "Abracadabra", "요거트", "혁명가들",
        "콩코드", "밤공기좋은날엔", "격차", "Odd Eyes", "커피한잔의여유",
        "커버", "Eve.Re", "니플헤임", "TMZX", "수달",
        "무덤", "Dongs", "도탁스", "구글기프트코드", " 《G&C》",
    },
}


def make_def_key(a: str, b: str, c: str) -> str:
    """Build a defense key with a fixed leader and sorted followers."""
    a = (a or "").strip()
    b = (b or "").strip()
    c = (c or "").strip()

    if not a:
        return ""

    rest = sorted([x for x in [b, c] if x])
    if len(rest) != 2:
        return ""

    return "|".join([a] + rest)


def _is_win(result: str) -> Optional[bool]:
    r = (result or "").strip()
    if r == "Win":
        return True
    if r == "Lose":
        return False
    return None


def _pct(win: int, total: int) -> str:
    if total <= 0:
        return "0.0%"
    return f"{(win / total) * 100.0:.1f}%"


@st.cache_data(ttl=300)
def list_opp_guilds() -> List[str]:
    """List opponent guild names from defense_logs."""
    client = sb()
    page_size = 1000
    start = 0

    s = set()

    while True:
        res = (
            client
            .table("defense_logs")
            .select("opp_guild")
            .range(start, start + page_size - 1)
            .execute()
        )
        batch = res.data or []
        if not batch:
            break

        for r in batch:
            g = (r.get("opp_guild") or "").strip()
            if g:
                s.add(g)

        if len(batch) < page_size:
            break
        start += page_size

    return sorted(s)


@st.cache_data(ttl=300)
def list_defense_deck_stats(limit: int = 50) -> pd.DataFrame:
    """Return aggregated defense deck stats with guild-group splits."""
    if limit is None or int(limit) < 0:
        limit = 50
    limit = int(limit)

    client = sb()
    page_size = 1000
    start = 0

    base_map: Dict[str, List] = {}
    g32: Dict[str, Tuple[int, int]] = {}
    g12: Dict[str, Tuple[int, int]] = {}
    g4: Dict[str, Tuple[int, int]] = {}

    def _inc_pair(m: Dict[str, Tuple[int, int]], k: str, is_win: bool):
        w, l = m.get(k, (0, 0))
        if is_win:
            w += 1
        else:
            l += 1
        m[k] = (w, l)

    while True:
        res = (
            client
            .table("defense_logs")
            .select("result, opp_guild, deck1_1, deck1_2, deck1_3")
            .in_("result", ["Win", "Lose"])
            .range(start, start + page_size - 1)
            .execute()
        )
        batch = res.data or []
        if not batch:
            break

        for r in batch:
            is_win = _is_win(r.get("result"))
            if is_win is None:
                continue

            d1 = r.get("deck1_1") or ""
            d2 = r.get("deck1_2") or ""
            d3 = r.get("deck1_3") or ""
            def_key = make_def_key(d1, d2, d3)
            if not def_key:
                continue

            if def_key not in base_map:
                base_map[def_key] = [d1, d2, d3, 0, 0]
            if is_win:
                base_map[def_key][3] += 1
            else:
                base_map[def_key][4] += 1

            og = (r.get("opp_guild") or "").strip()
            if og:
                if og in GUILD_GROUPS["in32"]:
                    _inc_pair(g32, def_key, is_win)
                if og in GUILD_GROUPS["in12"]:
                    _inc_pair(g12, def_key, is_win)
                if og in GUILD_GROUPS["in4"]:
                    _inc_pair(g4, def_key, is_win)

        if len(batch) < page_size:
            break
        start += page_size

    if not base_map:
        return pd.DataFrame([{"error": "defense_logs에 집계할 데이터가 없습니다."}])

    rows = []
    for k, v in base_map.items():
        d1, d2, d3, w, l = v
        total = w + l
        rows.append(
            {
                "def_key": k,
                "d1": d1,
                "d2": d2,
                "d3": d3,
                "win": int(w),
                "lose": int(l),
                "total": int(total),
                "win_rate_num": (w / total) if total else 0.0,
                "win_rate": _pct(w, total),
            }
        )

    df = pd.DataFrame(rows)
    df = df.sort_values(
        by=["win_rate_num", "total", "def_key"],
        ascending=[False, False, True],
    )

    if limit != 0:
        df = df.head(limit)

    def _apply_group(df_in: pd.DataFrame, gm: Dict[str, Tuple[int, int]], prefix: str) -> pd.DataFrame:
        win_col = f"{prefix}_win"
        lose_col = f"{prefix}_lose"
        wr_col = f"{prefix}_win_rate"

        w_list, l_list, wr_list = [], [], []
        for k in df_in["def_key"].tolist():
            w, l = gm.get(k, (0, 0))
            t = w + l
            w_list.append(int(w) if t > 0 else "")
            l_list.append(int(l) if t > 0 else "")
            wr_list.append(_pct(w, t) if t > 0 else "")
        df_in[win_col] = w_list
        df_in[lose_col] = l_list
        df_in[wr_col] = wr_list
        return df_in

    df = _apply_group(df, g32, "in32")
    df = _apply_group(df, g12, "in12")
    df = _apply_group(df, g4, "in4")

    out = df[
        [
            "d1", "d2", "d3",
            "win", "lose", "win_rate",
            "in32_win", "in32_lose", "in32_win_rate",
            "in12_win", "in12_lose", "in12_win_rate",
            "in4_win", "in4_lose", "in4_win_rate",
        ]
    ].reset_index(drop=True)

    return out


@st.cache_data(ttl=300)
def defense_decks_vs_guild(opp_guild: str, limit: int = 50) -> pd.DataFrame:
    """Return defense deck stats filtered by opponent guild."""
    opp_guild = (opp_guild or "").strip()
    if not opp_guild:
        return pd.DataFrame([{"error": "상대 길드명을 선택/입력하세요."}])

    if limit is None or int(limit) < 1:
        limit = 50
    limit = int(limit)

    client = sb()
    page_size = 1000
    start = 0

    base_map: Dict[str, List] = {}

    while True:
        res = (
            client
            .table("defense_logs")
            .select("result, opp_guild, deck1_1, deck1_2, deck1_3")
            .eq("opp_guild", opp_guild)
            .in_("result", ["Win", "Lose"])
            .range(start, start + page_size - 1)
            .execute()
        )
        batch = res.data or []
        if not batch:
            break

        for r in batch:
            is_win = _is_win(r.get("result"))
            if is_win is None:
                continue

            d1 = r.get("deck1_1") or ""
            d2 = r.get("deck1_2") or ""
            d3 = r.get("deck1_3") or ""
            def_key = make_def_key(d1, d2, d3)
            if not def_key:
                continue

            if def_key not in base_map:
                base_map[def_key] = [d1, d2, d3, 0, 0]
            if is_win:
                base_map[def_key][3] += 1
            else:
                base_map[def_key][4] += 1

        if len(batch) < page_size:
            break
        start += page_size

    if not base_map:
        return pd.DataFrame([{"error": f"{opp_guild} 상대 방덱 기록이 없습니다."}])

    rows = []
    for k, v in base_map.items():
        d1, d2, d3, w, l = v
        total = w + l
        rows.append(
            {
                "def_key": k,
                "d1": d1,
                "d2": d2,
                "d3": d3,
                "win": int(w),
                "lose": int(l),
                "total": int(total),
                "win_rate_num": (w / total) if total else 0.0,
                "win_rate": _pct(w, total),
            }
        )

    df = pd.DataFrame(rows)
    df = df.sort_values(
        by=["win_rate_num", "total", "def_key"],
        ascending=[False, False, True],
    ).head(limit)

    out = df[["d1", "d2", "d3", "win", "lose", "win_rate"]].reset_index(drop=True)
    return out


get_opp_guild_options = list_opp_guilds
get_defense_deck_stats = list_defense_deck_stats
get_defense_decks_vs_guild = defense_decks_vs_guild
