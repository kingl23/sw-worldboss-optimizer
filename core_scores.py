# core_scores.py
import math
from collections import defaultdict
from config import SKILLUP_COEF

# ---------- Basic utils ----------


def ceil(x):
    return int(math.ceil(x))


def init_stat():
    return {
        "HP": 0.0,
        "ATK": 0.0,
        "DEF": 0.0,
        "SPD": 0.0,
        "CR": 0.0,
        "CD": 0.0,
        "RES": 0.0,
        "ACC": 0.0
    }


def add_stat(a, b):
    return {k: a[k] + b[k] for k in a}


def stat_struct_score(st):
    return (st["HP"] * 0.08 + st["ATK"] * 1.2 + st["DEF"] * 1.2 +
            st["SPD"] * 7.99 + st["CR"] * 8.67 + st["CD"] * 6.32 +
            st["RES"] * 7.85 + st["ACC"] * 7.85)


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
    add = init_stat()
    coef = 0.0
    real = 0.0

    if typ == 1:
        real = val
        add["HP"] = real
        coef = 0.08
    elif typ == 2:
        real = ch["HP"] * val / 100
        add["HP"] = real
        coef = 0.08
    elif typ == 3:
        real = val
        add["ATK"] = real
        coef = 1.2
    elif typ == 4:
        real = ch["ATK"] * val / 100
        add["ATK"] = real
        coef = 1.2
    elif typ == 5:
        real = val
        add["DEF"] = real
        coef = 1.2
    elif typ == 6:
        real = ch["DEF"] * val / 100
        add["DEF"] = real
        coef = 1.2
    elif typ == 8:
        real = val
        add["SPD"] = real
        coef = 7.99
    elif typ == 9:
        real = val
        add["CR"] = real
        coef = 8.67
    elif typ == 10:
        real = val
        add["CD"] = real
        coef = 6.32
    elif typ == 11:
        real = val
        add["RES"] = real
        coef = 7.85
    elif typ == 12:
        real = val
        add["ACC"] = real
        coef = 7.85

    return real * coef, add


def rune_stat_score(r, ch):
    score = 0.0
    st = init_stat()

    for eff in (r.get("prefix_eff"), r.get("pri_eff")):
        if isinstance(eff, list) and len(eff) >= 2 and eff[0] != 0:
            v, add = eff_score(int(eff[0]), float(eff[1]), ch)
            score += v
            st = add_stat(st, add)

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
    statB = init_stat()
    fixedB = 0.0
    need = 4

    if set_id == 1:
        need = 2
        statB["HP"] = ch["HP"] * 0.15
    elif set_id == 2:
        need = 2
        statB["DEF"] = ch["DEF"] * 0.15
    elif set_id == 3:
        need = 4
        statB["SPD"] = ch["SPD"] * 0.25
    elif set_id == 4:
        need = 2
        statB["CR"] = 12
    elif set_id == 5:
        need = 4
        statB["CD"] = 40
    elif set_id == 6:
        need = 2
        statB["ACC"] = 20
    elif set_id == 7:
        need = 2
        statB["RES"] = 20
    elif set_id == 8:
        need = 4
        statB["ATK"] = ch["ATK"] * 0.35
    elif set_id == 10:
        need = 4
        fixedB = 299
    elif set_id == 11:
        need = 4
        fixedB = 291
    elif set_id == 13:
        need = 4
        fixedB = 296
    elif set_id == 14:
        need = 2
        fixedB = 124
    elif set_id == 15:
        need = 2
        fixedB = 123
    elif set_id == 16:
        need = 2
        fixedB = 124
    elif set_id == 17:
        need = 2
        fixedB = 123
    elif set_id == 18:
        need = 2
        fixedB = 125

    need = int(need)
    return need, statB, fixedB


# ---------- Artifact ----------


def artifact_sub_score_only(art):
    score = 0.0
    for row in art.get("sec_effects", []):
        if len(row) >= 2:
            score += (row[1] / 6.0) * 25.0
    return 0 # score


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

    total_score = (base_stat_score + sum(base_scores) + stat_bonus_score +
                   fixed_score + artifact_score_sum + su_score)


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
