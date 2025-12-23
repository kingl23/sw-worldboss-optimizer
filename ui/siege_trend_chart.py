# ui/siege_trend_chart.py
import streamlit as st
import altair as alt
import pandas as pd


def render_cumulative_trend_chart(trend: dict):
    if not isinstance(trend, dict):
        st.error("Trend payload is not a dict.")
        return

    line_df = trend.get("line")
    area_df = trend.get("area")
    bucket_size = trend.get("bucket_size")
    total_games = trend.get("total_games")

    if not isinstance(line_df, pd.DataFrame) or line_df.empty:
        st.info("Trend line 데이터가 없습니다.")
        return

    # area가 비어도 line은 그릴 수 있게 처리
    if not isinstance(area_df, pd.DataFrame):
        area_df = pd.DataFrame(columns=["bucket", "offense", "share"])

    st.caption(f"total_games={total_games}, bucket_size={bucket_size}")

    # ---- Area (Top 5 + Others 포함해도 되고, 제외해도 됨)
    area = (
        alt.Chart(area_df)
        .mark_area(opacity=0.35)
        .encode(
            x=alt.X("bucket:Q", title="Matches (bucketed)"),
            y=alt.Y("share:Q", title="Offense Share (%)"),
            color=alt.Color("offense:N", legend=alt.Legend(title="Offense")),
            tooltip=["bucket:Q", "offense:N", alt.Tooltip("share:Q", format=".1f")],
        )
        .properties(height=260)
    )

    # (선택) Others를 빼고 싶으면 아래 한 줄을 켜세요.
    # area = area.transform_filter(alt.datum.offense != "Others")

    # ---- Line
    line = (
        alt.Chart(line_df)
        .mark_line(interpolate="monotone", strokeWidth=2)
        .encode(
            x=alt.X("bucket:Q", title="Matches (bucketed)"),
            y=alt.Y("cum_win_rate:Q", title="Cumulative Win Rate (%)"),
            tooltip=[
                "bucket:Q",
                alt.Tooltip("cum_win_rate:Q", format=".1f"),
            ],
        )
        .properties(height=260)
    )

    chart = alt.layer(area, line).resolve_scale(y="independent")
    st.altair_chart(chart, width="stretch")
