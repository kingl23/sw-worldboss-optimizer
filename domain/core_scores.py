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


def stat_struct_score(st, stat_coef=None):
    # coefficients are defined in config (STAT_COEF)
    coef = stat_coef or STAT_COEF
    return sum(st[k] * coef[k] for k in STAT_KEYS)


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


# ---------- Flag bonus (base 기준 delta만 계산) ----------


def flag_bonus_delta(ch_base):
    """
    Compute base-flag bonuses as DELTA stats (do NOT mutate or replace base).
    Requirements:
      - SPD +15% (of base)
      - HP  +20% (of base)
      - DEF +20% (of base)
      - ATK +41% (of base)
      - CD  +25  (flat)
    """
    d = init_stat()
    d["SPD"] = ch_base["SPD"] * 0.15
    d["HP"] = ch_base["HP"] * 0.20
    d["DEF"] = ch_base["DEF"] * 0.20
    d["ATK"] = ch_base["ATK"] * 0.41
    d["CD"] = 25.0
    return d


# ---------- Rune scoring ----------


def eff_score(typ, val, ch_base, stat_coef=None):
    """
    Returns:
      (score_contribution, added_stat_dict)

    - score_contribution = real_value * STAT_COEF[stat_key]
    - real_value uses BASE ch for percent conversions
    """
    add = init_stat()

    mapping = TYP_TO_STAT_KEY.get(int(typ))
    if mapping is None:
        return 0.0, add

    stat_key, is_percent = mapping

    if is_percent:
        real = ch_base[stat_key] * float(val) / 100.0
    else:
        real = float(val)

    add[stat_key] = real
    coef = stat_coef or STAT_COEF
    return real * coef[stat_key], add


def rune_stat_score(r, ch_base, stat_coef=None):
    score = 0.0
    st = init_stat()

    # prefix + primary
    for eff in (r.get("prefix_eff"), r.get("pri_eff")):
        if isinstance(eff, list) and len(eff) >= 2 and eff[0] != 0:
            v, add = eff_score(int(eff[0]), float(eff[1]), ch_base, stat_coef=stat_coef)
            score += v
            st = add_stat(st, add)

    # secondary (incl grind)
    for row in r.get("sec_eff", []):
        if not row or row[0] == 0:
            continue
        base = float(row[1]) if len(row) > 1 else 0.0
        grind = float(row[3]) if len(row) > 3 else 0.0
        v, add = eff_score(int(row[0]), base + grind, ch_base, stat_coef=stat_coef)
        score += v
        st = add_stat(st, add)

    return score, st


# ---------- Set effects ----------


def set_effect(set_id, ch_base, set_fixed_override=None):
    """
    Set effects are also BASE-based.
    stat effects:
      - v < 1.0 => percent of base stat
      - v >= 1.0 => flat stat
    fixed effects:
      - contributes to fixed score directly
    """
    cfg = SET_EFFECTS.get(int(set_id))
    if not cfg:
        return 0, init_stat(), 0.0

    need = int(cfg["need"])
    if set_fixed_override and int(set_id) in set_fixed_override:
        fixedB = float(set_fixed_override[int(set_id)])
    else:
        fixedB = float(cfg.get("fixed", 0.0))

    statB = init_stat()
    for stat_key, v in cfg.get("stat", {}).items():
        v = float(v)
        if 0.0 < v < 1.0:
            statB[stat_key] = ch_base[stat_key] * v
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

        score += (value / max_val) * 25.0

    return score


def artifact_score_total(art):
    score = 0.0
    if art.get("pri_effect"):
        score += 120.0
    score += artifact_sub_score_only(art)
    return score


# ---------- Skill-up ----------


def skillup_score(u, skillup_coef_override=None):
    total = 0
    for row in u.get("skills", []):
        if isinstance(row, list) and len(row) >= 2:
            total += max(0, int(row[1]) - 1)
    coef = SKILLUP_COEF if skillup_coef_override is None else skillup_coef_override
    return total * coef


# ---------- Current unit total ----------


def score_unit_total(u, stat_coef=None, set_fixed=None, skillup_coef=None):
    runes = u.get("runes", [])
    if not isinstance(runes, list) or not runes:
        return None

    # 1) Base stats (pure base)
    ch = unit_base_char(u)

    # 2) Flag bonus (base-based delta; added at the end)
    flag_delta = flag_bonus_delta(ch)
    flag_bonus_score = stat_struct_score(flag_delta, stat_coef=stat_coef)

    # 3) Rune scores (base-based)
    rune_stat_sum = init_stat()
    base_scores = []
    for r in runes:
        s, add = rune_stat_score(r, ch, stat_coef=stat_coef)
        base_scores.append(s)
        rune_stat_sum = add_stat(rune_stat_sum, add)

    # 4) Set effects (base-based)
    set_ids = [int(r.get("set_id", 0)) for r in runes]
    cnt = defaultdict(int)
    for sid in set_ids:
        cnt[sid] += 1

    stat_bonus = init_stat()
    fixed_score = 0.0
    for sid, c in cnt.items():
        need, statB, fixedB = set_effect(sid, ch, set_fixed_override=set_fixed)
        if need > 0:
            times = c // need
            # preserve your original rule: 4-set effects apply at most once
            if need >= 4:
                times = min(times, 1)
            for _ in range(times):
                stat_bonus = add_stat(stat_bonus, statB)
                fixed_score += fixedB

    # 5) Score components
    base_stat_score = stat_struct_score(ch, stat_coef=stat_coef)               # pure base
    stat_bonus_score = stat_struct_score(stat_bonus, stat_coef=stat_coef)      # set stat bonus only
    rune_score_sum = sum(base_scores)                     # rune score only
    su_score = skillup_score(u, skillup_coef_override=skillup_coef)                           # skill-up only

    # Display/debug: total added stats (runes + set stats + flag delta)
    total_add_stat = add_stat(add_stat(rune_stat_sum, stat_bonus), flag_delta)

    # NOTE: artifact_score_sum is currently excluded from total_score (per your code)
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

    # 6) Final total score (as you specified)
    # final = base + flag_bonus(base) + rune(base) + set_stat(base) + set_fixed + skillup
    total_score = (
        base_stat_score
        + flag_bonus_score
        + rune_score_sum
        + stat_bonus_score
        + fixed_score
        + su_score
    )

    print(
        "DEBUG score_unit_total called, "
        "flag_bonus_score=", flag_bonus_score,
        "stat_bonus_score=", stat_bonus_score,
        "fixed_score=", fixed_score,
        "cnt=", dict(cnt),
    )

    return {
        "unit_id": int(u.get("unit_id", 0)),
        "unit_master_id": int(u.get("unit_master_id", 0)),
        "char": ch,  # pure base
        "flag_delta": flag_delta,
        "flag_bonus_score": flag_bonus_score,
        "total_add_stat": total_add_stat,
        "base_stat_score": base_stat_score,
        "rune_score_sum": rune_score_sum,
        "stat_bonus_score": stat_bonus_score,
        "fixed_score": fixed_score,
        "artifact_score": artifact_score_sum,
        "artifact_sub_l": art_sub_l,
        "artifact_sub_r": art_sub_r,
        "skillup_score": su_score,
        "total_score": total_score,
    }
