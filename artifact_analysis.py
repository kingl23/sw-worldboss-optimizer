# artifact_analysis.py
from __future__ import annotations

from typing import Any, Dict, List, Tuple
import pandas as pd

# Change this one number only
TOP_N = 3


# ----------------------------
# Collect
# ----------------------------
def collect_all_artifacts(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Collect artifacts from both account-level and each unit."""
    all_artifacts: List[Dict[str, Any]] = []

    # account-level artifacts (some exports use this)
    root_arts = data.get("artifacts", [])
    if isinstance(root_arts, list):
        for a in root_arts:
            if isinstance(a, dict):
                all_artifacts.append(a)

    # unit-level artifacts
    for u in data.get("unit_list", []) or []:
        if not isinstance(u, dict):
            continue
        arts = u.get("artifacts", [])
        if isinstance(arts, list):
            for a in arts:
                if isinstance(a, dict):
                    all_artifacts.append(a)

    return all_artifacts


# ----------------------------
# Robust parsers
# ----------------------------
def _safe_int(x: Any, default: int = 0) -> int:
    try:
        return int(x)
    except Exception:
        return default


def _parse_pri_effect(art: Dict[str, Any]) -> Tuple[int, float]:
    """Return (effect_id, value) from pri_effect like [id, val]."""
    pri = art.get("pri_effect", [])
    if isinstance(pri, list) and len(pri) >= 2:
        return _safe_int(pri[0]), float(pri[1])
    return 0, 0.0


def _iter_sec_effects(art: Dict[str, Any]) -> List[Tuple[int, float]]:
    """
    Return list of (eff_id, eff_val) from sec_effects.
    Handles cases:
      - [[id,val], [id,val], ...]
      - [[id,val, ...], ...]
      - weird/empty -> []
    """
    sec = art.get("sec_effects", [])
    out: List[Tuple[int, float]] = []

    if not isinstance(sec, list):
        return out

    for row in sec:
        if not isinstance(row, (list, tuple)) or len(row) < 2:
            continue
        eff_id = _safe_int(row[0])
        try:
            eff_val = float(row[1])
        except Exception:
            eff_val = 0.0
        out.append((eff_id, eff_val))

    return out


def _top_n_desc(values: List[float], n: int) -> List[int]:
    values_sorted = sorted([v for v in values if v is not None], reverse=True)
    top = values_sorted[: min(n, len(values_sorted))]
    top += [0] * (n - len(top))
    return [int(round(x)) for x in top]


def _join_slash(nums: List[int]) -> str:
    return " / ".join(str(x) for x in nums)


# ----------------------------
# Attribute-based summary
# ----------------------------
def artifact_attribute_summary(all_artifacts: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Output columns:
      Attribute | Main | Fire | Water | Wind | Light | Dark
    Each element cell is: "v1 / v2 / ... / v5" (TOP_N)
    """
    # Keep same ordering as your MATLAB
    attr_order = [2, 1, 3, 4, 5]  # show Fire first, then Water...
    attr_names = ["Fire", "Water", "Wind", "Light", "Dark"]

    # (mainId, rowName, effFrom)
    main_defs = [
        (100, "HP_DR", 305),
        (102, "DEF_DR", 305),
        (101, "ATK_DD", 300),
    ]

    # Filter by presence of 'attribute' (do NOT trust art["type"])
    attr_arts = [a for a in all_artifacts if isinstance(a, dict) and "attribute" in a]

    rows: List[Dict[str, Any]] = []

    for a_idx, art_attr_id in enumerate(attr_order):
        attr_label = attr_names[a_idx]

        for r_idx, (main_id, row_name, eff_from) in enumerate(main_defs):
            row: Dict[str, Any] = {
                "Attribute": attr_label if r_idx == 0 else "",
                "Main": row_name,
            }

            for tgt_attr_name, tgt_attr_index in zip(attr_names, range(1, 6)):
                values: List[float] = []

                for art in attr_arts:
                    if _safe_int(art.get("attribute")) != art_attr_id:
                        continue

                    pri_id, _ = _parse_pri_effect(art)
                    if pri_id != main_id:
                        continue

                    tmp: List[float] = []
                    for eff_id, eff_val in _iter_sec_effects(art):
                        # Range match (eff_from ~ eff_from+4), slot match by offset
                        if eff_from <= eff_id <= eff_from + 4:
                            if (eff_id - eff_from + 1) == tgt_attr_index:
                                tmp.append(eff_val)

                    if tmp:
                        values.append(max(tmp))

                top = _top_n_desc(values, TOP_N)
                row[tgt_attr_name] = _join_slash(top)

            rows.append(row)

    df = pd.DataFrame(rows, columns=["Attribute", "Main"] + attr_names)
    return df.reset_index(drop=True)


# ----------------------------
# Archetype-based summary
# ----------------------------
def artifact_archetype_summary(all_artifacts: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Output columns:
      Archetype | Main | SPD_INC | S1_REC | S2_REC | S3_REC | S1_ACC | S2_ACC | S3_ACC
    Each cell is: "v1 / v2 / ... / v5" (TOP_N)
    """
    archetype_names = ["Attack", "Defense", "HP", "Support"]

    main_defs = [
        (100, "HP"),
        (101, "ATK"),
        (102, "DEF"),
    ]

    sub_effects = [206, 404, 405, 406, 407, 408, 409]
    sub_names = ["SPD_INC", "S1_REC", "S2_REC", "S3_REC", "S1_ACC", "S2_ACC", "S3_ACC"]
    eff_id_to_name = dict(zip(sub_effects, sub_names))

    # Filter by presence of 'unit_style' (do NOT trust art["type"])
    arch_arts = [a for a in all_artifacts if isinstance(a, dict) and "unit_style" in a]

    rows: List[Dict[str, Any]] = []

    for arch_id in range(1, 5):
        arch_label = archetype_names[arch_id - 1]

        for m_idx, (main_id, main_name) in enumerate(main_defs):
            row: Dict[str, Any] = {
                "Archetype": arch_label if m_idx == 0 else "",
                "Main": main_name,
            }

            for eff_id in sub_effects:
                values: List[float] = []

                for art in arch_arts:
                    if _safe_int(art.get("unit_style")) != arch_id:
                        continue

                    pri_id, _ = _parse_pri_effect(art)
                    if pri_id != main_id:
                        continue

                    tmp = [v for (eid, v) in _iter_sec_effects(art) if eid == eff_id]
                    if tmp:
                        values.append(max(tmp))

                top = _top_n_desc(values, TOP_N)
                row[eff_id_to_name[eff_id]] = _join_slash(top)

            rows.append(row)

    df = pd.DataFrame(rows, columns=["Archetype", "Main"] + sub_names)
    return df.reset_index(drop=True)
