import re
import pandas as pd
import streamlit as st


def _parse_top_values(cell: str) -> list[int]:
    if cell is None:
        return []
    s = str(cell).strip()
    if not s:
        return []
    nums = re.findall(r"-?\d+", s)
    return [int(n) for n in nums]


def _color_for_value(v: int) -> str:
    if v < 20:
        return "background-color:#ff0000;color:#ffffff;"
    if v <= 22:
        return "background-color:#ffff00;color:#000000;"
    if v <= 24:
        return "background-color:#66ff66;color:#000000;"
    return "background-color:#00cc44;color:#ffffff;"


def _style_df(df: pd.DataFrame) -> str:
    def style_cell(val):
        if val is None:
            return ""
        try:
            v = int(val)
        except Exception:
            return ""
        return _color_for_value(v)

    styler = (
        df.style
        .applymap(style_cell)
        .set_properties(**{
            "text-align": "center",
            "border": "1px solid #333",
            "font-size": "13px",
            "padding": "6px",
        })
        .set_table_styles([
            {"selector": "th", "props": [
                ("text-align", "center"),
                ("font-weight", "700"),
                ("border", "1px solid #000"),
                ("padding", "6px"),
            ]},
            {"selector": "table", "props": [
                ("border-collapse", "collapse"),
                ("width", "100%"),
            ]},
        ])
    )
    return styler.to_html()


def render_colored_topn_table(df_summary: pd.DataFrame, label_cols: list[str], value_cols: list[str], top_index: int = 0):
    out = pd.DataFrame()
    for col in value_cols:
        out[col] = df_summary[col].apply(lambda s: (_parse_top_values(s) + [0, 0, 0])[top_index])

    labels = df_summary[label_cols].copy()

    left, right = st.columns([1.0, 3.2], gap="small")

    with left:
        st.dataframe(labels, use_container_width=True, hide_index=True)

    with right:
        html = _style_df(out)
        st.markdown(html, unsafe_allow_html=True)
