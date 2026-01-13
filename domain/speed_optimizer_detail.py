from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import time
from typing import Any, Dict, List, Optional, Tuple

from config.atb_simulator_presets import ATB_SIMULATOR_PRESETS, build_full_preset
from domain.atb_simulator import simulate_with_turn_log
from domain.atb_simulator_utils import prefix_monsters

MAX_RUNE_SPEED = 400
MAX_EFFECT = 50
SECTION1_TURN_ORDER_DEFAULT = ["a2", "a1", "a3", "e_fast"]
SECTION1_TURN_ORDER_OVERRIDES: Dict[str, List[str]] = {}


@dataclass
class DetailTable:
    ranges: List[Dict[str, str]]


@dataclass
class PresetDetailResult:
    preset_id: str
    a1_table: Optional[DetailTable]
    a3_table: Optional[DetailTable]
    error: Optional[str] = None
    timing: Optional[Dict[str, float]] = None


@lru_cache(maxsize=128)
def build_section1_detail_cached(
    preset_id: str,
    input_1: Optional[int],
    input_2: Optional[int],
    input_3: Optional[int],
    max_runtime_s: Optional[float],
) -> PresetDetailResult:
    preset = build_full_preset(preset_id)
    return _build_preset_detail(
        preset_id,
        preset,
        input_1,
        input_2,
        input_3,
        max_runtime_s=max_runtime_s,
    )


def _build_preset_detail(
    preset_id: str,
    preset: Dict[str, Any],
    input_1: Optional[int],
    input_2: Optional[int],
    input_3: Optional[int],
    max_runtime_s: Optional[float],
) -> PresetDetailResult:
    allies = preset.get("allies", [])
    enemies = preset.get("enemies", [])
    if len(allies) < 3 or len(enemies) < 2:
        return PresetDetailResult(
            preset_id=preset_id,
            a1_table=None,
            a3_table=None,
            error="Preset must contain at least 3 allies and 2 enemies.",
        )

    # Input 2 fixes a1's rune speed so only a3 is optimized.
    start_time = time.perf_counter()
    deadline = start_time + max_runtime_s if max_runtime_s else None

    base_overrides = _build_section1_overrides(allies, enemies, input_1, input_2, input_3)
    prefixed_allies, ally_key_map = prefix_monsters(allies, prefix="A")
    prefixed_enemies, enemy_key_map = prefix_monsters(enemies, prefix="E")

    prefixed_overrides = _prefix_overrides(base_overrides, ally_key_map, enemy_key_map)
    e_fast_start = time.perf_counter()
    e_fast_key = _select_fastest_enemy(
        preset,
        prefixed_allies,
        prefixed_enemies,
        prefixed_overrides,
    )
    e_fast_time = time.perf_counter() - e_fast_start
    if not e_fast_key:
        return PresetDetailResult(
            preset_id=preset_id,
            a1_table=None,
            a3_table=None,
            error="No enemy took a turn in the simulation.",
            timing={"e_fast_s": e_fast_time},
        )

    detail_preset, detail_keys = _build_detail_preset(
        preset,
        prefixed_allies,
        prefixed_enemies,
        e_fast_key,
    )
    required_order = _resolve_required_order(preset_id, detail_keys)
    if required_order is None:
        return PresetDetailResult(
            preset_id=preset_id,
            a1_table=None,
            a3_table=None,
            error="Invalid required turn order mapping for this preset.",
            timing={"e_fast_s": e_fast_time},
        )

    a3_start = time.perf_counter()
    a3_table, a3_error = _build_unit_detail_table(
        detail_preset,
        required_order,
        prefixed_overrides,
        target_key=detail_keys["a3"],
        deadline=deadline,
    )
    a3_time = time.perf_counter() - a3_start

    error_messages = [msg for msg in [a3_error] if msg]
    combined_error = "\n".join(error_messages) if error_messages else None

    return PresetDetailResult(
        preset_id=preset_id,
        a1_table=None,
        a3_table=a3_table,
        error=combined_error,
        timing={
            "e_fast_s": e_fast_time,
            "a3_s": a3_time,
        },
    )


