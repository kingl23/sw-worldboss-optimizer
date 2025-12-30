from __future__ import annotations

import pandas as pd
import streamlit as st


def apply_dataframe_style() -> None:
    if st.session_state.get("_table_style_applied"):
        return

    st.markdown(
        """
        <style>
          div[data-testid="stDataFrame"] th {
            font-weight: 600;
          }
          div[data-testid="stDataFrame"] td {
            padding: 6px 10px;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.session_state["_table_style_applied"] = True


def build_deck_column(df: pd.DataFrame, columns: list[str]) -> pd.Series:
    return df[columns].fillna("").apply(
        lambda row: " / ".join([str(value) for value in row if str(value)]),
        axis=1,
    )


def to_numeric(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    return numeric.where(numeric.notna(), None)


def percent_to_float(series: pd.Series) -> pd.Series:
    cleaned = series.astype(str).str.replace("%", "", regex=False)
    numeric = pd.to_numeric(cleaned, errors="coerce")
    return numeric.where(numeric.notna(), None)
