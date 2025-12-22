# data/siege_data.py
import pandas as pd
import streamlit as st
from supabase import create_client


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
    agg[["d1", "d2", "d3"]] = agg["def_key"].str.split("|", expand=True)

    return agg
