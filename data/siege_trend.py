# data/siege_trend.py
import math
import pandas as pd

MAX_POINTS = 500          # x축 포인트 최대(가볍게)
TOP_N_OFFENSE = 10         # area에서 보여줄 공덱 개수 (나머지 Others)


def _norm(v) -> str:
    return str(v).strip() if v is not None else ""


def make_off_key(a, b, c) -> str:
    """
    첫 자리 고정, 2/3자리 순서 무관: A|sort(B,C)
    """
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
    """
    반환 DF 컬럼:
      - bucket_idx (x축)
      - cum_win_rate (line)
      - share_<offense> (area, stack normalize로 100% 분할)
    """
    if siege_df is None or siege_df.empty:
        return pd.DataFrame()

    df = siege_df.copy()

    # ---- 정렬 (match_id 우선, fallback ts)
    df["match_sort"] = pd.to_numeric(df.get("match_id"), errors="coerce")
    if "ts" not in df.columns:
        df["ts"] = None
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

    # ---- 누적 승률(원본 단위)
    df["cum_games"] = range(1, len(df) + 1)
    df["cum_wins"] = df["is_win"].cumsum()
    df["cum_win_rate"] = (df["cum_wins"] / df["cum_games"]) * 100.0

    # ---- 가볍게: bucket으로 downsample (MAX_POINTS)
    N = len(df)
    bucket_size = max(1, math.ceil(N / MAX_POINTS))
    df["bucket_idx"] = (df.index // bucket_size).astype(int)

    # ---- bucket 대표(마지막 전투)만 남겨서 line을 가볍게
    last = df.groupby("bucket_idx", as_index=False).tail(1).reset_index(drop=True)

    # ---- Top N offense 선정 (전체 기준: 많이 등장한 공덱)
    # (off_key 등장 횟수 기준이 가장 직관적)
    top_off = (
        df["off_key"]
        .value_counts()
        .head(TOP_N_OFFENSE)
        .index
        .tolist()
    )

    # ---- bucket별 offense 사용 횟수 (bucket 내부에서 등장한 횟수)
    # top_off 외는 Others로 묶음
    df["offense"] = df["off_key"].where(df["off_key"].isin(top_off), other="Others")

    bucket_counts = (
        df.groupby(["bucket_idx", "offense"])
          .size()
          .unstack(fill_value=0)   # bucket_idx x offense grid (없으면 0)
          .sort_index()
    )

    # ---- 누적 사용량 (bucket 단위 누적)
    cum_counts = bucket_counts.cumsum()

    # ---- wide-form share_ 컬럼 생성 (normalize stack은 차트에서 수행)
    share_wide = cum_counts.copy()
    share_wide.columns = [f"share_{c}" for c in share_wide.columns]

    # ---- line DF (bucket 대표의 누적 승률)
    line = last[["bucket_idx", "cum_win_rate"]].copy()

    # ---- merge: bucket_idx 기준으로 한 장의 DF로 반환 (원래 잘 되던 형태)
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

    # 메타 컬럼(디버깅용)도 필요하면 추가 가능하지만, 차트에는 안 씀
    out["bucket_size"] = bucket_size
    out["total_games"] = N

    return out