def _build_section1_overrides(
    allies: List[Dict[str, Any]],
    enemies: List[Dict[str, Any]],
    input_1: Optional[int],
    input_2: Optional[int],
    input_3: Optional[int],
) -> Dict[str, Dict[str, int]]:
    overrides: Dict[str, Dict[str, int]] = {}
    a1_key = allies[0].get("key")
    if a1_key and input_2 is not None:
        overrides[a1_key] = {"rune_speed": input_2}

    a2_key = allies[1].get("key")
    if a2_key and input_1 is not None:
        overrides[a2_key] = {"rune_speed": input_1}

    a2_rune_speed = input_1 if input_1 is not None else allies[1].get("rune_speed", 0)
    e2_key = enemies[1].get("key")
    if e2_key:
        enemy_speed = input_3 if input_3 is not None else a2_rune_speed
        overrides[e2_key] = {"rune_speed": enemy_speed}

    return overrides


def _resolve_required_order(
    preset_id: str,
    detail_keys: Dict[str, str],
) -> Optional[List[str]]:
    order_tokens = SECTION1_TURN_ORDER_OVERRIDES.get(preset_id, SECTION1_TURN_ORDER_DEFAULT)
    resolved = []
    for token in order_tokens:
        key = detail_keys.get(token)
        if not key:
            # Previously this could return None keys and cause comparisons to never match.
            return None
        resolved.append(key)
    return resolved


def _prefix_overrides(
    overrides: Dict[str, Dict[str, int]],
    ally_key_map: Dict[str, str],
    enemy_key_map: Dict[str, str],
) -> Dict[str, Dict[str, int]]:
    prefixed: Dict[str, Dict[str, int]] = {}
    for key, values in overrides.items():
        if key in ally_key_map:
            prefixed[ally_key_map[key]] = values
        elif key in enemy_key_map:
            prefixed[enemy_key_map[key]] = values
    return prefixed


def _select_fastest_enemy(
    preset: Dict[str, Any],
    prefixed_allies: List[Dict[str, Any]],
    prefixed_enemies: List[Dict[str, Any]],
    overrides: Dict[str, Dict[str, int]],
) -> Optional[str]:
    simulation_preset = {
        "allies": prefixed_allies,
        "enemies": prefixed_enemies,
        "allyEffects": preset.get("allyEffects", {}),
        "enemyEffects": preset.get("enemyEffects", {}),
        "tickCount": preset.get("tickCount", 0),
    }
    _, turn_events = simulate_with_turn_log(simulation_preset, overrides)
    for event in turn_events:
        if not event.get("isAlly"):
            return event.get("key")
    return None


def _build_detail_preset(
    preset: Dict[str, Any],
    prefixed_allies: List[Dict[str, Any]],
    prefixed_enemies: List[Dict[str, Any]],
    e_fast_key: str,
) -> Tuple[Dict[str, Any], Dict[str, str]]:
    a1 = prefixed_allies[0]
    a2 = prefixed_allies[1]
    a3 = prefixed_allies[2]
    e_fast = next(
        (enemy for enemy in prefixed_enemies if enemy.get("key") == e_fast_key),
        prefixed_enemies[0],
    )

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
    required_order: List[str],
    base_overrides: Dict[str, Dict[str, int]],
    target_key: Optional[str],
    deadline: Optional[float],
) -> Tuple[Optional[DetailTable], Optional[str]]:
    if not target_key:
        return None, "Target unit key was missing."

    effect_to_speed: Dict[int, Optional[int]] = {}
    start_speed = 0
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
        )
        effect_to_speed[effect] = minimum
        if minimum is not None:
            start_speed = minimum

    if all(value is None for value in effect_to_speed.values()):
        return None, None

    return DetailTable(ranges=_summarize_effect_ranges(effect_to_speed)), None


def _find_minimum_rune_speed(
    detail_preset: Dict[str, Any],
    required_order: List[str],
    base_overrides: Dict[str, Dict[str, int]],
    target_key: str,
    effect: int,
    start_speed: int,
    deadline: Optional[float],
) -> Optional[int]:
    for rune_speed in range(start_speed, MAX_RUNE_SPEED + 1):
        if deadline and time.perf_counter() > deadline:
            return None
        overrides = dict(base_overrides)
        overrides[target_key] = {
            "rune_speed": rune_speed,
            "speedIncreasingEffect": effect,
        }
        if _matches_required_order(detail_preset, overrides, required_order):
            return rune_speed
    return None


def _matches_required_order(
    detail_preset: Dict[str, Any],
    overrides: Dict[str, Dict[str, int]],
    required_order: List[str],
) -> bool:
    _, turn_events = simulate_with_turn_log(detail_preset, overrides)
    if len(turn_events) < len(required_order):
        return False
    actual_order = [event.get("key") for event in turn_events[: len(required_order)]]
    return actual_order == required_order


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
