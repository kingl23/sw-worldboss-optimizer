# ui/siege_trend_chart.py
import pandas as pd
import streamlit as st
import altair as alt


def render_cumulative_trend_chart(trend: dict):
    if not trend or "line" not in trend or "area" not in trend:
        st.info("Trend 데이터가 없습니다.")
        return

    line_df = trend["line"]
    area_df = trend["area"]

    base = alt.Chart().encode(
        x=alt.X("bucket:Q", title="Matches (bucketed)")
    )

    area = (
        base
        .mark_area(opacity=0.35)
        .encode(
            y=alt.Y("share:Q", title="Offense Share (%)"),
            color=alt.Color("offense:N", legend=alt.Legend(title="Offense")),
        )
        .transform_filter(alt.datum.offense != "Others")
        .properties(height=260)
    )

    line = (
        base
        .mark_line(interpolate="monotone", strokeWidth=2)
        .encode(
            y=alt.Y("cum_win_rate:Q", title="Cumulative Win Rate (%)"),
            color=alt.value("#000000"),
            tooltip=["cum_win_rate:Q"],
        )
        .properties(height=260)
    )

    chart = alt.layer(area, line).resolve_scale(y="independent")
    st.altair_chart(chart, width="stretch")
