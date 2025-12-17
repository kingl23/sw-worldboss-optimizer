import pandas as pd


def collect_all_artifacts(data):
    arts = []
    arts.extend(data.get("artifacts", []))
    for u in data.get("unit_list", []):
        if "artifacts" in u and u["artifacts"]:
            arts.extend(u["artifacts"])
    return arts


# ==============================
# HTML TABLE RENDERER (CORE)
# ==============================
def render_artifact_table_html(df, row_group_col):
    """
    df: summary dataframe
    row_group_col: column name to vertically merge (Attribute / Archetype)
    """

    df = df.reset_index(drop=True)

    # columns
    fixed_cols = [row_group_col, "Main"]
    element_cols = ["Fire", "Water", "Wind", "Light", "Dark"]

    html = """
    <style>
    table {
        border-collapse: collapse;
        width: 100%;
        font-size: 14px;
    }
    th, td {
        border: 1px solid #ddd;
        padding: 8px 12px;
        text-align: center;
        vertical-align: middle;
    }
    th {
        background-color: #f3f3f3;
        font-weight: 600;
    }
    </style>
    <table>
    """

    # ===== HEADER =====
    html += "<tr>"
    for c in fixed_cols:
        html += f"<th>{c}</th>"
    for e in element_cols:
        html += f"<th>{e}</th>"
    html += "</tr>"

    # ===== BODY =====
    i = 0
    while i < len(df):
        row = df.iloc[i]
        group_val = row[row_group_col]

        # count rowspan
        span = 1
        j = i + 1
        while j < len(df) and df.iloc[j][row_group_col] == group_val:
            span += 1
            j += 1

        for k in range(span):
            r = df.iloc[i + k]
            html += "<tr>"

            # merged row-group column
            if k == 0:
                html += f"<td rowspan='{span}'><b>{group_val}</b></td>"

            # Main
            html += f"<td>{r['Main']}</td>"

            # Elements (already merged ①②③)
            for e in element_cols:
                html += f"<td>{r[e]}</td>"

            html += "</tr>"

        i += span

    html += "</table>"
    return html


# ==============================
# SUMMARY BUILDERS
# ==============================
def artifact_attribute_summary(all_artifacts):
    rows = []
    for attr in ["Fire", "Water", "Wind", "Light", "Dark"]:
        for main in ["HP_DR", "DEF_DR", "ATK_DD"]:
            rows.append({
                "Attribute": attr,
                "Main": main,
                "Fire": 0,
                "Water": 0,
                "Wind": 0,
                "Light": 0,
                "Dark": 0,
            })
    return pd.DataFrame(rows)


def artifact_archetype_summary(all_artifacts):
    rows = []
    for arch in ["Attack", "Defense", "HP", "Support"]:
        for main in ["HP", "ATK", "DEF"]:
            rows.append({
                "Archetype": arch,
                "Main": main,
                "Fire": 0,
                "Water": 0,
                "Wind": 0,
                "Light": 0,
                "Dark": 0,
            })
    return pd.DataFrame(rows)
