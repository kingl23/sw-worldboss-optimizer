# data/siege_trend.py
import pandas as pd
import math

MAX_POINTS = 500
TOP_N_OFFENSE = 5


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

    # ---- 정렬 (match_id 우선, fallback ts)
    df["match_sort"] = pd.to_numeric(df["match_id"], errors="coerce")
    df = df.sort_values(["match_sort", "ts"], ascending=[True, True]).reset_index(drop=True)

    # ---- 결과 정규화
    df["is_win"] = (df["result"].astype(str).str.lower() == "win").astype(int)

    # ---- offense key
    df["off_key"] = df.apply(
        lambda r: make_off_key(r.get("deck1_1"), r.get("deck1_2"), r.get("deck1_3")),
        axis=1,
    )
    df = df[df["off_key"] != ""].reset_index(drop=True)
    if df.empty:
        return pd.DataFrame()

    # ---- 누적 계산 (원본 단위)
    df["cum_games"] = range(1, len(df) + 1)
    df["cum_wins"] = df["is_win"].cumsum()
    df["cum_win_rate"] = df["cum_wins"] / df["cum_games"] * 100.0

    # ---- offense 누적 count
    off_cum = (
        df.groupby(["off_key"])
        .cumcount()
        .add(1)
        .rename("off_cum_count")
    )
    df = df.join(off_cum)

    # ---- bucket 결정 (핵심)
    N = len(df)
    bucket_size = max(1, math.ceil(N / MAX_POINTS))
    df["bucket"] = df.index // bucket_size

    # ---- bucket 대표값 = 마지막 값
    last_rows = df.groupby("bucket").tail(1).reset_index(drop=True)

    # ---- Top N offense 선정 (전체 기준)
    top_off = (
        df.groupby("off_key")["off_cum_count"]
        .max()
        .sort_values(ascending=False)
        .head(TOP_N_OFFENSE)
        .index
        .tolist()
    )

    last_rows["offense"] = last_rows["off_key"].where(
        last_rows["off_key"].isin(top_off),
        other="Others",
    )

    # ---- area용 share 계산 (근본 해결: reset_index 충돌/불안정 제거)
    tmp = (
        last_rows
        .groupby(["bucket", "offense"], as_index=False)["off_cum_count"]
        .sum()
    )
    
    tmp["share"] = tmp["off_cum_count"] / tmp.groupby("bucket")["off_cum_count"].transform("sum") * 100.0
    area = tmp[["bucket", "offense", "share"]]


    # ---- line용 dataframe
    line = last_rows[["bucket", "cum_win_rate"]].copy()
    line["series"] = "Win Rate"

    # ---- merge (chart에서 레이어 분리 사용)
    return {
        "line": line,
        "area": area,
        "bucket_size": bucket_size,
        "total_games": N,
    }
