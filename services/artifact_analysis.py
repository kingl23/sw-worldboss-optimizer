from __future__ import annotations

from typing import Any, Dict, List, Tuple, Iterable
import pandas as pd

TOP_N = 3

ATTR_ORDER = [2, 1, 3, 4, 5]
ATTR_NAMES = ["Fire", "Water", "Wind", "Light", "Dark"]

MAIN_DEFS_ATTR = [
    (100, "HP_DR", 305),
    (102, "DEF_DR", 305),
    (101, "ATK_DD", 300),
]

ARCHETYPE_NAMES = ["Attack", "Defense", "HP", "Support"]
MAIN_DEFS_ARCH = [
    (100, "HP"),
    (101, "ATK"),
    (102, "DEF"),
]
SUB_EFFECTS = [206, 404, 405, 406, 407, 408, 409]
SUB_NAMES = ["SPD_INC", "S1_REC", "S2_REC", "S3_REC", "S1_ACC", "S2_ACC", "S3_ACC"]
EFF_ID_TO_NAME = dict(zip(SUB_EFFECTS, SUB_NAMES))


def collect_all_artifacts(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Collect artifacts from account storage and each unit."""
    all_artifacts: List[Dict[str, Any]] = []

    root_arts = data.get("artifacts", [])
    if isinstance(root_arts, list):
        for a in root_arts:
            if isinstance(a, dict):
                all_artifacts.append(a)

    for u in data.get("unit_list", []) or []:
        if not isinstance(u, dict):
            continue
        arts = u.get("artifacts", [])
        if isinstance(arts, list):
            for a in arts:
                if isinstance(a, dict):
                    all_artifacts.append(a)

    return all_artifacts


def _safe_int(x: Any, default: int = 0) -> int:
    try:
        return int(x)
    except Exception:
        return default


def _parse_pri_effect(art: Dict[str, Any]) -> Tuple[int, float]:
    pri = art.get("pri_effect", [])
    if isinstance(pri, list) and len(pri) >= 2:
        return _safe_int(pri[0]), float(pri[1])
    return 0, 0.0


def _iter_sec_effects(art: Dict[str, Any]) -> Iterable[Tuple[int, float]]:
    sec = art.get("sec_effects", [])
    if not isinstance(sec, list):
        return []
    out: List[Tuple[int, float]] = []
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
    vals = sorted([v for v in values if v is not None], reverse=True)
    top = vals[: min(n, len(vals))]
    top += [0.0] * (n - len(top))
    return [int(round(x)) for x in top]


def artifact_attribute_matrix(all_artifacts: List[Dict[str, Any]], top_n: int = TOP_N) -> pd.DataFrame:
    """Build the attribute matrix with grouped top-N columns."""
    attr_arts = [a for a in all_artifacts if isinstance(a, dict) and "attribute" in a]

    rows = []
    for a_idx, art_attr_id in enumerate(ATTR_ORDER):
        attr_label = ATTR_NAMES[a_idx]
        for r_idx, (main_id, row_name, eff_from) in enumerate(MAIN_DEFS_ATTR):
            row: Dict[Tuple[str, int], int] = {}

            for tgt_attr_name, tgt_attr_index in zip(ATTR_NAMES, range(1, 6)):
                values: List[float] = []
                for art in attr_arts:
                    if _safe_int(art.get("attribute")) != art_attr_id:
                        continue
                    pri_id, _ = _parse_pri_effect(art)
                    if pri_id != main_id:
                        continue

                    tmp: List[float] = []
                    for eff_id, eff_val in _iter_sec_effects(art):
                        if eff_from <= eff_id <= eff_from + 4:
                            if (eff_id - eff_from + 1) == tgt_attr_index:
                                tmp.append(eff_val)
                    if tmp:
                        values.append(max(tmp))

                top_vals = _top_n_desc(values, top_n)
                for k in range(1, top_n + 1):
                    row[(tgt_attr_name, k)] = top_vals[k - 1]

            rows.append(
                {
                    "Attribute": attr_label if r_idx == 0 else "",
                    "Main": row_name,
                    **row,
                }
            )

    value_cols = pd.MultiIndex.from_product([ATTR_NAMES, list(range(1, top_n + 1))])
    df = pd.DataFrame(rows)

    for col in value_cols:
        if col not in df.columns:
            df[col] = 0

    out = df[["Attribute", "Main"] + list(value_cols)]
    return out.reset_index(drop=True)


def artifact_archetype_matrix(all_artifacts: List[Dict[str, Any]], top_n: int = TOP_N) -> pd.DataFrame:
    """Build the archetype matrix with grouped top-N columns."""
    arch_arts = [a for a in all_artifacts if isinstance(a, dict) and "unit_style" in a]

    rows = []
    for arch_id in range(1, 5):
        arch_label = ARCHETYPE_NAMES[arch_id - 1]

        for m_idx, (main_id, main_name) in enumerate(MAIN_DEFS_ARCH):
            row: Dict[Tuple[str, int], int] = {}

            for eff_id in SUB_EFFECTS:
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

                top_vals = _top_n_desc(values, top_n)
                eff_name = EFF_ID_TO_NAME[eff_id]
                for k in range(1, top_n + 1):
                    row[(eff_name, k)] = top_vals[k - 1]

            rows.append(
                {
                    "Archetype": arch_label if m_idx == 0 else "",
                    "Main": main_name,
                    **row,
                }
            )

    value_cols = pd.MultiIndex.from_product([SUB_NAMES, list(range(1, top_n + 1))])

    df = pd.DataFrame(rows)
    for col in value_cols:
        if col not in df.columns:
            df[col] = 0

    out = df[["Archetype", "Main"] + list(value_cols)]
    return out.reset_index(drop=True)
