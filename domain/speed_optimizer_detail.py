from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import time
from typing import Any, Dict, List, Optional, Tuple

from config.atb_simulator_presets import (
    TOWER_PERCENT,
    build_full_preset,
    get_leader_percent,
)
from domain.atb_simulator import simulate_with_turn_log
from domain.atb_simulator_utils import prefix_monsters

MAX_RUNE_SPEED = 250
MIN_RUNE_SPEED = 150
COARSE_STEP = 10
MAX_EFFECT = 50
DEFAULT_INPUT_3 = 0


@dataclass
class DetailTable:
    ranges: List[Dict[str, str]]


@dataclass(frozen=True)
class RequiredOrder:
    mode: str
    order: List[str]


@dataclass
class PresetDetailResult:
    preset_id: str
    a1_table: Optional[DetailTable]
    a2_table: Optional[DetailTable]
    a3_table: Optional[DetailTable]
    error: Optional[str] = None
    timing: Optional[Dict[str, float]] = None
    debug: Optional[Dict[str, Any]] = None
    calc_type: Optional[str] = None


@lru_cache(maxsize=128)
def build_section1_detail_cached(
    preset_id: str,
    input_1: Optional[int],
    input_2: Optional[int],
    input_3: Optional[int],
    max_runtime_s: Optional[float],
    debug: bool,
) -> PresetDetailResult:
    preset = build_full_preset(preset_id)
    if preset_id == "Preset B":
        return _build_preset_detail_type_b(
            preset_id,
            preset,
            input_1,
            input_2,
            input_3,
            max_runtime_s=max_runtime_s,
            debug=debug,
        )
    return _build_preset_detail_type_general(
        preset_id,
        preset,
        input_1,
        input_2,
        input_3,
        max_runtime_s=max_runtime_s,
        debug=debug,
    )


def _build_preset_detail_type_general(
    preset_id: str,
    preset: Dict[str, Any],
    input_1: Optional[int],
    input_2: Optional[int],
    input_3: Optional[int],
    max_runtime_s: Optional[float],
    debug: bool,
) -> PresetDetailResult:
    allies = preset.get("allies", [])
    enemies = preset.get("enemies", [])
    if len(allies) < 3 or len(enemies) < 2:
        return PresetDetailResult(
            preset_id=preset_id,
            a1_table=None,
            a2_table=None,
            a3_table=None,
            error="Preset must contain at least 3 allies and 2 enemies.",
            calc_type="general",
        )

    # Input 2 fixes a1's rune speed so only a3 is optimized.
    start_time = time.perf_counter()
    deadline = start_time + max_runtime_s if max_runtime_s else None

    prefixed_allies, _ = prefix_monsters(allies, prefix="A")
    prefixed_enemies, _ = prefix_monsters(enemies, prefix="E")
    prefixed_overrides, enemy_speed_source, enemy_speed_effective = _build_section1_overrides(
        preset_id,
        prefixed_allies,
        prefixed_enemies,
        input_1,
        input_2,
        input_3,
        allow_enemy_fallback=True,
    )
    debug_payload: Optional[Dict[str, Any]] = None
    if debug:
        debug_payload = {
            "input_summary": {
                "preset_id": preset_id,
                "input_1": input_1,
                "input_2": input_2,
                "input_3": input_3 if input_3 is not None else enemy_speed_effective,
                "enemy_rune_speed_source": enemy_speed_source,
                "enemy_rune_speed_effective": enemy_speed_effective,
                "calc_type": "general",
            },
            "attempts": [],
            # Debug mode stores only a limited number of attempts to avoid heavy memory use.
            "attempt_limit": 25,
            "truncated": False,
            "min_rune_speed": MIN_RUNE_SPEED,
            "max_rune_speed": MAX_RUNE_SPEED,
            "effect_logs": [],
        }
    if debug_payload is not None:
        debug_payload["calc_type"] = "general"
        debug_payload["input_summary"]["selected_enemy_key"] = "E_MIRROR"

    enemy_mirror = _build_enemy_mirror(
        preset_id,
        prefixed_allies,
        prefixed_overrides,
        input_3,
    )
    detail_preset, detail_keys = _build_detail_preset(
        preset,
        prefixed_allies,
        enemy_mirror,
    )
    required_order = _resolve_required_order(preset_id, detail_keys)
    if required_order is None:
        return PresetDetailResult(
            preset_id=preset_id,
            a1_table=None,
            a2_table=None,
            a3_table=None,
            error="Invalid required turn order mapping for this preset.",
            timing={},
            debug=debug_payload,
            calc_type="general",
        )

    if debug_payload is not None:
        debug_payload["required_order"] = {
            "mode": required_order.mode,
            "order": required_order.order,
        }
        debug_payload["unit_order"] = {
            "a2": detail_keys["a2"],
            "a1": detail_keys["a1"],
            "a3": detail_keys["a3"],
            "e": detail_keys["e_fast"],
        }
        debug_payload["selected_units"] = _build_debug_unit_summary(
            detail_preset,
            required_order,
            prefixed_overrides,
        )
        debug_payload["tick_limit"] = 30
        debug_snapshots: List[Dict[str, Any]] = []
        baseline_overrides = dict(prefixed_overrides)
        baseline_overrides[detail_keys["a3"]] = {
            "rune_speed": MIN_RUNE_SPEED,
            "speedIncreasingEffect": 0,
        }
        _, baseline_turn_events = simulate_with_turn_log(
            detail_preset,
            baseline_overrides,
            debug_snapshots=debug_snapshots,
            debug_ticks=debug_payload["tick_limit"],
            debug_keys=set(debug_payload["unit_order"].values()),
        )
        debug_payload["tick_snapshots"] = debug_snapshots
        debug_payload["baseline_turn_events"] = baseline_turn_events

    a3_start = time.perf_counter()
    a3_table, a3_error = _build_unit_detail_table(
        detail_preset,
        required_order,
        prefixed_overrides,
        target_key=detail_keys["a3"],
        deadline=deadline,
        debug=debug_payload,
    )
    a3_time = time.perf_counter() - a3_start

    error_messages = [msg for msg in [a3_error] if msg]
    combined_error = "\n".join(error_messages) if error_messages else None

    return PresetDetailResult(
        preset_id=preset_id,
        a1_table=None,
        a2_table=None,
        a3_table=a3_table,
        error=combined_error,
        timing={
            "a3_s": a3_time,
        },
        debug=debug_payload,
        calc_type="general",
    )


