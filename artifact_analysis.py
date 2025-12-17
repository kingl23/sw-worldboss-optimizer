# artifact_analysis.py
import pandas as pd

# ============================
# One knob
# ============================
TOP_K = 5  # Change only this (e.g., 3 -> 5)

# ============================
# Constants (MATLAB parity)
# ============================
ATTR_ORDER = [2, 1, 3, 4, 5]
ATTR_NAMES = {1: "Fire", 2: "Water", 3: "Wind", 4: "Light", 5: "Dark"}

# mainDefs = { mainId, rowName, effFrom }
MAIN_DEFS_ATTR = [
    (100, "HP_DR", 305, 309),
    (102, "DEF_DR", 305, 309),
    (101, "ATK_DD", 300, 304),
]

ARCHETYPE_NAMES = {1: "Attack", 2: "Defense", 3: "HP", 4: "Support"}
MAIN_DEFS_ARCH = [
    (100, "HP"),
    (101, "ATK"),
    (102, "DEF"),
]
SUB_EFFECTS = [206, 404, 405, 406, 407, 408, 409]
SUB_NAMES = {
    206: "SPD_INC",
    404: "S1_REC",
    405: "S2_REC",
    406: "S3_REC",
    407: "S1_ACC",
    408: "S2_ACC",
    409: "S3_ACC",
}

# ============================
# Helpers
# ============================
def _as_list(x):
    return x if isinstance(x, list) else []

def _iter_sec_effects(sec_effects):
    """
    sec_effects can be list of [type, value] or list of lists.
    Return iterator of (eff_id:int, eff_val:float).
    """
    if not isinstance(sec_effects, list):
        return
    for row in sec_effects:
        if not isinstance(row, list) or len(row) < 2:
            continue
        try:
            eff_id = int(row[0])
            eff_val = float(row[1])
        except Exception:
            continue
        yield eff_id, eff_val

def _top_k_padded(values, k=TOP_K):
    """
    Sort desc, take top-k, pad with zeros to exactly k length.
    """
    values = sorted(values, reverse=True)
    out = values[:k]
    if len(out) < k:
        out += [0] * (k - len(out))
    return out

def _join_vals(vals):
    """
    Always show exactly TOP_K values in one cell.
    No emphasis on 1/2/3: equal visual weight.
    """
    return " / ".join(str(int(v)) for v in vals)

# ============================
# Public API
# ============================
def collect_all_artifacts(data):
    """
    MATLAB parity:
      allArtifacts = [data.artifacts] + unit_list[*].artifacts
    """
    all_arts = []
    if isinstance(data, dict):
        all_arts += _as_list(data.get("artifacts", []))
        for u in _as_list(data.get("unit_list", [])):
            if isinstance(u, dict):
                all_arts += _as_list(u.get("artifacts", []))
    return all_arts

def artifact_attribute_summary(all_artifacts, top_k=TOP_K):
    """
    Equivalent to artifact_summary.xlsx part (type == 1).
    Output columns: Attribute | Main | Fire | Water | Wind | Light | Dark
    Each element is a string of exactly top_k values: "a / b / c / d / e"
    """
    cols = ["Attribute", "Main"] + [ATTR_NAMES[i] for i in [1, 2, 3, 4, 5]]
    rows = []

    for a_idx, art_attr in enumerate(ATTR_ORDER):
        attr_name = ATTR_NAMES.get(art_attr, str(art_attr))

        for r, (main_id, row_name, eff_from, eff_to) in enumerate(MAIN_DEFS_ATTR):
            row = {"Attribute": attr_name if r == 0 else "", "Main": row_name}

            # target attribute columns Fire..Dark => 1..5
            for tgt_attr in [1, 2, 3, 4, 5]:
                values = []

                for art in all_artifacts:
                    if not isinstance(art, dict):
                        continue
                    # MATLAB: if art.type ~= 1; continue;
                    if int(art.get("type", 0)) != 1:
                        continue
                    # MATLAB: if art.attribute ~= artAttr; continue;
                    if int(art.get("attribute", 0)) != int(art_attr):
                        continue
                    # MATLAB: if art.pri_effect(1) ~= mainId; continue;
                    pri = art.get("pri_effect", [])
                    if not (isinstance(pri, list) and len(pri) >= 1 and int(pri[0]) == int(main_id)):
                        continue

                    tmp = []
                    for eff_id, eff_val in _iter_sec_effects(art.get("sec_effects", [])):
                        if eff_id < eff_from or eff_id > eff_to:
                            continue
                        # MATLAB: if effId - effFrom + 1 == tgtAttr
                        if (eff_id - eff_from + 1) == tgt_attr:
                            tmp.append(eff_val)

                    if tmp:
                        values.append(max(tmp))

                top_vals = _top_k_padded(values, k=top_k)
                row[ATTR_NAMES[tgt_attr]] = _join_vals(top_vals)

            rows.append(row)

    df = pd.DataFrame(rows, columns=cols)
    return df

