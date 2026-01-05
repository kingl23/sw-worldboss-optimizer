# core_scores.py
import math
from collections import defaultdict

from config import (
    SKILLUP_COEF,
    STAT_KEYS,
    STAT_COEF,
    TYP_TO_STAT_KEY,
    SET_EFFECTS,
)

# ---------- Basic utils ----------


def ceil(x):
    return int(math.ceil(x))


def init_stat():
    return {k: 0.0 for k in STAT_KEYS}


def add_stat(a, b):
    return {k: a[k] + b[k] for k in a}


def stat_struct_score(st):
    # coefficients are defined in config (STAT_COEF)
    return sum(st[k] * STAT_COEF[k] for k in STAT_KEYS)


# ---------- Unit base ----------


def unit_base_char(u):
    return {
        "HP": float(u.get("con", 0)) * 15.0,
        "ATK": float(u.get("atk", 0)),
        "DEF": float(u.get("def", 0)),
        "SPD": float(u.get("spd", 0)),
        "CR": float(u.get("critical_rate", 0)),
        "CD": float(u.get("critical_damage", 0)),
        "RES": float(u.get("resist", 0)),
        "ACC": float(u.get("accuracy", 0)),
    }


# ---------- Rune scoring ----------


def eff_score(typ, val, ch):
    """
    Returns:
      (score_contribution, added_stat_dict)

    - score_contribution = real_value * STAT_COEF[stat_key]
    - added_stat_dict accumulates the real-value (converted) stat for aggregation
    """
    add = init_stat()

    mapping = TYP_TO_STAT_KEY.get(int(typ))
    if mapping is None:
        return 0.0, add

    stat_key, is_percent = mapping

    if is_percent:
        real = ch[stat_key] * float(val) / 100.0
    else:
        real = float(val)

    add[stat_key] = real
    return real * STAT_COEF[stat_key], add


def rune_stat_score(r, ch):
    score = 0.0
    st = init_stat()

    # prefix + primary
    for eff in (r.get("prefix_eff"), r.get("pri_eff")):
        if isinstance(eff, list) and len(eff) >= 2 and eff[0] != 0:
            v, add = eff_score(int(eff[0]), float(eff[1]), ch)
            score += v
            st = add_stat(st, add)

    # secondary (incl grind)
    for row in r.get("sec_eff", []):
        if not row or row[0] == 0:
            continue
        base = float(row[1]) if len(row) > 1 else 0.0
        grind = float(row[3]) if len(row) > 3 else 0.0
        v, add = eff_score(int(row[0]), base + grind, ch)
        score += v
        st = add_stat(st, add)

    return score, st


# ---------- Set effects ----------


def set_effect(set_id, ch):
    cfg = SET_EFFECTS.get(set_id)
    if not cfg:
        return 0, init_stat(), 0.0

    need = int(cfg["need"])
    fixedB = float(cfg.get("fixed", 0.0))

    statB = init_stat()
    for stat_key, v in cfg.get("stat", {}).items():
        if v < 1.0:
            statB[stat_key] = ch[stat_key] * v
        else:
            statB[stat_key] = v

    return need, statB, fixedB


# ---------- Artifact ----------


def artifact_sub_score_only(art):
    score = 0.0

    for row in art.get("sec_effects", []):
        if not row or len(row) < 2:
            continue

        effect_type = int(row[0])
        value = float(row[1])

        # --- artifactSubMax(type) inlined ---
        if effect_type in {200, 201, 202, 203, 207, 208, 211, 212, 213, 216, 217}:
            max_val = 0.0
        elif effect_type in {204, 205, 226, 300, 301, 302, 303, 304}:
            max_val = 5.0
        elif effect_type in {209, 210, 214, 219, 220, 224, 225}:
            max_val = 4.0
        elif effect_type in {
            222, 305, 306, 307, 308, 309,
            400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411
        }:
            max_val = 6.0
        elif effect_type in {215, 223}:
            max_val = 12.0
        elif effect_type == 218:
            max_val = 0.3
        elif effect_type == 221:
            max_val = 40.0
        else:
            max_val = 6.0

        if max_val <= 0:
            continue

        # MATLAB: (value / maxVal) * 25
        score += (value / max_val) * 25.0

    return score


def artifact_score_total(art):
    score = 0.0
    if art.get("pri_effect"):
        score += 120.0
    score += artifact_sub_score_only(art)
    return score


# ---------- Skill-up ----------


def skillup_score(u):
    total = 0
    for row in u.get("skills", []):
        if isinstance(row, list) and len(row) >= 2:
            total += max(0, int(row[1]) - 1)
    return total * SKILLUP_COEF


# ---------- Current unit total ----------


def score_unit_total(u):
    runes = u.get("runes", [])
    if not isinstance(runes, list) or not runes:
        return None

    ch = unit_base_char(u)

    rune_stat_sum = init_stat()
    base_scores = []

    for r in runes:
        s, add = rune_stat_score(r, ch)
        base_scores.append(s)
        rune_stat_sum = add_stat(rune_stat_sum, add)

    set_ids = [int(r.get("set_id", 0)) for r in runes]
    cnt = defaultdict(int)
    for sid in set_ids:
        cnt[sid] += 1

    stat_bonus = init_stat()
    fixed_score = 0.0
    for sid, c in cnt.items():
        need, statB, fixedB = set_effect(sid, ch)
        if need > 0:
            times = c // need
            if need >= 4:
                times = min(times, 1)
            for _ in range(times):
                stat_bonus = add_stat(stat_bonus, statB)
                fixed_score += fixedB

    base_stat_score = stat_struct_score(ch)
    stat_bonus_score = stat_struct_score(stat_bonus)

    artifact_score_sum = 0.0
    art_sub_l = 0.0
    art_sub_r = 0.0
    arts = u.get("artifacts", [])
    if isinstance(arts, list) and arts:
        for art in arts:
            artifact_score_sum += artifact_score_total(art)
            slot = int(art.get("slot", 0))
            if slot == 1:
                art_sub_l = artifact_sub_score_only(art)
            elif slot == 2:
                art_sub_r = artifact_sub_score_only(art)

    su_score = skillup_score(u)

    total_add_stat = add_stat(rune_stat_sum, stat_bonus)

    # NOTE: artifact_score_sum is currently excluded from total_score (as per your existing code)
    total_score = (
        base_stat_score
        + sum(base_scores)
        + stat_bonus_score
        + fixed_score
        + su_score
    )

    print(
        "DEBUG score_unit_total called, stat_bonus_score=",
        stat_bonus_score,
        "fixed_score=",
        fixed_score,
        "cnt=",
        dict(cnt),
    )

    return {
        "unit_id": int(u.get("unit_id", 0)),
        "unit_master_id": int(u.get("unit_master_id", 0)),
        "char": ch,
        "total_add_stat": total_add_stat,
        "base_stat_score": base_stat_score,
        "stat_bonus_score": stat_bonus_score,
        "fixed_score": fixed_score,
        "artifact_score": artifact_score_sum,
        "artifact_sub_l": art_sub_l,
        "artifact_sub_r": art_sub_r,
        "skillup_score": su_score,
        "total_score": total_score,
    }