def _build_preset_detail_type_b(
    preset_id: str,
    preset: Dict[str, Any],
    input_1: Optional[int],
    input_2: Optional[int],
    input_3: Optional[int],
    max_runtime_s: Optional[float],
    debug: bool,
) -> PresetDetailResult:
    allies = preset.get("allies", [])
    enemies = preset.get("enemies", [])
    if len(allies) < 3 or len(enemies) < 2:
        return PresetDetailResult(
            preset_id=preset_id,
            a1_table=None,
            a2_table=None,
            a3_table=None,
            error="Preset must contain at least 3 allies and 2 enemies.",
            calc_type="special_b",
        )

    start_time = time.perf_counter()
    deadline = start_time + max_runtime_s if max_runtime_s else None

    prefixed_allies, _ = prefix_monsters(allies, prefix="A")
    prefixed_enemies, _ = prefix_monsters(enemies, prefix="E")
    prefixed_overrides, enemy_speed_source, enemy_speed_effective = _build_section1_overrides(
        preset_id,
        prefixed_allies,
        prefixed_enemies,
        input_1,
        input_2,
        input_3,
        allow_enemy_fallback=False,
    )
    debug_payload: Optional[Dict[str, Any]] = None
    if debug:
        debug_payload = {
            "input_summary": {
                "preset_id": preset_id,
                "input_1": input_1,
                "input_2": input_2,
                "input_3": input_3,
                "enemy_rune_speed_source": enemy_speed_source,
                "enemy_rune_speed_effective": enemy_speed_effective,
                "calc_type": "special_b",
            },
            "attempts": [],
            "attempt_limit": 25,
            "truncated": False,
            "min_rune_speed": MIN_RUNE_SPEED,
            "max_rune_speed": MAX_RUNE_SPEED,
            "effect_logs": [],
        }

    enemy_mirror = _build_enemy_mirror(
        preset_id,
        prefixed_allies,
        prefixed_overrides,
        input_3,
    )
    detail_preset, detail_keys = _build_detail_preset(
        preset,
        prefixed_allies,
        enemy_mirror,
    )
    required_order = _resolve_required_order(preset_id, detail_keys)
    if required_order is None:
        return PresetDetailResult(
            preset_id=preset_id,
            a1_table=None,
            a2_table=None,
            a3_table=None,
            error="Invalid required turn order mapping for this preset.",
            timing={},
            debug=debug_payload,
            calc_type="special_b",
        )

    required_order_a1 = RequiredOrder(
        mode="strict",
        order=[detail_keys["a2"], detail_keys["a1"], detail_keys["e_fast"]],
    )
    a1_start = time.perf_counter()
    a1_min0 = _find_minimum_rune_speed(
        detail_preset,
        required_order_a1,
        prefixed_overrides,
        detail_keys["a1"],
        effect=0,
        start_speed=MIN_RUNE_SPEED,
        deadline=deadline,
        debug=debug_payload,
    )
    a1_time = time.perf_counter() - a1_start
    if debug_payload is not None:
        debug_payload["a1_min0"] = a1_min0

    if a1_min0 is None:
        return PresetDetailResult(
            preset_id=preset_id,
            a1_table=None,
            a2_table=None,
            a3_table=None,
            error="Unable to find minimum rune speed for a1 at effect 0.",
            timing={"a1_s": a1_time},
            debug=debug_payload,
            calc_type="special_b",
        )

    fixed_overrides = dict(prefixed_overrides)
    fixed_overrides[detail_keys["a1"]] = {
        "rune_speed": a1_min0,
        "speedIncreasingEffect": 0,
    }
    a3_start = time.perf_counter()
    a3_table, a3_error = _build_unit_detail_table(
        detail_preset,
        required_order,
        fixed_overrides,
        target_key=detail_keys["a3"],
        deadline=deadline,
        debug=debug_payload,
    )
    a3_time = time.perf_counter() - a3_start

    error_messages = [msg for msg in [a3_error] if msg]
    combined_error = "\n".join(error_messages) if error_messages else None

    return PresetDetailResult(
        preset_id=preset_id,
        a1_table=None,
        a2_table=None,
        a3_table=a3_table,
        error=combined_error,
        timing={
            "a1_s": a1_time,
            "a3_s": a3_time,
        },
        debug=debug_payload,
        calc_type="special_b",
    )


