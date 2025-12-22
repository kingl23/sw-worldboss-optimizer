import re
import pandas as pd
import streamlit as st


def _parse_first(cell: str) -> int:
    if cell is None:
        return 0
    s = str(cell).strip()
    nums = re.findall(r"-?\d+", s)
    return int(nums[0]) if nums else 0


def _color_for_value(v: int) -> str:
    if v < 20:
        return "background-color:#ff0000;color:#ffffff;"
    if v <= 22:
        return "background-color:#ffff00;color:#000000;"
    if v <= 24:
        return "background-color:#66ff66;color:#000000;"
    return "background-color:#00cc44;color:#ffffff;"


def render_google_style(df_summary: pd.DataFrame, label_cols: list[str], value_cols: list[str]):
    key_df = df_summary[value_cols].applymap(_parse_first)

    def style_cell(cell_text, key_val):
        if cell_text is None or str(cell_text).strip() == "":
            return ""
        return _color_for_value(int(key_val))

    def apply_styles(data: pd.DataFrame):
        styles = pd.DataFrame("", index=data.index, columns=data.columns)
        for c in value_cols:
            for i in data.index:
                styles.loc[i, c] = style_cell(data.loc[i, c], key_df.loc[i, c])
        return styles

    styled = (
        df_summary[label_cols + value_cols]
        .style
        .apply(apply_styles, axis=None)
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

    st.markdown(styled.to_html(), unsafe_allow_html=True)
