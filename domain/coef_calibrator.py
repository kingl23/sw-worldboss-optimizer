import math
import random
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple


@dataclass(frozen=True)
class CalibItem:
    unit_id: int
    true_rank: int
    stats: Dict[str, float]
    fixed_counts: Dict[int, int]
    skillup_count: int


def _clamp(val: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, val))


def _make_bounds(values: Sequence[float], ratio: float = 0.10) -> List[Tuple[float, float]]:
    bounds = []
    for v in values:
        span = abs(v) * ratio
        lo = v - span
        hi = v + span
        if span == 0:
            lo = hi = v
        bounds.append((lo, hi))
    return bounds


def _predicted_ranks(
    scores: Sequence[float],
    unit_ids: Sequence[int],
) -> Dict[int, int]:
    pairs = list(zip(unit_ids, scores))
    pairs_sorted = sorted(pairs, key=lambda x: (-x[1], x[0]))
    return {unit_id: rank + 1 for rank, (unit_id, _) in enumerate(pairs_sorted)}


def _footrule_loss(
    pred_rank_map: Dict[int, int],
    unit_ids: Sequence[int],
    true_ranks: Sequence[int],
) -> Tuple[float, float]:
    loss = 0
    exact = 0
    total = len(unit_ids)
    for unit_id, true_rank in zip(unit_ids, true_ranks):
        pred_rank = pred_rank_map[unit_id]
        loss += abs(pred_rank - true_rank)
        if pred_rank == true_rank:
            exact += 1
    exact_match_rate = exact / total if total else 0.0
    return float(loss), exact_match_rate


def _score_items(
    items: Sequence[CalibItem],
    stat_keys: Sequence[str],
    fixed_ids: Sequence[int],
    params: Sequence[float],
) -> List[float]:
    stat_n = len(stat_keys)
    fixed_n = len(fixed_ids)
    stat_coef = params[:stat_n]
    fixed_coef = params[stat_n:stat_n + fixed_n]
    skillup_coef = params[-1]

    scores = []
    for item in items:
        score = 0.0
        for idx, key in enumerate(stat_keys):
            score += item.stats.get(key, 0.0) * stat_coef[idx]
        for idx, sid in enumerate(fixed_ids):
            score += item.fixed_counts.get(sid, 0) * fixed_coef[idx]
        score += item.skillup_count * skillup_coef
        scores.append(score)
    return scores


def _objective(
    items: Sequence[CalibItem],
    stat_keys: Sequence[str],
    fixed_ids: Sequence[int],
    params: Sequence[float],
    base_params: Sequence[float],
    lambdas: Tuple[float, float, float],
) -> Tuple[float, float, float]:
    scores = _score_items(items, stat_keys, fixed_ids, params)
    unit_ids = [item.unit_id for item in items]
    true_ranks = [item.true_rank for item in items]
    pred_rank_map = _predicted_ranks(scores, unit_ids)
    rank_loss, exact_match_rate = _footrule_loss(pred_rank_map, unit_ids, true_ranks)

    stat_n = len(stat_keys)
    fixed_n = len(fixed_ids)
    stat_lambda, fixed_lambda, skill_lambda = lambdas

    reg_stat = 0.0
    reg_fixed = 0.0
    for i in range(stat_n):
        delta = params[i] - base_params[i]
        reg_stat += delta * delta
    for i in range(fixed_n):
        idx = stat_n + i
        delta = params[idx] - base_params[idx]
        reg_fixed += delta * delta
    delta = params[-1] - base_params[-1]
    reg_skill = delta * delta

    reg = stat_lambda * reg_stat + fixed_lambda * reg_fixed + skill_lambda * reg_skill
    return rank_loss + reg, rank_loss, exact_match_rate