def _build_section1_overrides(
    preset_id: str,
    allies: List[Dict[str, Any]],
    enemies: List[Dict[str, Any]],
    input_1: Optional[int],
    input_2: Optional[int],
    input_3: Optional[int],
    allow_enemy_fallback: bool,
) -> Tuple[Dict[str, Dict[str, int]], str, int]:
    overrides: Dict[str, Dict[str, int]] = {}
    a1_key = allies[0].get("key")
    a2_key = allies[1].get("key")
    leader_percent = get_leader_percent(preset_id)
    if preset_id in {"Preset A", "Preset B", "Preset E"}:
        if input_2 is None:
            raise ValueError("input_2 is required for preset mapping.")
        if a2_key:
            overrides[a2_key] = {"rune_speed": input_2 + leader_percent + TOWER_PERCENT}
    elif preset_id in {"Preset C", "Preset D"}:
        if input_1 is None:
            raise ValueError("input_1 is required for preset mapping.")
        if a2_key:
            overrides[a2_key] = {"rune_speed": input_1}
    elif preset_id in {"Preset F", "Preset G"}:
        if input_1 is None:
            raise ValueError("input_1 is required for preset mapping.")
        if a1_key:
            overrides[a1_key] = {"rune_speed": input_1}

    resolved_enemy_speed = input_3 if input_3 is not None else DEFAULT_INPUT_3
    enemy_speed_source = "input_3" if input_3 is not None else "default"

    return overrides, enemy_speed_source, resolved_enemy_speed


