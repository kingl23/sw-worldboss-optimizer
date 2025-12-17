# artifact_analysis.py
from collections import defaultdict
import html

TOP_K = 5


# ----------------------------
# Collect artifacts
# ----------------------------
def collect_all_artifacts(data):
    arts = []

    if isinstance(data.get("artifacts"), list):
        arts.extend(data["artifacts"])

    for u in data.get("unit_list", []):
        if isinstance(u.get("artifacts"), list):
            arts.extend(u["artifacts"])

    return arts


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
                    if not isinstance(art.get("pri_effect"), list):
                        continue
                    if art["pri_effect"][0] != main_id:
                        continue

                    sec = art.get("sec_effects")
                    if not isinstance(sec, list):
                        continue

                    best = None
                    for eff in sec:
                        if (
                            isinstance(eff, list)
                            and len(eff) == 2
                            and eff_from <= eff[0] <= eff_from + 4
                            and (eff[0] - eff_from) == tgt_idx
                        ):
                            best = max(best or 0, eff[1])

                    if best is not None:
                        values.append(best)

                values = sorted(values, reverse=True)[:TOP_K]
                values += [0] * (TOP_K - len(values))

                row[tgt_name] = values

            rows.append(row)

    return rows


# ----------------------------
# Archetype-based summary
# ----------------------------
def artifact_archetype_summary(all_artifacts):
    archetypes = ["Attack", "Defense", "HP", "Support"]
    main_defs = [(100, "HP"), (101, "ATK"), (102, "DEF")]

    sub_defs = [
        (206, "SPD_INC"),
        (404, "S1_REC"),
        (405, "S2_REC"),
        (406, "S3_REC"),
        (407, "S1_ACC"),
        (408, "S2_ACC"),
        (409, "S3_ACC"),
    ]

    rows = []

    for arch_idx, arch_name in enumerate(archetypes, start=1):
        for main_id, main_name in main_defs:
            row = {
                "Archetype": arch_name,
                "Main": main_name,
            }

            for eff_id, eff_name in sub_defs:
                values = []

                for art in all_artifacts:
                    if art.get("type") != 2:
                        continue
                    if art.get("unit_style") != arch_idx:
                        continue
                    if not isinstance(art.get("pri_effect"), list):
                        continue
                    if art["pri_effect"][0] != main_id:
                        continue

                    sec = art.get("sec_effects")
                    if not isinstance(sec, list):
                        continue

                    best = None
                    for eff in sec:
                        if isinstance(eff, list) and len(eff) == 2 and eff[0] == eff_id:
                            best = max(best or 0, eff[1])

                    if best is not None:
                        values.append(best)

                values = sorted(values, reverse=True)[:TOP_K]
                values += [0] * (TOP_K - len(values))

                row[eff_name] = values

            rows.append(row)

    return rows


# ----------------------------
# HTML Renderer
# ----------------------------
def render_artifact_table_html(rows, mode="attribute"):
    if not rows:
        return "<p>No data</p>"

    headers = list(rows[0].keys())

    html_out = """
    <style>
    table {
        border-collapse: collapse;
        width: 100%;
        font-size: 12px;
        text-align: center;
    }
    th, td {
        border: 1px solid #ccc;
        padding: 6px;
    }
    th {
        background-color: #f4f4f4;
    }
    td.group {
        font-weight: bold;
        background-color: #fafafa;
    }
    </style>
    <table>
    <tr>
    """

    for h in headers:
        html_out += f"<th>{html.escape(h)}</th>"
    html_out += "</tr>"

    prev_group = None

    for row in rows:
        html_out += "<tr>"

        for idx, h in enumerate(headers):
            val = row[h]

            if idx == 0:
                if val == prev_group:
                    html_out += "<td></td>"
                else:
                    prev_group = val
                    html_out += f"<td class='group'>{html.escape(str(val))}</td>"
            elif isinstance(val, list):
                html_out += "<td>" + " / ".join(str(x) for x in val) + "</td>"
            else:
                html_out += f"<td>{html.escape(str(val))}</td>"

        html_out += "</tr>"

    html_out += "</table>"
    return html_out
