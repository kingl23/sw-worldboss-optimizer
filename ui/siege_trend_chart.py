import pandas as pd
import streamlit as st
import altair as alt


def show_cumulative_trend_chart(df: pd.DataFrame):
    """Render the cumulative siege trend chart when data is available."""
    if df is None or df.empty:
        st.info("Trend 데이터가 없습니다.")
        return

    n = len(df)

    if n < 5:
        st.info("표본 수가 부족하여 추세 분석을 표시하지 않습니다.")
        return
    elif n < 10:
        st.warning("표본 수가 적어 해석에 주의가 필요합니다.")
    elif n < 20:
        st.caption("표본 수가 충분하지 않아 참고용으로만 해석하세요.")

    if "total_games" in df.columns and "bucket_size" in df.columns:
        try:
            tg = int(df["total_games"].iloc[-1])
            bs = int(df["bucket_size"].iloc[-1])
            st.caption(f"total_games={tg}, bucket_size={bs}")
        except Exception:
            pass

    area_cols = [c for c in df.columns if c.startswith("share_")]
    if not area_cols:
        st.info("공덱 비중 데이터(share_*)가 없습니다.")
        return

    area_df = df.melt(
        id_vars=["bucket_idx"],
        value_vars=area_cols,
        var_name="offense",
        value_name="cum_cnt",
    )
    area_df["offense"] = area_df["offense"].str.replace("share_", "", regex=False)

    area = (
        alt.Chart(area_df)
        .mark_area(opacity=0.45)
        .encode(
            x=alt.X("bucket_idx:Q", title="Battle Order (bucketed)"),
            y=alt.Y(
                "cum_cnt:Q",
                stack="normalize",
                title="Offense Usage Share (%)",
                axis=alt.Axis(format="%"),
            ),
            color=alt.Color("offense:N", legend=alt.Legend(title="Offense")),
            tooltip=[
                alt.Tooltip("bucket_idx:Q", title="Bucket"),
                alt.Tooltip("offense:N", title="Offense"),
            ],
        )
        .properties(height=360)
    )

    line = (
        alt.Chart(df)
        .mark_line(color="black", strokeWidth=3)
        .encode(
            x=alt.X("bucket_idx:Q"),
            y=alt.Y(
                "cum_win_rate:Q",
                title="Cumulative Win Rate (%)",
                scale=alt.Scale(domain=[0, 100]),
            ),
            tooltip=[
                alt.Tooltip("bucket_idx:Q", title="Bucket"),
                alt.Tooltip("cum_win_rate:Q", title="Win Rate", format=".1f"),
            ],
        )
        .properties(height=360)
    )

    chart = (
        alt.layer(area, line)
        .resolve_scale(y="independent")
        .properties(title="Cumulative Defense Win Rate & Offense Usage Trend")
    )

    st.altair_chart(chart, width="stretch")


render_cumulative_trend_chart = show_cumulative_trend_chart
