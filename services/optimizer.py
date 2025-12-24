from itertools import product
from collections import defaultdict

from domain.scores import (
    rune_stat_score,
    set_effect,
    unit_base_char,
    init_stat,
    add_stat,
    stat_struct_score,
)


def _dedupe_runes_by_id(runes):
    """Keep first occurrence of each rune_id (safety for mixed sources)."""
    seen = set()
    out = []
    for r in runes or []:
        rid = r.get("rune_id")
        if rid is None:
            out.append(r)
            continue
        if rid in seen:
            continue
        seen.add(rid)
        out.append(r)
    return out


def _optimize_with_runes(u, runes, k):
    """Core optimizer (same algorithm as before)."""
    ch = unit_base_char(u)

    base_score = []
    for r in runes:
        s, _ = rune_stat_score(r, ch)
        base_score.append(s)

    slot_idx = {i: [] for i in range(1, 7)}
    for i, r in enumerate(runes):
        slot_idx[int(r.get("slot_no", 0))].append(i)

    best_score = -1e18
    best_pick = None

    for pick in product(*(slot_idx[i][:k] for i in range(1, 7))):
        score = sum(base_score[i] for i in pick)

        cnt = defaultdict(int)
        for i in pick:
            cnt[int(runes[i].get("set_id", 0))] += 1

        statB = init_stat()
        fixed = 0.0
        for sid, c in cnt.items():
            need, sb, fb = set_effect(sid, ch)
            if need > 0:
                times = c // need
                if need >= 4:
                    times = min(times, 1)           
                for _ in range(times):
                    statB = add_stat(statB, sb)
                    fixed += fb

        score += stat_struct_score(statB) + fixed

        if score > best_score:
            best_score = score
            best_pick = pick

    if best_pick is None:
        return None, None, [], [], []

    return u, ch, runes, list(best_pick), base_score


def optimize_unit_best_runes(data, target_master_id, k):
    """Optimize by master_id using +15 runes in storage."""
    units = [
        u
        for u in data.get("unit_list", [])
        if int(u.get("unit_master_id", -1)) == int(target_master_id)
    ]
    if not units:
        return None, None, [], [], []

    u = units[0]

    runes = [r for r in data.get("runes", []) if int(r.get("upgrade_curr", 0)) == 15]

    return _optimize_with_runes(u, runes, k)


def optimize_unit_best_runes_by_unit_id(data, target_unit_id, k):
    """Optimize by unit_id using equipped and +15 storage runes."""
    units = [
        u
        for u in data.get("unit_list", [])
        if int(u.get("unit_id", -1)) == int(target_unit_id)
    ]
    if not units:
        return None, None, [], [], []

    u = units[0]

    equipped = u.get("runes", []) or []
    storage = data.get("runes", []) or []

    pool = _dedupe_runes_by_id(list(equipped) + list(storage))
    runes = [r for r in pool if int(r.get("upgrade_curr", 0)) == 15]

    return _optimize_with_runes(u, runes, k)
