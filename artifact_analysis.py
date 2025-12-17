import pandas as pd

# ----------------------------
# Collect all artifacts
# ----------------------------
def collect_all_artifacts(data):
    all_artifacts = []
    all_artifacts.extend(data.get("artifacts", []))

    for u in data.get("unit_list", []):
        arts = u.get("artifacts", [])
        if arts:
            all_artifacts.extend(arts)

    return all_artifacts


# ----------------------------
# Artifact Attribute Summary
# ----------------------------
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
            row = {"Attribute": attr_name, "Main": main_name}

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

                row[f"{ATTR_NAMES[tgt_attr-1]}_1"] = top3[0]
                row[f"{ATTR_NAMES[tgt_attr-1]}_2"] = top3[1]
                row[f"{ATTR_NAMES[tgt_attr-1]}_3"] = top3[2]

            rows.append(row)

    return pd.DataFrame(rows)


# ----------------------------
# Artifact Archetype Summary
# ----------------------------
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
            row = {"Archetype": arch_name, "Main": main_name}

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

    return pd.DataFrame(rows)
