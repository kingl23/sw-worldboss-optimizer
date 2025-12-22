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
    Single HTML table:
      - 2-row header (group colspan)
      - label cols included
      - square numeric cells
      - rowspan merge for Attribute/Archetype group labels (3 rows each)
      - thicker borders between 3x3 blocks (group boundaries)
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
            raise ValueError("Value columns must be 2-tuples (Group, k) or a 2-level MultiIndex.")
    if values.columns.nlevels != 2:
        raise ValueError("Value columns must be a 2-level MultiIndex like (Group, k).")

    # Preserve group order
    groups = []
    for g in values.columns.get_level_values(0):
        if g not in groups:
            groups.append(g)

    # Determine where to draw thick borders:
    # - after Main column
    # - after each group block (Fire|Water|...)
    group_last_col = {}
    for g in groups:
        subcols = [c for c in values.columns if c[0] == g]
        group_last_col[g] = subcols[-1]  # last (g,k)

    # Rowspan merge: assume grouped label repeats every 3 rows (HP/DEF/ATK)
    # Works for both Attribute matrix (3 rows per element) and Archetype matrix (3 rows per archetype)
    merge_every = 3
    group_key_col = label_cols[0]  # "Attribute" or "Archetype"

    # CSS
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

      /* thick separators */
      table.mx .sep-right { border-right: 3px solid #000 !important; }
      table.mx .sep-left  { border-left:  3px solid #000 !important; }
      table.mx .sep-top   { border-top:   3px solid #000 !important; }
      table.mx .sep-bot   { border-bottom:3px solid #000 !important; }
    </style>
    """

    # ---------- header ----------
    h1 = "<tr>"
    # label headers rowspan=2
    for i, col in enumerate(label_cols):
        cls = "lbl1" if i == 0 else "lbl2"
        # add thick right border after Main header
        extra = " sep-right" if i == 1 else ""
        h1 += f'<th class="{cls}{extra}" rowspan="2">{html.escape(col)}</th>'

    for g in groups:
        subcols = [c for c in values.columns if c[0] == g]
        # thick right border at end of each group
        extra = " sep-right" if g != groups[-1] else ""
        h1 += f'<th class="{extra}" colspan="{len(subcols)}">{html.escape(str(g))}</th>'
    h1 += "</tr>"

    h2 = "<tr>"
    for g in groups:
        subcols = [c for c in values.columns if c[0] == g]
        for (_, k) in subcols:
            extra = ""
            # thick right border at end of group
            if (g, k) == group_last_col[g] and g != groups[-1]:
                extra = " sep-right"
            h2 += f'<th class="{extra}">{html.escape(str(k))}</th>'
    h2 += "</tr>"

    thead = f"<thead>{h1}{h2}</thead>"

    # ---------- body with rowspan ----------
    tbody_rows = []

    # Precompute rowspan starts: every 3 rows, take label if present else infer from next non-empty
    # We will render merged cell only at row indices 0,3,6,9,12...
    n = len(df)

    for r in range(n):
        tr = "<tr>"

        # Add thick horizontal separators between 3-row blocks
        row_block_start = (r % merge_every == 0)
        row_block_end = ((r + 1) % merge_every == 0)

        # label col 0: merged every 3 rows
        if row_block_start:
            # find label value (sometimes stored only on first row)
            label_val = labels.iloc[r][group_key_col]
            if (label_val is None) or (str(label_val).strip() == ""):
                # try lookahead within block
                for rr in range(r, min(r + merge_every, n)):
                    v = labels.iloc[rr][group_key_col]
                    if v is not None and str(v).strip() != "":
                        label_val = v
                        break
            label_val = "" if pd.isna(label_val) else str(label_val)

            extra = " sep-top" if row_block_start and r != 0 else ""
            extra += " sep-bot" if row_block_end else ""
            tr += f'<td class="lbl1{extra}" rowspan="{merge_every}">{html.escape(label_val)}</td>'

        # label col 1: always present (Main)
        main_val = labels.iloc[r][label_cols[1]]
        main_val = "" if pd.isna(main_val) else str(main_val)
        extra_main = " sep-right"
        if row_block_start and r != 0:
            extra_main += " sep-top"
        if row_block_end:
            extra_main += " sep-bot"
        tr += f'<td class="lbl2{extra_main}">{html.escape(main_val)}</td>'

        # numeric cells
        row_vals = values.iloc[r]
        for col in values.columns:
            v = row_vals[col]
            style = _cell_style(v)

            extra = ""
            g, k = col

            # thick vertical lines at end of each group block
            if col == group_last_col[g] and g != groups[-1]:
                extra += " sep-right"

            # thick horizontal lines between 3-row blocks
            if row_block_start and r != 0:
                extra += " sep-top"
            if row_block_end:
                extra += " sep-bot"

            tr += f'<td class="num{extra}" style="{style}">{html.escape(str(int(v)))}</td>'

        tr += "</tr>"
        tbody_rows.append(tr)

    tbody = "<tbody>" + "".join(tbody_rows) + "</tbody>"

    table = f'{css}<div class="mx-wrap"><table class="mx">{thead}{tbody}</table></div>'
    st.markdown(table, unsafe_allow_html=True)
