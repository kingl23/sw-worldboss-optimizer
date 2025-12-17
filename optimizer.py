# optimizer.py
from itertools import product
from collections import defaultdict

from core_scores import (rune_stat_score, set_effect, unit_base_char,
                         init_stat, add_stat, stat_struct_score)


def optimize_unit_best_runes(data, target_master_id, k):
    # Find target unit
    units = [
        u for u in data.get("unit_list", [])
        if int(u.get("unit_master_id", -1)) == int(target_master_id)
    ]
    if not units:
        return None, None, [], [], []

    u = units[0]
    ch = unit_base_char(u)

    # +15 runes only
    runes = [
        r for r in data.get("runes", []) if int(r.get("upgrade_curr", 0)) == 15
    ]

    # Base rune scores
    base_score = []
    for r in runes:
        s, _ = rune_stat_score(r, ch)
        base_score.append(s)

    # Group runes by slot
    slot_idx = {i: [] for i in range(1, 7)}
    for i, r in enumerate(runes):
        slot_idx[int(r.get("slot_no", 0))].append(i)

    best_score = -1e18
    best_pick = None

    # Exact enumeration (pruned by k)
    for pick in product(*(slot_idx[i][:k] for i in range(1, 7))):
        score = sum(base_score[i] for i in pick)

        # Set counting
        cnt = defaultdict(int)
        for i in pick:
            cnt[int(runes[i].get("set_id", 0))] += 1

        statB = init_stat()
        fixed = 0.0
        for sid, c in cnt.items():
            need, sb, fb = set_effect(sid, ch)
            if c >= need:
                statB = add_stat(statB, sb)
                fixed += fb

        score += stat_struct_score(statB) + fixed

        if score > best_score:
            best_score = score
            best_pick = pick

    if best_pick is None:
        return None, None, [], [], []

    return u, ch, runes, list(best_pick), base_score
