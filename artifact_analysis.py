# artifact_analysis.py
import pandas as pd


# ----------------------------
# Collect all artifacts
# ----------------------------
def collect_all_artifacts(data):
    all_artifacts = []

    # Account-level artifacts
    if "artifacts" in data and data["artifacts"]:
        all_artifacts.extend(data["artifacts"])

    # Unit-level artifacts
    for u in data.get("unit_list", []):
        arts = u.get("artifacts", [])
        if arts:
            all_artifacts.extend(arts)

    return all_artifacts


# ----------------------------
# Attribute-based summary
# ----------------------------
def artifact_attribute_summary(all_artifacts):
    attr_order = [2, 1, 3, 4, 5]
    attr_names = ["Fire", "Water", "Wind", "Light", "Dark"]

    main_defs = [
        (100, "HP_DR", 305),
        (102, "DEF_DR", 305),
        (101, "ATK_DD", 300),
    ]

    rows = []

    for attr_id, attr_name in zip(attr_order, attr_names):
        for main_id, main_name, eff_from in main_defs:
            row = {
                "Attribute": attr_name,
                "Main": main_name,
            }

            for tgt_attr, tgt_name in zip(attr_order, attr_names):
                values = []

                for art in all_artifacts:
                    if art.get("type") != 1:
                        continue
                    if art.get("attribute") != attr_id:
                        continue
                    if art.get("pri_effect", [None])[0] != main_id:
                        continue

                    for se in art.get("sec_effects", []):
                        eff_id = se[0]
                        eff_val = se[1]

                        if eff_from <= eff_id <= eff_from + 4:
                            if eff_id - eff_from + 1 == tgt_attr:
                                values.append(eff_val)

                values = sorted(values, reverse=True)[:3]
                values += [0] * (3 - len(values))

                row[f"{tgt_name}_1"] = values[0]
                row[f"{tgt_name}_2"] = values[1]
                row[f"{tgt_name}_3"] = values[2]

            rows.append(row)

    df = pd.DataFrame(rows)
    return df


# ----------------------------
# Archetype-based summary
# ----------------------------
def artifact_archetype_summary(all_artifacts):
    archetype_names = ["Attack", "Defense", "HP", "Support"]

    main_defs = [
        (100, "HP"),
        (101, "ATK"),
        (102, "DEF"),
    ]

    sub_effects = [206, 404, 405, 406, 407, 408, 409]
    sub_names = [
        "SPD_INC",
        "S1_REC",
        "S2_REC",
        "S3_REC",
        "S1_ACC",
        "S2_ACC",
        "S3_ACC",
    ]

    rows = []

    for arch_id, arch_name in enumerate(archetype_names, start=1):
        for main_id, main_name in main_defs:
            row = {
                "Archetype": arch_name,
                "Main": main_name,
            }

            for eff_id, eff_name in zip(sub_effects, sub_names):
                values = []

                for art in all_artifacts:
                    if art.get("type") != 2:
                        continue
                    if art.get("unit_style") != arch_id:
                        continue
                    if art.get("pri_effect", [None])[0] != main_id:
                        continue

                    for se in art.get("sec_effects", []):
                        if se[0] == eff_id:
                            values.append(se[1])

                values = sorted(values, reverse=True)[:3]
                values += [0] * (3 - len(values))

                row[f"{eff_name}_1"] = values[0]
                row[f"{eff_name}_2"] = values[1]
                row[f"{eff_name}_3"] = values[2]

            rows.append(row)

    df = pd.DataFrame(rows)
    return df


def render_artifact_table_html(df):
    df = df.copy()
    df = df.reset_index(drop=True)

    # Group columns by suffix (_1, _2, _3)
    grouped_cols = {}
    for col in df.columns:
        if "_" in col and col.split("_")[-1] in ("1", "2", "3"):
            base = col.rsplit("_", 1)[0]
            grouped_cols.setdefault(base, []).append(col)

    html = """
    <style>
    table {
        border-collapse: collapse;
        width: 100%;
        font-size: 14px;
    }
    th, td {
        border: 1px solid #ccc;
        padding: 6px 10px;
        text-align: center;
    }
    th {
        background-color: #f5f5f5;
    }
    </style>
    <table>
    """

    # Header
    html += "<tr>"
    fixed_cols = [c for c in df.columns if c not in sum(grouped_cols.values(), [])]
    for c in fixed_cols:
        html += f"<th>{c}</th>"
    for g in grouped_cols:
        html += f"<th colspan='3'>{g}</th>"
    html += "</tr>"

    # Sub-header
    html += "<tr>"
    for _ in fixed_cols:
        html += "<th></th>"
    for _ in grouped_cols:
        html += "<th>①</th><th>②</th><th>③</th>"
    html += "</tr>"

    # Body
    for _, row in df.iterrows():
        html += "<tr>"
        for c in fixed_cols:
            html += f"<td>{row[c]}</td>"
        for g, cols in grouped_cols.items():
            for c in cols:
                html += f"<td>{row[c]}</td>"
        html += "</tr>"

    html += "</table>"
    return html
