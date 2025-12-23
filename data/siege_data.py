# data/siege_data.py
import pandas as pd
import streamlit as st
from supabase import create_client


def _or_val(v: str) -> str:
    s = (v or "").strip()
    s = s.replace('"', r'\"')
    return f'"{s}"'


def sb():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_ANON_KEY"]
    )


@st.cache_data(ttl=300)
def build_worst_offense_list(cutoff: int = 4) -> pd.DataFrame:
    res = (
        sb()
        .table("siege_logs")
        .select("result, deck2_1, deck2_2, deck2_3")
        .in_("result", ["Win", "Lose"])
        .execute()
    )

    df = pd.DataFrame(res.data or [])
    if df.empty:
        return df

    def make_def_key(r):
        a = r["deck2_1"]
        rest = sorted([r["deck2_2"], r["deck2_3"]])
        return "|".join([a] + rest)

    df["def_key"] = df.apply(make_def_key, axis=1)

    agg = (
        df.groupby("def_key")
        .agg(
            win=("result", lambda x: (x == "Lose").sum()),
            lose=("result", lambda x: (x == "Win").sum()),
        )
        .reset_index()
    )

    agg["total"] = agg["win"] + agg["lose"]
    agg = agg[agg["total"] >= cutoff]
    if agg.empty:
        return agg

    agg["win_rate"] = agg["win"] / agg["total"]
    agg[["d1", "d2", "d3"]] = agg["def_key"].str.split(r"\|", expand=True)
    # 또는: .str.split("|", expand=True, regex=False)

    return agg



def make_key_fixed(a: str, b: str, c: str) -> str:
    a = (a or "").strip()
    b = (b or "").strip()
    c = (c or "").strip()
    if not a:
        return ""
    rest = sorted([x for x in [b, c] if x])
    if len(rest) != 2:
        return ""
    return "|".join([a] + rest)


@st.cache_data(ttl=300)
def get_offense_stats_by_defense(def1: str, def2: str, def3: str, limit: int = 50) -> pd.DataFrame:
    def1 = (def1 or "").strip()
    def2 = (def2 or "").strip()
    def3 = (def3 or "").strip()
    if not (def1 and def2 and def3):
        return pd.DataFrame()

    # 방덱: 첫 슬롯 고정 + 2/3 스왑만 허용
    def_perms = [(def1, def2, def3), (def1, def3, def2)]

    q = (
        sb()
        .table("siege_logs")
        .select("result, deck1_1,deck1_2,deck1_3, deck2_1,deck2_2,deck2_3")
        .in_("result", ["Win", "Lose"])  # 공격자 기준
    )

    # 방덱 매칭 (deck2_1 고정, deck2_2/3만 swap)
    or_clauses = [
        f"and(deck2_1.eq.{_or_val(a)},deck2_2.eq.{_or_val(b)},deck2_3.eq.{_or_val(c)})"
        for a, b, c in def_perms
    ]
    q = q.or_(",".join(or_clauses))

    res = q.execute()
    df = pd.DataFrame(res.data or [])
    if df.empty:
        return df

    # 공덱 키 생성: 첫 슬롯 고정 + 2/3 정렬(고정)
    def off_key_row(r) -> str:
        return make_key_fixed(r.get("deck1_1", ""), r.get("deck1_2", ""), r.get("deck1_3", ""))

    df["off_key"] = df.apply(off_key_row, axis=1)
    df = df[df["off_key"] != ""]
    if df.empty:
        return pd.DataFrame()

    # 공격자 기준 집계: Win=공격자 승, Lose=공격자 패
    agg = (
        df.groupby("off_key")
        .agg(
            wins=("result", lambda x: (x == "Win").sum()),
            losses=("result", lambda x: (x == "Lose").sum()),
        )
        .reset_index()
    )
    agg["total"] = agg["wins"] + agg["losses"]
    agg["win_rate"] = agg.apply(lambda r: (r["wins"] / r["total"] * 100) if r["total"] else 0.0, axis=1)

    # 공덱 유닛 분해
    agg[["Unit #1", "Unit #2", "Unit #3"]] = agg["off_key"].str.split("|", expand=True)

    # GAS와 동일한 정렬: total desc → win_rate desc
    agg = agg.sort_values(["total", "win_rate"], ascending=[False, False]).head(int(limit)).reset_index(drop=True)
    agg["Win Rate"] = agg["win_rate"].map(lambda x: f"{x:.1f}%")
    agg["Summary"] = agg["wins"].astype(int).astype(str) + "W-" + agg["losses"].astype(int).astype(str) + "L"

    return agg[["Unit #1", "Unit #2", "Unit #3", "wins", "losses", "Win Rate", "Summary", "total"]]



def debug_lookup_defense(def_key=None, d1=None, d2=None, d3=None):
    """
    returns dict:
      - defense_list rows (matched)
      - defense_matchups rows (matched, limited)
    """
    client = sb()


    out = {}

    # defense_list 조회
    q1 = sb.table("defense_list").select("def_key,a,b,c,updated_at")
    if def_key:
        q1 = q1.eq("def_key", def_key)
    elif d1:
        q1 = q1.eq("a", d1).eq("b", d2).eq("c", d3)
    r1 = q1.execute()
    out["defense_list"] = r1.data

    # defense_matchups 조회
    q2 = sb.table("defense_matchups").select("def_key,off_key,o1,o2,o3,win,lose,total,win_rate,updated_at")
    if def_key:
        q2 = q2.eq("def_key", def_key)
    elif d1:
        # def_key를 모르므로 defense_list 결과가 있으면 그 키로 조회
        if out["defense_list"]:
            q2 = q2.eq("def_key", out["defense_list"][0]["def_key"])
        else:
            out["defense_matchups"] = []
            return out

    r2 = q2.order("total", desc=True).limit(50).execute()
    out["defense_matchups"] = r2.data

    return out