def calibrate_rank60(
    items: Sequence[CalibItem],
    stat_keys: Sequence[str],
    fixed_ids: Sequence[int],
    init_stat_coef: Dict[str, float],
    init_fixed_map: Dict[int, float],
    init_skillup_coef: float,
    iterations: int = 3000,
    seed: int = 7,
    step0: float = 1.0,
    lambdas: Tuple[float, float, float] = (1e-4, 1e-4, 1e-4),
    initial_params: Sequence[float] | None = None,
) -> Dict[str, object]:
    stat_keys = list(stat_keys)
    fixed_ids = list(fixed_ids)

    base_params = [init_stat_coef[k] for k in stat_keys]
    base_params += [init_fixed_map[sid] for sid in fixed_ids]
    base_params.append(init_skillup_coef)

    bounds = _make_bounds(base_params)

    rng = random.Random(seed)
    start_params = list(initial_params) if initial_params is not None else list(base_params)
    base_obj, base_rank_loss, base_exact = _objective(
        items, stat_keys, fixed_ids, base_params, base_params, lambdas
    )
    if base_rank_loss == 0:
        stat_n = len(stat_keys)
        fixed_n = len(fixed_ids)
        tuned_stat = {
            key: float(base_params[i]) for i, key in enumerate(stat_keys)
        }
        tuned_fixed = {
            int(sid): float(base_params[stat_n + i]) for i, sid in enumerate(fixed_ids)
        }
        tuned_skill = float(base_params[-1])

        return {
            "STAT_COEF": tuned_stat,
            "SET_FIXED": tuned_fixed,
            "SKILLUP_COEF": tuned_skill,
            "summary": {
                "objective": float(base_obj),
                "rank_loss": float(base_rank_loss),
                "exact_match_rate": float(base_exact),
                "iterations": int(iterations),
            },
        }

    best_params = list(start_params)
    best_obj, best_rank, best_exact = _objective(
        items, stat_keys, fixed_ids, best_params, base_params, lambdas
    )

    current_params = list(start_params)
    current_obj = best_obj

    t0 = 1.0
    tmin = 1e-3
    jump_prob = 0.02

    for t in range(int(iterations)):
        decay = 0.1 + 0.9 * (1.0 - (t / max(1, iterations)))
        step = step0 * decay
        if rng.random() < jump_prob:
            candidate = [rng.uniform(lo, hi) for lo, hi in bounds]
        else:
            idx = rng.randrange(len(current_params))
            direction = -1.0 if rng.random() < 0.5 else 1.0

            candidate = list(current_params)
            lo, hi = bounds[idx]
            candidate[idx] = _clamp(candidate[idx] + direction * step, lo, hi)

        cand_obj, cand_rank, cand_exact = _objective(
            items, stat_keys, fixed_ids, candidate, base_params, lambdas
        )

        temperature = max(tmin, t0 * (0.01 ** (t / max(1, iterations))))
        delta = cand_obj - current_obj

        if delta <= 0:
            current_params = candidate
            current_obj = cand_obj
        else:
            accept_prob = math.exp(-delta / temperature)
            if rng.random() < accept_prob:
                current_params = candidate
                current_obj = cand_obj

        if cand_obj < best_obj:
            best_params = candidate
            best_obj = cand_obj
            best_rank = cand_rank
            best_exact = cand_exact

    stat_n = len(stat_keys)
    fixed_n = len(fixed_ids)
    tuned_stat = {
        key: float(best_params[i]) for i, key in enumerate(stat_keys)
    }
    tuned_fixed = {
        int(sid): float(best_params[stat_n + i]) for i, sid in enumerate(fixed_ids)
    }
    tuned_skill = float(best_params[-1])

    return {
        "STAT_COEF": tuned_stat,
        "SET_FIXED": tuned_fixed,
        "SKILLUP_COEF": tuned_skill,
        "summary": {
            "objective": float(best_obj),
            "rank_loss": float(best_rank),
            "exact_match_rate": float(best_exact),
            "iterations": int(iterations),
        },
    }


def calibrate_rank60_multistart(
    items: Sequence[CalibItem],
    stat_keys: Sequence[str],
    fixed_ids: Sequence[int],
    init_stat_coef: Dict[str, float],
    init_fixed_map: Dict[int, float],
    init_skillup_coef: float,
    iterations: int = 3000,
    seed: int = 7,
    step0: float = 1.0,
    lambdas: Tuple[float, float, float] = (1e-4, 1e-4, 1e-4),
    restarts: int = 5,
) -> Dict[str, object]:
    stat_keys = list(stat_keys)
    fixed_ids = list(fixed_ids)

    base_params = [init_stat_coef[k] for k in stat_keys]
    base_params += [init_fixed_map[sid] for sid in fixed_ids]
    base_params.append(init_skillup_coef)
    bounds = _make_bounds(base_params)

    best_result = None
    best_obj = None
    for k in range(int(restarts)):
        run_seed = seed + k
        if k == 0:
            start_params = None
        else:
            rng = random.Random(run_seed)
            start_params = [rng.uniform(lo, hi) for lo, hi in bounds]

        result = calibrate_rank60(
            items=items,
            stat_keys=stat_keys,
            fixed_ids=fixed_ids,
            init_stat_coef=init_stat_coef,
            init_fixed_map=init_fixed_map,
            init_skillup_coef=init_skillup_coef,
            iterations=iterations,
            seed=run_seed,
            step0=step0,
            lambdas=lambdas,
            initial_params=start_params,
        )

        obj = float(result["summary"]["objective"])
        if best_result is None or obj < best_obj:
            best_result = result
            best_obj = obj

    return best_result


def build_calib_items(
    items: Iterable[Dict[str, object]],
    stat_keys: Sequence[str],
) -> List[CalibItem]:
    out = []
    for row in items:
        stats = {k: float(row.get("stats", {}).get(k, 0.0)) for k in stat_keys}
        fixed_counts = {
            int(k): int(v) for k, v in (row.get("fixed_counts", {}) or {}).items()
        }
        out.append(
            CalibItem(
                unit_id=int(row.get("unit_id", 0)),
                true_rank=int(row.get("true_rank", 0)),
                stats=stats,
                fixed_counts=fixed_counts,
                skillup_count=int(row.get("skillup_count", 0)),
            )
        )
    return out
