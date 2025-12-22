from __future__ import annotations

import html
import pandas as pd
import streamlit as st


def _cell_style_dr(v: int) -> str:
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


def _cell_style_dd(v: int) -> str:
    try:
        x = int(v)
    except Exception:
        return ""

    if x < 18:
        return "background-color:#ff0000;color:#ffffff;"
    if x <= 19:
        return "background-color:#ffff00;color:#000000;"
    if x <= 20:
        return "background-color:#66ff66;color:#000000;"
    return "background-color:#00cc44;color:#ffffff;"


def render_matrix(
    df: pd.DataFrame,
    label_cols: list[str],
    title: str | None = None,
):
    """
    Single HTML table:
      - 2-row header (group colspan)
      - label cols included
      - square numeric cells
      - rowspan merge for Attribute/Archetype group labels (3 rows each)
      - NO thick borders
    """
    if title:
        st.markdown(f"### {title}")

    labels = df[label_cols].copy()
    values = df.drop(columns=label_cols)

    # Coerce tuple columns -> MultiIndex (needed when df has string + tuple mixed)
    if not isinstance(values.columns, pd.MultiIndex):
        if all(isinstance(c, tuple) and len(c) == 2 for c in values.columns):
            values.columns = pd.MultiIndex.from_tuples(values.columns)
        else:
            raise ValueError(
                "Value columns must be 2-tuples (Group, k) or a 2-level MultiIndex."
            )
    if values.columns.nlevels != 2:
        raise ValueError("Value columns must be a 2-level MultiIndex like (Group, k).")

    # Preserve group order
    groups = []
    for g in values.columns.get_level_values(0):
        if g not in groups:
            groups.append(g)

    # Rowspan merge: assume grouped label repeats every 3 rows (HP/DEF/ATK)
    merge_every = 3
    group_key_col = label_cols[0]  # "Attribute" or "Archetype"

    # CSS (NO thick separators)
    css = """
    <style>
      .mx-wrap { overflow-x: auto; }

      table.mx {
        border-collapse: collapse;
        width: max-content;
        min-width: 100%;
        font-size: 13px;
      }

      /* base cell */
      table.mx th, table.mx td {
        border: 1px solid #000;
        text-align: center;
        white-space: nowrap;
        padding: 0;
      }

      table.mx thead th {
        background: #f3f3f3;
        font-weight: 700;
        padding: 6px 8px;
      }

      /* label columns width tighten */
      table.mx th.lbl1, table.mx td.lbl1 {
        width: 90px; min-width: 90px; max-width: 90px;
        padding: 6px 8px;
      }
      table.mx th.lbl2, table.mx td.lbl2 {
        width: 85px; min-width: 85px; max-width: 85px;
        padding: 6px 8px;
      }

      /* numeric cells: square-ish */
      table.mx td.num {
        width: 40px; min-width: 40px; max-width: 40px;
        height: 40px; min-height: 40px; max-height: 40px;
        line-height: 40px;
        font-weight: 600;
      }
    </style>
    """

    # ---------- header ----------
    h1 = "<tr>"
    for i, col in enumerate(label_cols):
        cls = "lbl1" if i == 0 else "lbl2"
        h1 += f'<th class="{cls}" rowspan="2">{html.escape(col)}</th>'

    for g in groups:
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

    # ---------- body with rowspan ----------
    tbody_rows = []
    n = len(df)

    for r in range(n):
        tr = "<tr>"

        row_block_start = (r % merge_every == 0)

        # label col 0: merged every 3 rows
        if row_block_start:
            label_val = labels.iloc[r][group_key_col]
            if (label_val is None) or (str(label_val).strip() == ""):
                for rr in range(r, min(r + merge_every, n)):
                    v = labels.iloc[rr][group_key_col]
                    if v is not None and str(v).strip() != "":
                        label_val = v
                        break
            label_val = "" if pd.isna(label_val) else str(label_val)

            tr += f'<td class="lbl1" rowspan="{merge_every}">{html.escape(label_val)}</td>'

        # label col 1: always present (Main)
        main_val = labels.iloc[r][label_cols[1]]
        main_val = "" if pd.isna(main_val) else str(main_val)
        tr += f'<td class="lbl2">{html.escape(main_val)}</td>'

        # numeric cells
        row_vals = values.iloc[r]
        main_val_for_style = str(labels.iloc[r][label_cols[1]] or "")

        for col in values.columns:
            v = row_vals[col]
            if main_val_for_style.endswith("_DD"):
                style = _cell_style_dd(v)
            else:
                style = _cell_style_dr(v)

            tr += f'<td class="num" style="{style}">{html.escape(str(int(v)))}</td>'

        tr += "</tr>"
        tbody_rows.append(tr)

    tbody = "<tbody>" + "".join(tbody_rows) + "</tbody>"
    table = f'{css}<div class="mx-wrap"><table class="mx">{thead}{tbody}</table></div>'
    st.markdown(table, unsafe_allow_html=True)
