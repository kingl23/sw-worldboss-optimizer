import copy
from core_scores import score_unit_total, rune_stat_score, unit_base_char
from optimizer import optimize_unit_best_runes, optimize_unit_best_runes_by_unit_id
from ranking import rank_all_units
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


def build_wb_ranking(working_data, top_n: int = 60):
    return rank_all_units(working_data, top_n=top_n)


def build_optimizer_context(working_data, unit_id: int):
    u = get_unit_by_unit_id(working_data, unit_id)
    if u is None:
        return None

    # BEFORE
    ch0, runes0, picked0, base0 = render_current_build(u)
    before = score_unit_total(u)

    # AFTER
    u1, ch1, runes1, picked1, base1 = optimize_unit_best_runes_by_unit_id(
        working_data, unit_id, K_PER_SLOT
    )

    rec_runes = None
    after = None
    if u1 is not None:
        rec_runes = [runes1[i] for i in picked1]
        u_tmp = copy.deepcopy(u)
        u_tmp["runes"] = rec_runes
        after = score_unit_total(u_tmp)

    return {
        "unit": u,
        "before": before,
        "before_state": {
            "unit": u,
            "char": ch0,
            "runes": runes0,
            "picked": picked0,
            "base": base0,
        },
        "after_state": {
            "unit": u1,
            "char": ch1,
            "runes": runes1,
            "picked": picked1,
            "base": base1,
        },
        "after": after,
        "rec_runes": rec_runes,
    }


def run_manual_optimizer(working_data, unit_master_id: int, k_per_slot: int = K_PER_SLOT):
    u, ch, runes, picked, base = optimize_unit_best_runes(
        working_data, int(unit_master_id), k_per_slot
    )
    final_score = score_unit_total(u)
    return {
        "unit": u,
        "char": ch,
        "runes": runes,
        "picked": picked,
        "base": base,
        "final_score": final_score,
    }


def run_optimizer_for_unit(working_data, unit_id):
    ctx = build_optimizer_context(working_data, unit_id)
    if ctx is None:
        return None

    before = ctx.get("before")
    before_score = before["total_score"] if before else None
    before_state = ctx.get("before_state", {})

    before_text = render_optimizer_result(
        before_state.get("unit"),
        before_state.get("char"),
        before_state.get("runes"),
        before_state.get("picked"),
        before_state.get("base"),
        final_score=before,
    )

    after_state = ctx.get("after_state", {})
    after = ctx.get("after")
    if after_state.get("unit") is None:
        return {
            "before_text": before_text,
            "after_text": "Optimizer: no result.",
            "before_score": before_score,
            "after_score": None,
            "rec_runes": None,
        }

    after_score = after["total_score"] if after else None
    after_text = render_optimizer_result(
        after_state.get("unit"),
        after_state.get("char"),
        after_state.get("runes"),
        after_state.get("picked"),
        after_state.get("base"),
        final_score=after,
    )

    return {
        "before_text": before_text,
        "after_text": after_text,
        "before_score": before_score,
        "after_score": after_score,
        "rec_runes": ctx.get("rec_runes"),
    }
