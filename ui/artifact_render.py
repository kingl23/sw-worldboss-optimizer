# ui/artifact_render.py
from __future__ import annotations

import html
import pandas as pd
import streamlit as st


def _cell_style(v: int) -> str:
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


def render_matrix(
    df: pd.DataFrame,
    label_cols: list[str],
    title: str | None = None,
):
    """
    df:
      - label_cols (예: ["Attribute","Main"])
      - value columns: MultiIndex (Group, k) e.g. ("Fire",1), ("Fire",2)...

    출력:
      - label_cols 포함한 단일 HTML table
      - 2줄 헤더 (Group colSpan 병합)
      - 숫자 셀 색칠
    """
    if title:
        st.markdown(f"### {title}")

    labels = df[label_cols].copy()
    values = df.drop(columns=label_cols)

    # value columns must be a 2-level MultiIndex like (Group, k)
    # NOTE: when df has both string columns (labels) + tuple columns, pandas may keep columns as plain Index(object).
    # In that case, coerce tuple columns into MultiIndex here.
    if not isinstance(values.columns, pd.MultiIndex):
        if all(isinstance(c, tuple) and len(c) == 2 for c in values.columns):
            values.columns = pd.MultiIndex.from_tuples(values.columns)
        else:
            raise ValueError(
                "Value columns must be 2-tuples (Group, k) or a 2-level MultiIndex."
            )
    
    if values.columns.nlevels != 2:
        raise ValueError("Value columns must be a 2-level MultiIndex like (Group, k).")


    groups = []
    # preserve order
    for g in values.columns.get_level_values(0):
        if g not in groups:
            groups.append(g)

    # Build HTML
    css = """
    <style>
      .mx-wrap { overflow-x: auto; }
      table.mx {
        border-collapse: collapse;
        width: max-content;
        min-width: 100%;
        font-size: 13px;
      }
      table.mx th, table.mx td {
        border: 1px solid #000;
        padding: 6px 8px;
        text-align: center;
        white-space: nowrap;
      }
      table.mx thead th {
        background: #f3f3f3;
        font-weight: 700;
      }
      table.mx th.sticky {
        position: sticky;
        left: 0;
        z-index: 3;
        background: #ffffff;
      }
      table.mx th.sticky2 {
        position: sticky;
        left: 120px; /* 두 번째 라벨 열 고정 위치(필요시 조정) */
        z-index: 3;
        background: #ffffff;
      }
      table.mx td.sticky {
        position: sticky;
        left: 0;
        z-index: 2;
        background: #ffffff;
      }
      table.mx td.sticky2 {
        position: sticky;
        left: 120px; /* 두 번째 라벨 열 고정 위치(필요시 조정) */
        z-index: 2;
        background: #ffffff;
      }
    </style>
    """

    # Header row 1: label headers + group headers(colspan=3)
    # Header row 2: label placeholders + 1/2/3 under each group
    h1 = "<tr>"
    # label columns header cells (rowspan=2)
    # sticky 처리: 첫 라벨 열, 두 번째 라벨 열
    for i, col in enumerate(label_cols):
        cls = "sticky" if i == 0 else ("sticky2" if i == 1 else "")
        h1 += f'<th class="{cls}" rowspan="2">{html.escape(col)}</th>'
    for g in groups:
        # count how many subcols (usually 3)
        subcols = [c for c in values.columns if c[0] == g]
        h1 += f'<th colspan="{len(subcols)}">{html.escape(str(g))}</th>'
    h1 += "</tr>"

    h2 = "<tr>"
    for g in groups:
        subcols = [c for c in values.columns if c[0] == g]
        for (_, k) in subcols:
            h2 += f"<th>{html.escape(str(k))}</th>"
    h2 += "</tr>"

    thead = f"<thead>{h1}{h2}</thead>"

    # Body rows
    tbody_rows = []
    for r in range(len(df)):
        tr = "<tr>"

        # label cols
        for i, col in enumerate(label_cols):
            val = "" if pd.isna(labels.iloc[r][col]) else str(labels.iloc[r][col])
            cls = "sticky" if i == 0 else ("sticky2" if i == 1 else "")
            tr += f'<td class="{cls}">{html.escape(val)}</td>'

        # values
        row_vals = values.iloc[r]
        for col in values.columns:
            v = row_vals[col]
            style = _cell_style(v)
            tr += f'<td style="{style}">{html.escape(str(int(v)))}</td>'
        tr += "</tr>"
        tbody_rows.append(tr)

    tbody = "<tbody>" + "".join(tbody_rows) + "</tbody>"

    table = f'{css}<div class="mx-wrap"><table class="mx">{thead}{tbody}</table></div>'
    st.markdown(table, unsafe_allow_html=True)
