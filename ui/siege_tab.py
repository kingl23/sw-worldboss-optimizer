import altair as alt
import streamlit as st


def render_cumulative_trend_chart(df: pd.DataFrame):
    n = len(df)

    # 표본 수 가드
    if n < 5:
        st.info("표본 수가 부족하여 추세 분석을 표시하지 않습니다.")
        return
    elif n < 10:
        st.warning("표본 수가 적어 해석에 주의가 필요합니다.")
    elif n < 20:
        st.caption("표본 수가 충분하지 않아 참고용으로만 해석하세요.")

    # area용 long-form 변환
    area_cols = [c for c in df.columns if c.startswith("share_")]
    area_df = df.melt(
        id_vars=["battle_idx"],
        value_vars=area_cols,
        var_name="offense",
        value_name="share",
    )
    area_df["offense"] = area_df["offense"].str.replace("share_", "", regex=False)

    # --- Stacked Area (공덱 비중) ---
    area = (
        alt.Chart(area_df)
        .mark_area(opacity=0.45)
        .encode(
            x=alt.X("battle_idx:Q", title="Battle Order"),
            y=alt.Y(
                "share:Q",
                stack="normalize",
                title="Offense Usage Share (%)",
                axis=alt.Axis(format="%"),
            ),
            color=alt.Color("offense:N", legend=alt.Legend(title="Offense")),
        )
    )

    # --- Line (누적 승률) ---
    line = (
        alt.Chart(df)
        .mark_line(color="black", strokeWidth=3)
        .encode(
            x="battle_idx:Q",
            y=alt.Y(
                "cum_win_rate:Q",
                title="Cumulative Win Rate (%)",
                scale=alt.Scale(domain=[0, 100]),
            ),
            tooltip=[
                alt.Tooltip("battle_idx:Q", title="Battle"),
                alt.Tooltip("cum_win_rate:Q", title="Win Rate", format=".1f"),
            ],
        )
    )

    chart = (
        alt.layer(area, line)
        .resolve_scale(y="independent")
        .properties(
            height=360,
            title="Cumulative Defense Win Rate & Offense Usage Trend",
        )
    )

    st.altair_chart(chart, use_container_width=True)