def _resolve_required_order(
    preset_id: str,
    detail_keys: Dict[str, str],
) -> Optional[RequiredOrder]:
    if preset_id == "Preset A":
        order = [detail_keys.get("a2"), detail_keys.get("a3"), detail_keys.get("e_fast")]
        if any(key is None for key in order):
            return None
        return RequiredOrder(mode="a2_a3_e", order=order)
    if preset_id in {"Preset B", "Preset C", "Preset D", "Preset E"}:
        order = [
            detail_keys.get("a2"),
            detail_keys.get("a1"),
            detail_keys.get("a3"),
            detail_keys.get("e_fast"),
        ]
        if any(key is None for key in order):
            return None
        return RequiredOrder(mode="strict", order=order)
    if preset_id in {"Preset F", "Preset G"}:
        order = [
            detail_keys.get("a1"),
            detail_keys.get("a2"),
            detail_keys.get("a3"),
            detail_keys.get("e_fast"),
        ]
        if any(key is None for key in order):
            return None
        return RequiredOrder(mode="strict", order=order)
    return None


def _build_enemy_mirror(
    preset_id: str,
    prefixed_allies: List[Dict[str, Any]],
    overrides: Dict[str, Dict[str, int]],
    input_3: Optional[int],
) -> Dict[str, Any]:
    reference_index = 1 if preset_id in {"Preset A", "Preset B", "Preset C", "Preset D", "Preset E"} else 0
    reference = prefixed_allies[reference_index]
    reference_key = reference.get("key")
    reference_rune_speed = reference.get("rune_speed", 0)
    if reference_key and reference_key in overrides:
        reference_rune_speed = overrides[reference_key].get("rune_speed", reference_rune_speed)
    mirror = dict(reference)
    mirror["key"] = "E_MIRROR"
    mirror["name"] = f"E_{reference.get('name', 'mirror')}"
    mirror["isAlly"] = False
    mirror["rune_speed"] = reference_rune_speed + (input_3 or DEFAULT_INPUT_3)
    mirror["isSwift"] = False
    return mirror


def _build_detail_preset(
    preset: Dict[str, Any],
    prefixed_allies: List[Dict[str, Any]],
    enemy_mirror: Dict[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, str]]:
    a1 = prefixed_allies[0]
    a2 = prefixed_allies[1]
    a3 = prefixed_allies[2]
    e_fast = enemy_mirror

    detail_preset = {
        "allies": [a1, a2, a3],
        "enemies": [e_fast],
        "allyEffects": preset.get("allyEffects", {}),
        "enemyEffects": preset.get("enemyEffects", {}),
        "tickCount": preset.get("tickCount", 0),
    }
    detail_keys = {
        "a1": a1.get("key"),
        "a2": a2.get("key"),
        "a3": a3.get("key"),
        "e_fast": e_fast.get("key"),
    }
    return detail_preset, detail_keys


def _build_unit_detail_table(
    detail_preset: Dict[str, Any],
    required_order: RequiredOrder,
    base_overrides: Dict[str, Dict[str, int]],
    target_key: Optional[str],
    deadline: Optional[float],
    debug: Optional[Dict[str, Any]],
) -> Tuple[Optional[DetailTable], Optional[str]]:
    if not target_key:
        return None, "Target unit key was missing."

    effect_to_speed: Dict[int, Optional[int]] = {}
    start_speed = MIN_RUNE_SPEED
    for effect in range(0, MAX_EFFECT + 1):
        if deadline and time.perf_counter() > deadline:
            return None, "Computation timed out while searching rune speeds."
        minimum = _find_minimum_rune_speed(
            detail_preset,
            required_order,
            base_overrides,
            target_key,
            effect,
            start_speed,
            deadline,
            debug,
        )
        effect_to_speed[effect] = minimum
        if minimum is not None:
            start_speed = minimum

    if all(value is None for value in effect_to_speed.values()):
        return None, None

    return DetailTable(ranges=_summarize_effect_ranges(effect_to_speed)), None


