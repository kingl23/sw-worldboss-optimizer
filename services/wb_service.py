import copy
from core_scores import score_unit_total, rune_stat_score, unit_base_char
from optimizer import optimize_unit_best_runes_by_unit_id
from visualize import render_optimizer_result
from config import K_PER_SLOT
from domain.unit_repo import get_unit_by_unit_id


def render_current_build(u):
    ch = unit_base_char(u)
    runes = sorted(
        (u.get("runes", []) or []),
        key=lambda r: int(r.get("slot_no", 0)),
    )
    base_score = []
    for r in runes:
        s, _ = rune_stat_score(r, ch)
        base_score.append(s)
    picked = list(range(len(runes)))
    return ch, runes, picked, base_score


def run_optimizer_for_unit(working_data, unit_id):
    u = get_unit_by_unit_id(working_data, unit_id)
    if u is None:
        return None

    # BEFORE
    ch0, runes0, picked0, base0 = render_current_build(u)
    before = score_unit_total(u)
    before_score = before["total_score"] if before else None
    before_text = render_optimizer_result(
        u, ch0, runes0, picked0, base0, final_score=before
    )

    # AFTER
    u1, ch1, runes1, picked1, base1 = optimize_unit_best_runes_by_unit_id(
        working_data, unit_id, K_PER_SLOT
    )

    if u1 is None:
        return {
            "before_text": before_text,
            "after_text": "Optimizer: no result.",
            "before_score": before_score,
            "after_score": None,
            "rec_runes": None,
        }

    rec_runes = [runes1[i] for i in picked1]
    u_tmp = copy.deepcopy(u)
    u_tmp["runes"] = rec_runes
    after = score_unit_total(u_tmp)
    after_score = after["total_score"] if after else None
    after_text = render_optimizer_result(
        u1, ch1, runes1, picked1, base1, final_score=after
    )

    return {
        "before_text": before_text,
        "after_text": after_text,
        "before_score": before_score,
        "after_score": after_score,
        "rec_runes": rec_runes,
    }
