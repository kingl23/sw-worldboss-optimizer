# visualize.py
from collections import defaultdict

from config import SET_NAME, EFF_NAME
from core_scores import (rune_stat_score, init_stat, add_stat,
                         stat_struct_score, ceil, set_effect)

# ============================================================
# Internal builders (string only, no printing)
# ============================================================


def _build_optimizer_lines(u, ch, runes, picked, base_score):
    lines = []

    # Set effects
    set_ids = [int(runes[i].get("set_id", 0)) for i in picked]
    cnt = defaultdict(int)
    for sid in set_ids:
        cnt[sid] += 1

    stat_bonus = init_stat()
    fixed_score = 0.0
    for sid, c in cnt.items():
        need, sb, fb = set_effect(sid, ch)
        if c >= need:
            stat_bonus = add_stat(stat_bonus, sb)
            fixed_score += fb

    stat_bonus_score = stat_struct_score(stat_bonus)
    total_score = (sum(base_score[i]
                       for i in picked) + stat_bonus_score + fixed_score)

    lines.append("")
    lines.append("=== Best Rune Set (World Boss) ===")

    rune_stat_sum = init_stat()
    picked_sorted = sorted(picked,
                           key=lambda i: int(runes[i].get("slot_no", 0)))

    # Per-slot details
    for idx in picked_sorted:
        r = runes[idx]
        _, st = rune_stat_score(r, ch)
        rune_stat_sum = add_stat(rune_stat_sum, st)

        slot = int(r.get("slot_no", 0))
        set_id = int(r.get("set_id", 0))
        rune_id = int(r.get("rune_id", 0))

        lines.append("")
        lines.append(f"[Slot {slot}] {SET_NAME.get(set_id, set_id)} "
                     f"(Rune ID: {rune_id})")

        pri = r.get("pri_eff", [])
        if isinstance(pri, list) and len(pri) >= 2:
            lines.append(
                f"  Main : {EFF_NAME.get(int(pri[0]), pri[0])} {int(pri[1])}")

        for row in r.get("sec_eff", []):
            if not row or row[0] == 0:
                continue
            typ = int(row[0])
            base = int(row[1]) if len(row) > 1 else 0
            grind = int(row[3]) if len(row) > 3 else 0
            lines.append(f"  Sub  : {EFF_NAME.get(typ, typ)} {base + grind}")

    # Final stat summary
    total_add_stat = add_stat(rune_stat_sum, stat_bonus)

    lines.append("")
    lines.append("=== Final Stat Summary ===")

    for k in ["HP", "ATK", "DEF", "SPD", "CR", "CD", "RES", "ACC"]:
        lines.append(f"{k:3}: {ceil(ch[k])} + {ceil(total_add_stat[k])} "
                     f"= {ceil(ch[k] + total_add_stat[k])}")

    # lines.append(f"Stat-set bonus score : {stat_bonus_score:.1f}")
    # lines.append(f"Fixed set score      : {fixed_score:.1f}")
    # lines.append(f"TOTAL SCORE          : {total_score:.1f}")
    lines.append(f"Stat-set bonus score : {final_score['stat_bonus_score']:.1f}")
    lines.append(f"Fixed set score      : {final_score['fixed_score']:.1f}")
    lines.append(f"TOTAL SCORE          : {final_score['total_score']:.1f}")

    return lines


def _build_ranking_lines(results, top_n=60):
    lines = []
    n = min(top_n, len(results))

    lines.append("")
    lines.append(f"Showing Top {n} units by TOTAL SCORE")
    lines.append("")

    for i in range(n):
        r = results[i]
        ch = r["char"]
        add = r["total_add_stat"]

        lines.append(
            f"=== #{i+1} Unit "
            f"(unit_id: {r['unit_id']}, master_id: {r['unit_master_id']}) ===")

        for k in ["HP", "ATK", "DEF", "SPD", "CR", "CD", "RES", "ACC"]:
            lines.append(f"{k:3}: {ceil(ch[k])} + {ceil(add[k])} "
                         f"= {ceil(ch[k] + add[k])}")

        lines.append(f"Base stat score      : {r['base_stat_score']:.1f}")
        lines.append(f"Stat-set bonus score : {r['stat_bonus_score']:.1f}")
        lines.append(f"Fixed set score      : {r['fixed_score']:.1f}")
        lines.append(f"Skill-up score       : {r['skillup_score']:.1f}")
        lines.append(f"Artifact score (sub) : "
                     f"{r['artifact_sub_l']:.0f} / {r['artifact_sub_r']:.0f}")
        lines.append(f"TOTAL SCORE          : {r['total_score']:.1f}")
        lines.append("")

    return lines


# ============================================================
# Public APIs
# ============================================================

# --- Optimizer ---


def print_unit_optimizer_result(u, ch, runes, picked, base_score):
    lines = _build_optimizer_lines(u, ch, runes, picked, base_score)
    print("\n".join(lines))


# def render_optimizer_result(u, ch, runes, picked, base_score):
def render_optimizer_result(u, ch, runes, picked, base_score, final_score=None):
    lines = _build_optimizer_lines(u, ch, runes, picked, base_score)
    return "\n".join(lines)


# --- Ranking ---


def print_top_units(results, top_n=60):
    lines = _build_ranking_lines(results, top_n)
    print("\n".join(lines))


def render_ranking_result(results, top_n=60):
    lines = _build_ranking_lines(results, top_n)
    return "\n".join(lines)
