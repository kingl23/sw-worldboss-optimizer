# artifact_analysis.py
import pandas as pd

# ============================================================
# Collect all artifacts from JSON
# ============================================================
def collect_all_artifacts(data):
    all_artifacts = []

    # Global artifacts
    all_artifacts.extend(data.get("artifacts", []))

    # Unit-bound artifacts
    for u in data.get("unit_list", []):
        arts = u.get("artifacts", [])
        if arts:
            all_artifacts.extend(arts)

    return all_artifacts


# ============================================================
# Common helpers
# ============================================================
def collapse_identical_triplets(df):
    """
    If *_1, *_2, *_3 columns are identical across all rows,
    collapse them into a single column.
    """
    df = df.copy()
    new_cols = []
    skip = set()

    for col in df.columns:
        if col.endswith("_1"):
            base = col[:-2]
            c1, c2, c3 = f"{base}_1", f"{base}_2", f"{base}_3"

            if c2 in df.columns and c3 in df.columns:
                if (df[c1] == df[c2]).all() and (df[c1] == df[c3]).all():
                    df[base] = df[c1]
                    skip.update([c1, c2, c3])
                    new_cols.append(base)
                else:
                    new_cols.extend([c1, c2, c3])
        elif col not in skip:
            new_cols.append(col)

    return df[new_cols]


def style_artifact_table(df):
    """
    Styling for artifact summary tables:
    - No index
    - Equal emphasis for non-zero values
    - Zero values de-emphasized
    - Larger padding & readable font
    """
    def cell_style(val):
        if val == 0:
            return "color: #bbbbbb;"
        return (
            "background-color: #eef7f1;"
            "color: black;"
            "font-weight: normal;"
        )

    styled = (
        df.style
        .applymap(cell_style)
        .set_properties(**{
            "text-align": "center",
            "font-size": "13px",
            "padding": "8px",
            "border": "1px solid #dddddd",
            "min-width": "48px",
        })
        .set_table_styles([
            {
                "selector": "th",
                "props": [
                    ("font-size", "14px"),
                    ("font-weight", "bold"),
                    ("background-color", "#f5f5f5"),
                    ("text-align", "center"),
                    ("padding", "10px"),
                    ("border", "1px solid #cccccc"),
                ],
            }
        ])
    )

    return styled


# ============================================================
# Attribute-based Artifact Summary (MATLAB #1)
# ============================================================
ATTR_ORDER = [2, 1, 3, 4, 5]
ATTR_NAMES = ["Fire", "Water", "Wind", "Light", "Dark"]

MAIN_DEFS_ATTR = [
    (100, "HP_DR", 305),
    (102, "DEF_DR", 305),
    (101, "ATK_DD", 300),
]


def artifact_attribute_summary(all_artifacts):
    rows = []

    for attr_idx, attr in enumerate(ATTR_ORDER):
        attr_name = ATTR_NAMES[attr_idx]

        for main_id, main_name, eff_from in MAIN_DEFS_ATTR:
            row = {
                "Attribute": attr_name,
                "Main": main_name,
            }

            for tgt_attr in range(1, 6):
                values = []

                for art in all_artifacts:
                    if art.get("type") != 1:
                        continue
                    if art.get("attribute") != attr:
                        continue
                    if art.get("pri_effect", [None])[0] != main_id:
                        continue

                    tmp = []
                    for eff in art.get("sec_effects", []):
                        eff_id, eff_val = eff[0], eff[1]
                        if eff_from <= eff_id <= eff_from + 4:
                            if eff_id - eff_from + 1 == tgt_attr:
                                tmp.append(eff_val)

                    if tmp:
                        values.append(max(tmp))

                values.sort(reverse=True)
                top3 = values[:3] + [0] * (3 - len(values))

                base = ATTR_NAMES[tgt_attr - 1]
                row[f"{base}_1"] = top3[0]
                row[f"{base}_2"] = top3[1]
                row[f"{base}_3"] = top3[2]

            rows.append(row)

    df = pd.DataFrame(rows)
    df = df.reset_index(drop=True)
    df = collapse_identical_triplets(df)
    return df


# ============================================================
# Archetype-based Artifact Summary (MATLAB #2)
# ============================================================
ARCHETYPES = ["Attack", "Defense", "HP", "Support"]

MAIN_DEFS_ARCH = [
    (100, "HP"),
    (101, "ATK"),
    (102, "DEF"),
]

SUB_EFFECTS = [
    (206, "SPD_INC"),
    (404, "S1_REC"),
    (405, "S2_REC"),
    (406, "S3_REC"),
    (407, "S1_ACC"),
    (408, "S2_ACC"),
    (409, "S3_ACC"),
]


def artifact_archetype_summary(all_artifacts):
    rows = []

    for arch_idx, arch_name in enumerate(ARCHETYPES, start=1):
        for main_id, main_name in MAIN_DEFS_ARCH:
            row = {
                "Archetype": arch_name,
                "Main": main_name,
            }

            for eff_id, eff_name in SUB_EFFECTS:
                values = []

                for art in all_artifacts:
                    if art.get("type") != 2:
                        continue
                    if art.get("unit_style") != arch_idx:
                        continue
                    if art.get("pri_effect", [None])[0] != main_id:
                        continue

                    tmp = [
                        eff[1]
                        for eff in art.get("sec_effects", [])
                        if eff[0] == eff_id
                    ]

                    if tmp:
                        values.append(max(tmp))

                values.sort(reverse=True)
                top3 = values[:3] + [0] * (3 - len(values))

                row[f"{eff_name}_1"] = top3[0]
                row[f"{eff_name}_2"] = top3[1]
                row[f"{eff_name}_3"] = top3[2]

            rows.append(row)

    df = pd.DataFrame(rows)
    df = df.reset_index(drop=True)
    df = collapse_identical_triplets(df)
    return df
