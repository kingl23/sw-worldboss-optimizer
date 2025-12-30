# data/siege_trend.py
import math
import pandas as pd

MAX_POINTS = 500
TOP_N_OFFENSE = 7


def _norm(v) -> str:
    return str(v).strip() if v is not None else ""


def make_off_key(a, b, c) -> str:
    A = _norm(a)
    B = _norm(b)
    C = _norm(c)
    if not A:
        return ""
    rest = sorted([x for x in [B, C] if x])
    if len(rest) != 2:
        return ""
    return "|".join([A] + rest)


def build_cumulative_trend_df(siege_df: pd.DataFrame) -> pd.DataFrame:
    if siege_df is None or siege_df.empty:
        return pd.DataFrame()

    df = siege_df.copy()

    df["match_sort"] = pd.to_numeric(df.get("match_id"), errors="coerce")
    if "ts" not in df.columns:
        df["ts"] = None
    df = df.sort_values(["match_sort", "ts"], ascending=[True, True]).reset_index(drop=True)

    df["is_win"] = (df["result"].astype(str).str.lower() == "win").astype(int)

    df["off_key"] = df.apply(
        lambda r: make_off_key(r.get("deck1_1"), r.get("deck1_2"), r.get("deck1_3")),
        axis=1,
    )
    df = df[df["off_key"] != ""].reset_index(drop=True)
    if df.empty:
        return pd.DataFrame()

    df["cum_games"] = range(1, len(df) + 1)
    df["cum_wins"] = df["is_win"].cumsum()
    df["cum_win_rate"] = (df["cum_wins"] / df["cum_games"]) * 100.0

    N = len(df)
    bucket_size = max(1, math.ceil(N / MAX_POINTS))
    df["bucket_idx"] = (df.index // bucket_size).astype(int)

    last = df.groupby("bucket_idx", as_index=False).tail(1).reset_index(drop=True)

    top_off = (
        df["off_key"]
        .value_counts()
        .head(TOP_N_OFFENSE)
        .index
        .tolist()
    )

    df["offense"] = df["off_key"].where(df["off_key"].isin(top_off), other="Others")

    bucket_counts = (
        df.groupby(["bucket_idx", "offense"])
          .size()
          .unstack(fill_value=0)   # bucket_idx x offense grid (없으면 0)
          .sort_index()
    )

    cum_counts = bucket_counts.cumsum()

    share_wide = cum_counts.copy()
    share_wide.columns = [f"share_{c}" for c in share_wide.columns]

    line = last[["bucket_idx", "cum_win_rate"]].copy()

    out = (
        pd.merge(
            share_wide.reset_index(),
            line,
            on="bucket_idx",
            how="left",
        )
        .sort_values("bucket_idx")
        .reset_index(drop=True)
    )

    out["bucket_size"] = bucket_size
    out["total_games"] = N

    return out