def artifact_archetype_summary(all_artifacts, top_k=TOP_K):
    """
    Equivalent to archetype_sub_effect_summary.xlsx part (type == 2).
    Output columns: Archetype | Main | SPD_INC | S1_REC | ... | S3_ACC
    Each element is a string of exactly top_k values: "a / b / c / d / e"
    """
    effect_cols = [SUB_NAMES[e] for e in SUB_EFFECTS]
    cols = ["Archetype", "Main"] + effect_cols
    rows = []

    for arch in [1, 2, 3, 4]:
        arch_name = ARCHETYPE_NAMES.get(arch, str(arch))

        for m_i, (main_id, main_name) in enumerate(MAIN_DEFS_ARCH):
            row = {"Archetype": arch_name if m_i == 0 else "", "Main": main_name}

            for eff_id in SUB_EFFECTS:
                values = []

                for art in all_artifacts:
                    if not isinstance(art, dict):
                        continue
                    # MATLAB: if art.type ~= 2; continue;
                    if int(art.get("type", 0)) != 2:
                        continue
                    # MATLAB: if art.unit_style ~= arch; continue;
                    if int(art.get("unit_style", 0)) != int(arch):
                        continue
                    # MATLAB: if art.pri_effect(1) ~= mainId; continue;
                    pri = art.get("pri_effect", [])
                    if not (isinstance(pri, list) and len(pri) >= 1 and int(pri[0]) == int(main_id)):
                        continue

                    tmp = []
                    for s_id, s_val in _iter_sec_effects(art.get("sec_effects", [])):
                        if s_id == int(eff_id):
                            tmp.append(s_val)

                    if tmp:
                        values.append(max(tmp))

                top_vals = _top_k_padded(values, k=top_k)
                row[SUB_NAMES[eff_id]] = _join_vals(top_vals)

            rows.append(row)

    df = pd.DataFrame(rows, columns=cols)
    return df

def style_artifact_table(df: pd.DataFrame):
    """
    Streamlit-friendly styling:
    - Hide index
    - Center all cells
    - Improve padding & font
    - Make table compact
    """
    if not isinstance(df, pd.DataFrame):
        df = pd.DataFrame(df)

    styler = df.style

    # Hide index (works on recent pandas)
    try:
        styler = styler.hide(axis="index")
    except Exception:
        # fallback: keep index if hide not available
        pass

    # Center & compact
    styler = styler.set_table_styles(
        [
            {"selector": "table", "props": [("width", "100%"), ("border-collapse", "collapse")]},
            {"selector": "th", "props": [
                ("text-align", "center"),
                ("font-weight", "600"),
                ("font-size", "13px"),
                ("padding", "6px 8px"),
                ("border", "1px solid rgba(0,0,0,0.08)"),
                ("background-color", "rgba(0,0,0,0.03)"),
                ("white-space", "nowrap"),
            ]},
            {"selector": "td", "props": [
                ("text-align", "center"),
                ("font-size", "12px"),
                ("padding", "6px 8px"),
                ("border", "1px solid rgba(0,0,0,0.08)"),
                ("vertical-align", "middle"),
                ("white-space", "nowrap"),
            ]},
        ]
    )

    return styler
