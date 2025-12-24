from __future__ import annotations

import pandas as pd
import streamlit as st

from services.supabase_client import get_supabase_client


def make_def_key(a: str, b: str, c: str) -> str:
    # a는 leader(고정), b/c는 순서 무관
    rest = sorted([x for x in [b, c] if x])
    return "|".join([a] + rest)


def _q(v: str) -> str:
    """
    postgrest or_ 문자열에서 안전하게 쓰기 위한 값 quoting.
    """
    v = (v or "").replace('"', '\\"')
    return f'"{v}"'


@st.cache_data(ttl=120)
def get_siege_logs_for_defense(def_key: str, limit: int = 5000) -> pd.DataFrame:
    parts = [p for p in (def_key or "").split("|") if p]
    if len(parts) < 3:
        return pd.DataFrame()
    d1, d2, d3 = parts[0], parts[1], parts[2]

    q = (
        get_supabase_client()
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


@st.cache_data(ttl=3600)
def get_first_units():
    res = get_supabase_client().table("defense_list").select("a").execute()
    return sorted({r["a"] for r in (res.data or []) if r.get("a")})


@st.cache_data(ttl=3600)
def get_second_units(a: str):
    res = get_supabase_client().table("defense_list").select("b,c").eq("a", a).execute()
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
    res = get_supabase_client().table("defense_list").select("b,c").eq("a", a).execute()
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
        get_supabase_client()
        .table("defense_matchups")
        .select("o1,o2,o3,win,lose,total,win_rate")
        .eq("def_key", def_key)
        .order("total", desc=True)
        .order("win_rate", desc=True)
        .limit(int(limit))
        .execute()
    )
    return pd.DataFrame(res.data or [])


@st.cache_data(ttl=120)
def get_siege_loss_logs(def_key: str, o1: str, o2: str, o3: str, limit: int = 200) -> pd.DataFrame:
    parts = [p for p in (def_key or "").split("|") if p]
    if len(parts) < 3:
        return pd.DataFrame()

    d1, d2, d3 = parts[0], parts[1], parts[2]

    if not (o1 and o2 and o3):
        return pd.DataFrame()

    q = (
        get_supabase_client()
        .table("siege_logs")
        .select(
            "ts, wizard, opp_wizard, opp_guild, result, base, "
            "deck1_1,deck1_2,deck1_3, deck2_1,deck2_2,deck2_3"
        )
        .eq("result", "Lose")
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

    res = q.or_(",".join(or_clauses)).order("ts", desc=True).limit(int(limit)).execute()
    return pd.DataFrame(res.data or [])
