# ui/artifact_render.py
from __future__ import annotations

import pandas as pd
import streamlit as st


def _cell_style(v: int) -> str:
    # 구글시트 스샷 기준 색 범위
    try:
        x = int(v)
    except Exception:
        return ""

    if x < 20:
        return "background-color:#ff0000;color:#ffffff;"
    if x <= 22:
        return "background-color:#ffff00;color:#000000;"
    if x <= 24:
        return "background-color:#66ff66;color:#000000;"
    return "background-color:#00cc44;color:#ffffff;"


def render_matrix(df: pd.DataFrame, label_cols: list[str], title: str | None = None):
    """
    df: label_cols + MultiIndex value cols((Group, k)) 형태
    """
    if title:
        st.markdown(f"### {title}")

    # label + values 분리
    labels = df[label_cols].copy()
    values = df.drop(columns=label_cols)

    # Streamlit은 MultiIndex 컬럼을 그대로 dataframe으로 보여주면 헤더가 깔끔하지 않을 수 있어서
    # 표시용으로 "Fire-1" 같은 단일 컬럼명으로 변환(구글시트처럼 그룹 느낌 원하면 CSS로 확장 가능)
    display_values = values.copy()
    display_values.columns = [f"{a}{b}" for (a, b) in display_values.columns]  # Fire1, Fire2, Fire3...

    # 스타일 적용(숫자 셀별)
    styled = (
        display_values.style
        .applymap(_cell_style)
        .set_properties(**{
            "text-align": "center",
            "border": "1px solid #333",
            "font-size": "13px",
            "padding": "6px",
            "white-space": "nowrap",
        })
        .set_table_styles([
            {"selector": "th", "props": [
                ("text-align", "center"),
                ("font-weight", "700"),
                ("border", "1px solid #000"),
                ("padding", "6px"),
                ("background-color", "#f3f3f3"),
            ]},
            {"selector": "table", "props": [
                ("border-collapse", "collapse"),
                ("width", "100%"),
            ]},
        ])
    )

    # 레이아웃: 좌측 라벨 + 우측 매트릭스 (구글시트 느낌)
    left, right = st.columns([1.0, 3.4], gap="small")
    with left:
        st.dataframe(labels, use_container_width=True, hide_index=True)
    with right:
        st.markdown(styled.to_html(), unsafe_allow_html=True)