def _find_minimum_rune_speed(
    detail_preset: Dict[str, Any],
    required_order: RequiredOrder,
    base_overrides: Dict[str, Dict[str, int]],
    target_key: str,
    effect: int,
    start_speed: int,
    deadline: Optional[float],
    debug: Optional[Dict[str, Any]],
) -> Optional[int]:
    start = max(start_speed, MIN_RUNE_SPEED)
    effect_log = _init_effect_log(debug, effect, start)

    coarse_start = start if start % COARSE_STEP == 0 else start + (COARSE_STEP - start % COARSE_STEP)
    coarse_feasible = None
    for rune_speed in range(coarse_start, MAX_RUNE_SPEED + 1, COARSE_STEP):
        if deadline and time.perf_counter() > deadline:
            _finalize_effect_log(debug, effect_log, None)
            return None
        matched = _simulate_attempt(
            detail_preset,
            base_overrides,
            required_order,
            target_key,
            effect,
            rune_speed,
            debug,
            phase="coarse",
        )
        _log_effect_step(effect_log, "coarse_attempts", {"speed": rune_speed, "matched": matched})
        if matched:
            coarse_feasible = rune_speed
            _log_effect_step(effect_log, "coarse_first_feasible", rune_speed)
            break

    if coarse_feasible is None:
        _finalize_effect_log(debug, effect_log, None)
        return None

    bucket_low = max(MIN_RUNE_SPEED, coarse_feasible - COARSE_STEP)
    refine_start = max(start, bucket_low)
    refined = None
    for rune_speed in range(refine_start, coarse_feasible + 1):
        if deadline and time.perf_counter() > deadline:
            _finalize_effect_log(debug, effect_log, None)
            return None
        matched = _simulate_attempt(
            detail_preset,
            base_overrides,
            required_order,
            target_key,
            effect,
            rune_speed,
            debug,
            phase="refine",
        )
        _log_effect_step(effect_log, "refine_attempts", {"speed": rune_speed, "matched": matched})
        if matched:
            refined = rune_speed
            break

    if refined is None:
        _finalize_effect_log(debug, effect_log, None)
        return None

    while refined > MIN_RUNE_SPEED:
        candidate = refined - 1
        if deadline and time.perf_counter() > deadline:
            _finalize_effect_log(debug, effect_log, None)
            return None
        matched = _simulate_attempt(
            detail_preset,
            base_overrides,
            required_order,
            target_key,
            effect,
            candidate,
            debug,
            phase="refine",
        )
        _log_effect_step(effect_log, "refine_attempts", {"speed": candidate, "matched": matched})
        if matched:
            refined = candidate
        else:
            break

    _finalize_effect_log(debug, effect_log, refined)
    return refined


def _matches_required_order(
    detail_preset: Dict[str, Any],
    overrides: Dict[str, Dict[str, int]],
    required_order: RequiredOrder,
    debug: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, List[str], List[Dict[str, Any]]]:
    _, turn_events = simulate_with_turn_log(detail_preset, overrides)
    if required_order.mode == "a2_a3_e":
        actual_order = [event.get("key") for event in turn_events]
        index_map = {key: idx for idx, key in enumerate(actual_order) if key is not None}
        a2, a3, enemy = required_order.order
        if a2 not in index_map or a3 not in index_map or enemy not in index_map:
            return False, actual_order, _trim_turn_events(turn_events, debug)
        is_valid = index_map[a2] < index_map[a3] < index_map[enemy]
        return is_valid, actual_order, _trim_turn_events(turn_events, debug)
    if len(turn_events) < len(required_order.order):
        actual_order = [event.get("key") for event in turn_events]
        return False, actual_order, _trim_turn_events(turn_events, debug)
    actual_order = [event.get("key") for event in turn_events[: len(required_order.order)]]
    return actual_order == required_order.order, actual_order, _trim_turn_events(turn_events, debug)


def _summarize_effect_ranges(effect_to_speed: Dict[int, Optional[int]]) -> List[Dict[str, str]]:
    ranges: List[Dict[str, str]] = []
    sorted_effects = sorted(effect_to_speed.keys())
    if not sorted_effects:
        return ranges

    current_speed = effect_to_speed[sorted_effects[0]]
    range_start = sorted_effects[0]
    for effect in sorted_effects[1:]:
        speed = effect_to_speed[effect]
        if speed != current_speed:
            ranges.append(_format_range(range_start, effect - 1, current_speed))
            range_start = effect
            current_speed = speed

    ranges.append(_format_range(range_start, sorted_effects[-1], current_speed))
    return ranges


