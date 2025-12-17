import pandas as pd
from collections import defaultdict

TOP_K = 5

# ============================
# Collect artifacts
# ============================
def collect_all_artifacts(data):
    artifacts = []
    artifacts.extend(data.get("artifacts", []))
    for u in data.get("unit_list", []):
        if "artifacts" in u and u["artifacts"]:
            artifacts.extend(u["artifacts"])
    return artifacts


# ============================
# Attribute-based summary
# ============================
def artifact_attribute_summary(all_artifacts):
    attr_order = [2, 1, 3, 4, 5]
    attr_names = ["Fire", "Water", "Wind", "Light", "Dark"]

    main_defs = [
        (100, "HP_DR", 305),
        (102, "DEF_DR", 305),
        (101, "ATK_DD", 300),
    ]

    rows = []

    for a_idx, art_attr in enumerate(attr_order):
        for main_id, main_name, eff_from in main_defs:
            row = {
                "Attribute": attr_names[a_idx],
                "Main": main_name,
            }

            for tgt_idx, tgt_name in enumerate(attr_names):
                values = []

                for art in all_artifacts:
                    if art.get("type") != 1:
                        continue
                    if art.get("attribute") != art_attr:
                        continue
                    if art.get("pri_effect", [0])[0] != main_id:
                        continue

                    tmp = []
                    for eff in art.get("sec_effects", []):
                        eff_id, eff_val = eff[0], eff[1]
                        if eff_from <= eff_id <= eff_from + 4:
                            if eff_id - eff_from == tgt_idx:
                                tmp.append(eff_val)

                    if tmp:
                        values.append(max(tmp))

                values = sorted(values, reverse=True)
                top_vals = values[:TOP_K]
                top_vals += [0] * (TOP_K - len(top_vals))

                row[tgt_name] = values

            rows.append(row)

    return rows


# ============================
# Archetype-based summary
# ============================
def artifact_archetype_summary(all_artifacts):
    archetypes = ["Attack", "Defense", "HP", "Support"]
    main_defs = [(100, "HP"), (101, "ATK"), (102, "DEF")]

    sub_effects = [206, 404, 405, 406, 407, 408, 409]
    sub_names = [
        "SPD_INC", "S1_REC", "S2_REC", "S3_REC",
        "S1_ACC", "S2_ACC", "S3_ACC"
    ]

    rows = []

    for arch_idx, arch in enumerate(archetypes, start=1):
        for main_id, main_name in main_defs:
            row = {
                "Archetype": arch,
                "Main": main_name,
            }

            for eff_id, eff_name in zip(sub_effects, sub_names):
                values = []

                for art in all_artifacts:
                    if art.get("type") != 2:
                        continue
                    if art.get("unit_style") != arch_idx:
                        continue
                    if art.get("pri_effect", [0])[0] != main_id:
                        continue

                    tmp = [
                        eff[1] for eff in art.get("sec_effects", [])
                        if eff[0] == eff_id
                    ]

                    if tmp:
                        values.append(max(tmp))

                values = sorted(values, reverse=True)[:3]
                values += [0] * (3 - len(values))

                row[eff_name] = values

            rows.append(row)

    return rows


# ============================
# HTML renderer (merged rows)
# ============================
def render_artifact_table_html(rows, mode="attribute"):
    html = """
    <style>
    table {
        border-collapse: collapse;
        width: 100%;
        font-size: 12px;
    }
    th, td {
        border: 1px solid #ddd;
        padding: 4px 6px;
        text-align: center;
        vertical-align: middle;
    }
    th {
        background: #f2f2f2;
        font-weight: 600;
    }
    </style>
    <table>
    """

    if mode == "attribute":
        headers = ["Attribute", "Main", "Fire", "Water", "Wind", "Light", "Dark"]
    else:
        headers = ["Archetype", "Main"] + list(rows[0].keys())[2:]

    html += "<tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr>"

    prev_group = None
    span_count = 0

    for i, row in enumerate(rows):
        group_key = row[headers[0]]

        if group_key != prev_group:
            span_count = sum(
                1 for r in rows if r[headers[0]] == group_key
            )
            html += "<tr>"
            html += f"<td rowspan='{span_count}'><b>{group_key}</b></td>"
        else:
            html += "<tr>"

        html += f"<td>{row['Main']}</td>"

        for h in headers[2:]:
            v = row[h]
            if isinstance(v, list):
                html += f"<td>{v[0]} / {v[1]} / {v[2]}</td>"
            else:
                html += f"<td>{v}</td>"

        html += "</tr>"
        prev_group = group_key

    html += "</table>"
    return html
