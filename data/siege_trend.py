import pandas as pd

TOP_N_OFFENSE = 5

def make_key_fixed_first(a: str, b: str, c: str) -> str:
    a = (a or "").strip()
    rest = sorted([x for x in [b, c] if x])
    if not a or len(rest) != 2:
        return ""
    return "|".join([a] + rest)


def build_cumulative_trend_df(siege_df: pd.DataFrame, def_key: str) -> pd.DataFrame:
    """
    siege_df: siege_logs DataFrame (already filtered to this def_key)
    """

    if siege_df.empty:
        return pd.DataFrame()

    df = siege_df.copy()

    # 1) match_id 기준 정렬 (선후 순서)
    df = df.sort_values("match_id", ascending=True).reset_index(drop=True)

    # 2) 공덱 키 생성
    df["off_key"] = df.apply(
        lambda r: make_key_fixed_first(
            r.get("deck1_1"), r.get("deck1_2"), r.get("deck1_3")
        ),
        axis=1,
    )
    df = df[df["off_key"] != ""]
    if df.empty:
        return pd.DataFrame()

    # 3) 승패 → 방어 기준 win
    # Win = 방어 성공
    df["def_win"] = (df["result"] == "Win").astype(int)

    # 4) 누적 지표
    df["battle_idx"] = range(1, len(df) + 1)
    df["cum_wins"] = df["def_win"].cumsum()
    df["cum_total"] = df["battle_idx"]
    df["cum_win_rate"] = df["cum_wins"] / df["cum_total"] * 100.0

    # 5) Top N 공덱 선정 (전체 기준)
    top_off = (
        df["off_key"]
        .value_counts()
        .head(TOP_N_OFFENSE)
        .index
        .tolist()
    )

    df["off_group"] = df["off_key"].where(
        df["off_key"].isin(top_off),
        other="Others"
    )

    # 6) 누적 공덱 사용 비율
    for k in top_off + ["Others"]:
        df[f"share_{k}"] = (
            (df["off_group"] == k).cumsum() / df["cum_total"] * 100.0
        )

    return df