def _format_range(start: int, end: int, speed: Optional[int]) -> Dict[str, str]:
    label = f"{start}~{end}" if start != end else str(start)
    speed_label = "No solution" if speed is None else str(speed)
    return {"Effect Range": label, "Rune Speed": speed_label}


def _trim_turn_events(
    turn_events: List[Dict[str, Any]],
    debug: Optional[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    if not debug:
        return []
    return [
        {
            "tick": event.get("tick"),
            "key": event.get("key"),
            "isAlly": event.get("isAlly"),
            "attack_bar_before_reset": event.get("attack_bar_before_reset"),
        }
        for event in turn_events[:10]
    ]


def _record_debug_attempt(
    debug: Optional[Dict[str, Any]],
    effect: int,
    rune_speed: int,
    required_order: RequiredOrder,
    matched: bool,
    actual_order: List[str],
    turn_events: List[Dict[str, Any]],
    phase: str,
) -> None:
    if debug is None:
        return
    if debug.get("truncated"):
        return
    attempts = debug.get("attempts", [])
    limit = debug.get("attempt_limit", 25)
    if len(attempts) >= limit:
        debug["truncated"] = True
        return
    attempts.append({
        "effect": effect,
        "rune_speed": rune_speed,
        "phase": phase,
        "matched": matched,
        "required_order": required_order.order,
        "actual_order": actual_order,
        "turn_events": turn_events,
    })


def _build_debug_unit_summary(
    detail_preset: Dict[str, Any],
    required_order: RequiredOrder,
    overrides: Dict[str, Dict[str, int]],
) -> Dict[str, Any]:
    base_units = detail_preset.get("allies", []) + detail_preset.get("enemies", [])
    summary = {}
    for unit in base_units:
        key = unit.get("key")
        if not key:
            continue
        override = overrides.get(key, {})
        summary[key] = {
            "base_speed": unit.get("base_speed"),
            "rune_speed": override.get("rune_speed", unit.get("rune_speed")),
            "speedIncreasingEffect": override.get(
                "speedIncreasingEffect",
                unit.get("speedIncreasingEffect"),
            ),
            "isSwift": unit.get("isSwift"),
            "isAlly": unit.get("isAlly"),
        }
    return {
        "required_order": required_order.order,
        "units": summary,
        "parity_note": (
            "All units (allies/enemies) use the same ATB tick formula; "
            "differences come from allyEffects/enemyEffects and skills."
        ),
    }


def _simulate_attempt(
    detail_preset: Dict[str, Any],
    base_overrides: Dict[str, Dict[str, int]],
    required_order: RequiredOrder,
    target_key: str,
    effect: int,
    rune_speed: int,
    debug: Optional[Dict[str, Any]],
    phase: str,
) -> bool:
    overrides = dict(base_overrides)
    overrides[target_key] = {
        "rune_speed": rune_speed,
        "speedIncreasingEffect": effect,
    }
    matched, actual_order, turn_events = _matches_required_order(
        detail_preset,
        overrides,
        required_order,
        debug=debug,
    )
    _record_debug_attempt(
        debug,
        effect,
        rune_speed,
        required_order,
        matched,
        actual_order,
        turn_events,
        phase=phase,
    )
    return matched


def _init_effect_log(
    debug: Optional[Dict[str, Any]],
    effect: int,
    start_speed: int,
) -> Optional[Dict[str, Any]]:
    if debug is None:
        return None
    effect_log = {
        "effect": effect,
        "start_speed": start_speed,
        "first_feasible": None,
        "coarse_attempts": [],
        "refine_attempts": [],
        "final_min": None,
    }
    return effect_log


def _log_effect_step(effect_log: Optional[Dict[str, Any]], field: str, value: Any) -> None:
    if effect_log is None:
        return
    if field in ("coarse_attempts", "refine_attempts"):
        effect_log[field].append(value)
    else:
        effect_log[field] = value


def _finalize_effect_log(
    debug: Optional[Dict[str, Any]],
    effect_log: Optional[Dict[str, Any]],
    final_min: Optional[int],
) -> None:
    if debug is None or effect_log is None:
        return
    effect_log["final_min"] = final_min
    debug["effect_logs"].append(effect_log)
