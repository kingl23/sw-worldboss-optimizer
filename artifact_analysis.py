# artifact_analysis.py
from collections import defaultdict
import html

TOP_K = 5  # ← 여기 숫자만 바꾸면 3 → 5 → 10 전부 변경됨


# ----------------------------
# Collect artifacts
# ----------------------------
def collect_all_artifacts(data):
    artifacts = []
    artifacts.extend(data.get("artifacts", []))

    for u in data.get("unit_list", []):
        if "artifacts" in u and u["artifacts"]:
            artifacts.extend(u["artifacts"])

    return artifacts


# ----------------------------
# Attribute-based summary
# ----------------------------
def artifact_attribute_summary(all_artifacts):
    attr_names = ["Fire", "Water", "Wind", "Light", "Dark"]
    main_defs = [
        (100, "HP_DR", 305),
        (102, "DEF_DR", 305),
        (101, "ATK_DD", 300),
    ]

    rows = []

    for attr_idx, attr_name in enumerate(attr_names, start=1):
        for main_id, main_name, eff_from in main_defs:
            row = {
                "Attribute": attr_name,
                "Main": main_name,
            }

            for tgt_attr_idx, tgt_attr_name in enumerate(attr_names, start=1):
                values = []

                for art in all_artifacts:
                    if art.get("type") != 1:
                        continue
                    if art.get("attribute") != attr_idx:
                        continue
                    if art.get("pri_effect", [None])[0] != main_id:
                        continue

                    for eff_id, eff_val in art.get("sec_effects", []):
                        if eff_from <= eff_id <= eff_from + 4:
                            if eff_id - eff_from + 1 == tgt_attr_idx:
                                values.append(eff_val)

                values = sorted(values, reverse=True)[:TOP_K]
                while len(values) < TOP_K:
                    values.append(0)

                row[tgt_attr_name] = values

            rows.append(row)

    return rows


# ----------------------------
# Archetype-based summary
# ----------------------------
def artifact_archetype_summary(all_artifacts):
    archetypes = ["Attack", "Defense", "HP", "Support"]
    main_defs = [(100, "HP"), (101, "ATK"), (102, "DEF")]

    sub_effects = [
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

            for eff_id, eff_name in sub_effects:
                values = []

                for art in all_artifacts:
                    if art.get("type") != 2:
                        continue
                    if art.get("unit_style") != arch_idx:
                        continue
                    if art.get("pri_effect", [None])[0] != main_id:
                        continue

                    for sid, sval in art.get("sec_effects", []):
                        if sid == eff_id:
                            values.append(sval)

                values = sorted(values, reverse=True)[:TOP_K]
                while len(values) < TOP_K:
                    values.append(0)

                row[eff_name] = values

            rows.append(row)

    return rows


# ----------------------------
# HTML Renderer (병합 + 중앙정렬)
# ----------------------------
def render_artifact_table_html(rows, mode="attribute"):
    if not rows:
        return "<p>No data</p>"

    first_col = "Attribute" if mode == "attribute" else "Archetype"

    headers = [first_col, "Main"] + [
        k for k in rows[0].keys() if k not in (first_col, "Main")
    ]

    html_out = """
    <style>
    table { border-collapse: collapse; font-size: 12px; }
    th, td {
        border: 1px solid #ccc;
        padding: 4px 6px;
        text-align: center;
        vertical-align: middle;
        white-space: nowrap;
    }
    th {
        background: #f0f2f6;
        font-weight: 600;
    }
    </style>
    <table>
    <thead><tr>
    """

    for h in headers:
        html_out += f"<th>{html.escape(h)}</th>"
    html_out += "</tr></thead><tbody>"

    prev_val = None
    span_count = 0

    for i, row in enumerate(rows):
        cur_val = row[first_col]

        if cur_val != prev_val:
            if span_count > 0:
                html_out = html_out.replace(
                    f"__ROWSPAN_{prev_val}__",
                    f'rowspan="{span_count}"'
                )
            span_count = 1
            html_out += "<tr>"
            html_out += f'<td __ROWSPAN_{cur_val}__>{html.escape(cur_val)}</td>'
        else:
            span_count += 1
            html_out += "<tr>"

        html_out += f"<td>{row['Main']}</td>"

        for h in headers[2:]:
            v = row[h]
            html_out += "<td>" + " / ".join(map(str, v)) + "</td>"

        html_out += "</tr>"
        prev_val = cur_val

    html_out = html_out.replace(
        f"__ROWSPAN_{prev_val}__",
        f'rowspan="{span_count}"'
    )

    html_out += "</tbody></table>"
    return html_out
