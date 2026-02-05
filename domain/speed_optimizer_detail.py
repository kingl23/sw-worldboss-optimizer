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
from domain.atb_simulator import simulate_atb_table, simulate_with_turn_log
from domain.atb_simulator_utils import prefix_monsters

MAX_RUNE_SPEED = 250
MIN_RUNE_SPEED = 150
COARSE_STEP = 10
MAX_EFFECT = 60
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
    preset_name: str
    preset_label: str
    leader_percent: int
    objective: str
    legend: str
    formula_notes: List[str]
    formula_table: List[Dict[str, Any]]
    no_solution_diagnostic: Optional[Dict[str, Any]]
    effect_table: Optional[DetailTable]
    min_cut_result: Optional[Dict[str, Any]]
    tick_atb_table: Optional[List[Dict[str, Any]]]
    effect_table_title: Optional[str] = None
    effect_table_step1: Optional[DetailTable] = None
    effect_table_title_step1: Optional[str] = None
    tick_headers: Optional[List[str]] = None
    tick_atb_table_step1: Optional[List[Dict[str, Any]]] = None
    tick_atb_table_step2: Optional[List[Dict[str, Any]]] = None
    status: Optional[str] = None


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
            preset_name=preset_id,
            preset_label=preset_id,
            leader_percent=get_leader_percent(preset_id),
            objective="Invalid preset",
            legend="",
            formula_notes=[],
            formula_table=[],
            no_solution_diagnostic=None,
            effect_table=None,
            min_cut_result=None,
            tick_atb_table=None,
            tick_headers=None,
            status="NO VALID SOLUTION",
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
            preset_name=preset_id,
            preset_label=preset_id,
            leader_percent=get_leader_percent(preset_id),
            objective="Invalid required order",
            legend="",
            formula_notes=[],
            formula_table=[],
            no_solution_diagnostic=None,
            effect_table=None,
            min_cut_result=None,
            tick_atb_table=None,
            tick_headers=None,
            status="NO VALID SOLUTION",
        )

    baseline_overrides = dict(prefixed_overrides)
    baseline_overrides[detail_keys["a3"]] = {
        "rune_speed": MIN_RUNE_SPEED,
        "speedIncreasingEffect": 0,
    }
    case_display = _build_case_display(
        preset_id,
        detail_preset,
        detail_keys,
        required_order,
        baseline_overrides,
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
        debug_atb_log: List[Dict[str, Any]] = []
        _, baseline_turn_events = simulate_with_turn_log(
            detail_preset,
            baseline_overrides,
            debug_snapshots=debug_snapshots,
            debug_ticks=debug_payload["tick_limit"],
            debug_keys=set(debug_payload["unit_order"].values()),
            debug_atb_log=debug_atb_log,
            debug_atb_keys=[
                detail_keys["a1"],
                detail_keys["a2"],
                detail_keys["a3"],
                detail_keys["e_fast"],
            ],
            debug_atb_labels=case_display["unit_display_map"],
        )
        debug_payload["tick_snapshots"] = debug_snapshots
        debug_payload["baseline_turn_events"] = baseline_turn_events
        debug_payload["tick_atb_log"] = _format_atb_log(debug_atb_log, case_display["unit_display_map"])

    effect_table, effect_error = _build_unit_detail_table(
        detail_preset,
        required_order,
        prefixed_overrides,
        detail_keys["a3"],
        deadline,
        debug_payload,
    )
    tick_atb_table = _build_final_tick_table_for_a3(
        detail_preset,
        required_order,
        prefixed_overrides,
        detail_keys["a3"],
        case_display["short_label_map"],
        deadline,
    )
    min_speed = _find_minimum_rune_speed(
        detail_preset,
        required_order,
        prefixed_overrides,
        detail_keys["a3"],
        effect=0,
        start_speed=MIN_RUNE_SPEED,
        deadline=deadline,
        debug=None,
    )
    objective = _format_required_order_display(
        preset_id,
        required_order,
        case_display["name_label_map"],
    )
    effect_table_title = f"{case_display['name_label_map'].get(detail_keys['a3'], detail_keys['a3'])} Effect–Speed Table"
    formula_notes = _build_formula_notes()
    if min_speed is None:
        no_solution_diagnostic = _build_no_solution_diagnostic(
            detail_preset,
            required_order,
            prefixed_overrides,
            detail_keys["a3"],
            case_display,
        )
        return PresetDetailResult(
            preset_name=preset_id,
            preset_label=case_display["preset_label"],
            leader_percent=get_leader_percent(preset_id),
            objective=objective,
            legend=case_display["legend"],
            formula_notes=formula_notes,
            formula_table=_build_formula_table(
                detail_preset,
                prefixed_overrides,
                case_display,
                get_leader_percent(preset_id),
            ),
            no_solution_diagnostic=no_solution_diagnostic,
            effect_table=effect_table,
            effect_table_title=effect_table_title,
            min_cut_result=None,
            tick_atb_table=None,
            tick_headers=None,
            status=effect_error or "NO VALID SOLUTION",
        )
    overrides_for_formula = dict(prefixed_overrides)
    overrides_for_formula[detail_keys["a3"]] = {
        "rune_speed": min_speed,
        "speedIncreasingEffect": 0,
    }
    tick_headers = _build_tick_headers(detail_preset, overrides_for_formula, case_display["name_label_map"])
    return PresetDetailResult(
        preset_name=preset_id,
        preset_label=case_display["preset_label"],
        leader_percent=get_leader_percent(preset_id),
        objective=objective,
        legend=case_display["legend"],
        formula_notes=formula_notes,
        formula_table=_build_formula_table(
            detail_preset,
            overrides_for_formula,
            case_display,
            get_leader_percent(preset_id),
        ),
        no_solution_diagnostic=None,
        effect_table=effect_table,
        effect_table_title=effect_table_title,
        min_cut_result=None,
        tick_atb_table=tick_atb_table,
        tick_headers=tick_headers,
        status="OK",
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
            preset_name=preset_id,
            preset_label=preset_id,
            leader_percent=get_leader_percent(preset_id),
            objective="Invalid preset",
            legend="",
            formula_notes=[],
            formula_table=[],
            no_solution_diagnostic=None,
            effect_table=None,
            min_cut_result=None,
            tick_atb_table=None,
            tick_headers=None,
            tick_atb_table_step1=None,
            tick_atb_table_step2=None,
            status="NO VALID SOLUTION",
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
            preset_name=preset_id,
            preset_label=preset_id,
            leader_percent=get_leader_percent(preset_id),
            objective="Invalid required order",
            legend="",
            formula_notes=[],
            formula_table=[],
            no_solution_diagnostic=None,
            effect_table=None,
            min_cut_result=None,
            tick_atb_table=None,
            tick_headers=None,
            tick_atb_table_step1=None,
            tick_atb_table_step2=None,
            status="NO VALID SOLUTION",
        )

    baseline_overrides = dict(prefixed_overrides)
    baseline_overrides[detail_keys["a3"]] = {
        "rune_speed": MIN_RUNE_SPEED,
        "speedIncreasingEffect": 0,
    }
    case_display = _build_case_display(
        preset_id,
        detail_preset,
        detail_keys,
        required_order,
        baseline_overrides,
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
        debug_atb_log: List[Dict[str, Any]] = []
        _, baseline_turn_events = simulate_with_turn_log(
            detail_preset,
            baseline_overrides,
            debug_snapshots=debug_snapshots,
            debug_ticks=debug_payload["tick_limit"],
            debug_keys=set(debug_payload["unit_order"].values()),
            debug_atb_log=debug_atb_log,
            debug_atb_keys=[
                detail_keys["a1"],
                detail_keys["a2"],
                detail_keys["a3"],
                detail_keys["e_fast"],
            ],
            debug_atb_labels=case_display["unit_display_map"],
        )
        debug_payload["tick_snapshots"] = debug_snapshots
        debug_payload["baseline_turn_events"] = baseline_turn_events
        debug_payload["tick_atb_log"] = _format_atb_log(debug_atb_log, case_display["unit_display_map"])

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

    objective = _format_required_order_display(
        preset_id,
        required_order,
        case_display["name_label_map"],
    )
    effect_table_title_step1 = (
        f"{case_display['name_label_map'].get(detail_keys['a1'], detail_keys['a1'])} Effect–Speed Table"
    )
    effect_table_title = f"{case_display['name_label_map'].get(detail_keys['a3'], detail_keys['a3'])} Effect–Speed Table"
    formula_notes = _build_formula_notes()
    if a1_min0 is None:
        return PresetDetailResult(
            preset_name=preset_id,
            preset_label=case_display["preset_label"],
            leader_percent=get_leader_percent(preset_id),
            objective=objective,
            legend=case_display["legend"],
            formula_notes=formula_notes,
            formula_table=_build_formula_table(
                detail_preset,
                prefixed_overrides,
                case_display,
                get_leader_percent(preset_id),
            ),
            no_solution_diagnostic=_build_no_solution_diagnostic(
                detail_preset,
                required_order,
                prefixed_overrides,
                detail_keys["a3"],
                case_display,
            ),
            effect_table=_build_no_solution_table(),
            effect_table_title=effect_table_title,
            min_cut_result=None,
            tick_atb_table=None,
            tick_headers=None,
            tick_atb_table_step1=None,
            tick_atb_table_step2=None,
            status="NO VALID SOLUTION",
        )

    effect_table_step1, _ = _build_unit_detail_table(
        detail_preset,
        required_order_a1,
        prefixed_overrides,
        detail_keys["a1"],
        deadline,
        debug_payload,
    )
    step1_overrides = dict(prefixed_overrides)
    step1_overrides[detail_keys["a1"]] = {
        "rune_speed": a1_min0,
        "speedIncreasingEffect": 0,
    }
    fixed_overrides = dict(step1_overrides)
    case_display = _build_case_display(
        preset_id,
        detail_preset,
        detail_keys,
        required_order,
        fixed_overrides,
    )
    effect_table, effect_error = _build_unit_detail_table(
        detail_preset,
        required_order,
        fixed_overrides,
        detail_keys["a3"],
        deadline,
        debug_payload,
    )
    tick_atb_table_step2 = _build_final_tick_table_for_a3(
        detail_preset,
        required_order,
        fixed_overrides,
        detail_keys["a3"],
        case_display["short_label_map"],
        deadline,
    )
    min_speed_a3 = _find_minimum_rune_speed(
        detail_preset,
        required_order,
        fixed_overrides,
        detail_keys["a3"],
        effect=0,
        start_speed=MIN_RUNE_SPEED,
        deadline=deadline,
        debug=None,
    )
    if min_speed_a3 is None:
        return PresetDetailResult(
            preset_name=preset_id,
            preset_label=case_display["preset_label"],
            leader_percent=get_leader_percent(preset_id),
            objective=objective,
            legend=case_display["legend"],
            formula_notes=formula_notes,
            formula_table=_build_formula_table(
                detail_preset,
                fixed_overrides,
                case_display,
                get_leader_percent(preset_id),
            ),
            no_solution_diagnostic=_build_no_solution_diagnostic(
                detail_preset,
                required_order,
                fixed_overrides,
                detail_keys["a3"],
                case_display,
            ),
            effect_table=effect_table,
            effect_table_title=effect_table_title,
            effect_table_step1=effect_table_step1,
            effect_table_title_step1=effect_table_title_step1,
            min_cut_result=None,
            tick_atb_table=None,
            tick_headers=None,
            tick_atb_table_step1=None,
            tick_atb_table_step2=None,
            status=effect_error or "NO VALID SOLUTION",
        )
    overrides_for_formula = dict(fixed_overrides)
    overrides_for_formula[detail_keys["a3"]] = {
        "rune_speed": min_speed_a3,
        "speedIncreasingEffect": 0,
    }
    tick_headers = _build_tick_headers(detail_preset, overrides_for_formula, case_display["name_label_map"])
    return PresetDetailResult(
        preset_name=preset_id,
        preset_label=case_display["preset_label"],
        leader_percent=get_leader_percent(preset_id),
        objective=objective,
        legend=case_display["legend"],
        formula_notes=formula_notes,
        formula_table=_build_formula_table(
            detail_preset,
            overrides_for_formula,
            case_display,
            get_leader_percent(preset_id),
        ),
        no_solution_diagnostic=None,
        effect_table=effect_table,
        effect_table_title=effect_table_title,
        effect_table_step1=effect_table_step1,
        effect_table_title_step1=effect_table_title_step1,
        min_cut_result=None,
        tick_atb_table=tick_atb_table_step2,
        tick_headers=tick_headers,
        tick_atb_table_step1=None,
        tick_atb_table_step2=None,
        status="OK",
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
    if preset_id in {"Preset A", "Preset B"}:
        if input_2 is None:
            raise ValueError("input_2 is required for preset mapping.")
        if a2_key:
            overrides[a2_key] = {"rune_speed": input_2 + leader_percent + TOWER_PERCENT}
    elif preset_id == "Preset C":
        if input_1 is None:
            raise ValueError("input_1 is required for preset mapping.")
        if a2_key:
            overrides[a2_key] = {"rune_speed": input_1}
    elif preset_id == "Preset D":
        if input_1 is None:
            raise ValueError("input_1 is required for preset mapping.")
        if a2_key:
            overrides[a2_key] = {"rune_speed": input_1 - 1}
    elif preset_id == "Preset E":
        if input_1 is None:
            raise ValueError("input_1 is required for preset mapping.")
        if a2_key:
            overrides[a2_key] = {"rune_speed": input_1 + 1}
    elif preset_id in {"Preset F", "Preset G"}:
        if input_1 is None:
            raise ValueError("input_1 is required for preset mapping.")
        if a1_key:
            overrides[a1_key] = {"rune_speed": input_1 - 2}

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


def _build_case_display(
    preset_id: str,
    detail_preset: Dict[str, Any],
    detail_keys: Dict[str, str],
    required_order: RequiredOrder,
    overrides: Dict[str, Dict[str, int]],
) -> Dict[str, Any]:
    unit_names = _build_unit_name_map(detail_preset, detail_keys, preset_id)
    unit_display_map = {
        detail_keys["a1"]: f"A1({unit_names['a1']})",
        detail_keys["a2"]: f"A2({unit_names['a2']})",
        detail_keys["a3"]: f"A3({unit_names['a3']})",
        detail_keys["e_fast"]: f"E({unit_names['e']})",
    }
    short_label_map = {
        detail_keys["a1"]: "A1",
        detail_keys["a2"]: "A2",
        detail_keys["a3"]: "A3",
        detail_keys["e_fast"]: "E",
    }
    name_label_map = {
        detail_keys["a1"]: unit_names["a1"],
        detail_keys["a2"]: unit_names["a2"],
        detail_keys["a3"]: unit_names["a3"],
        detail_keys["e_fast"]: unit_names["e"],
    }
    matched, actual_order, _ = _matches_required_order(
        detail_preset,
        overrides,
        required_order,
        debug=None,
    )
    required_display = _format_required_order_display(
        preset_id,
        required_order,
        name_label_map,
    )
    actual_display = _format_actual_order_display(actual_order, name_label_map, required_order)
    display_title = f"{preset_id} — Required: {required_display}"
    resolved_specs = _build_resolved_specs(
        preset_id,
        detail_preset,
        detail_keys,
        overrides,
        unit_display_map,
    )
    legend = (
        f"A1={unit_names['a1']}, A2={unit_names['a2']}, "
        f"A3={unit_names['a3']}, E={unit_names['e']}"
    )
    preset_label = (
        f"{unit_names['a1']} / {unit_names['a2']} / {unit_names['a3']} "
        f"| Leader: +{get_leader_percent(preset_id)}%"
    )
    return {
        "display_title": display_title,
        "resolved_specs": resolved_specs,
        "required_order_display": required_display,
        "actual_order_display": actual_display,
        "pass_flag": matched,
        "unit_display_map": unit_display_map,
        "short_label_map": short_label_map,
        "name_label_map": name_label_map,
        "legend": legend,
        "preset_label": preset_label,
    }


def _build_formula_notes() -> List[str]:
    return [
        f"v_total = v_base + v_rune + (v_base × (leader% + tower%)/100); tower%={TOWER_PERCENT}",
        "If speed buff: combat_speed = v_total × [1 + 0.3 × (100 + effect)/100]; otherwise combat_speed = v_total",
        "ΔATB per tick = combat_speed × 0.07",
    ]


def _build_formula_table(
    detail_preset: Dict[str, Any],
    overrides: Dict[str, Dict[str, int]],
    case_display: Dict[str, Any],
    leader_percent: int,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    label_map = case_display["name_label_map"]
    units = detail_preset.get("allies", []) + detail_preset.get("enemies", [])
    for unit in units:
        key = unit.get("key")
        if not key or key not in label_map:
            continue
        base_speed = unit.get("base_speed", 0)
        rune_speed = overrides.get(key, {}).get("rune_speed", unit.get("rune_speed", 0))
        v_total = base_speed + rune_speed + (base_speed * (leader_percent + TOWER_PERCENT) / 100)
        v_total_formula = (
            f"{base_speed} + {rune_speed} + ({base_speed} × ({leader_percent}+{TOWER_PERCENT})/100)"
        )
        effect = 0
        has_speed_buff = bool(unit.get("has_speed_buff"))
        if has_speed_buff:
            combat_speed = v_total * (1 + 0.3 * (100 + effect) / 100)
            combat_formula = "v_total × [1 + 0.3 × (100 + effect)/100]"
        else:
            combat_speed = v_total
            combat_formula = "v_total"
        atb_gain = combat_speed * 0.07
        rows.append({
            "Unit": label_map[key],
            "v_base": base_speed,
            "v_rune": rune_speed,
            "leader%": leader_percent,
            "tower%": TOWER_PERCENT,
            "v_total": round(v_total, 2),
            "v_total_formula": v_total_formula,
            "combat_speed (effect=0)": round(combat_speed, 2),
            "combat_speed_formula": combat_formula,
            "ΔATB/tick": round(atb_gain, 2),
        })
    return rows


def _build_no_solution_diagnostic(
    detail_preset: Dict[str, Any],
    required_order: RequiredOrder,
    overrides: Dict[str, Dict[str, int]],
    target_key: Optional[str],
    case_display: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    if not target_key:
        return None
    overrides_max = dict(overrides)
    overrides_max[target_key] = {
        "rune_speed": MAX_RUNE_SPEED,
        "speedIncreasingEffect": 0,
    }
    _, turn_events = simulate_with_turn_log(detail_preset, overrides_max)
    actual_order = [event.get("key") for event in turn_events]
    actual_display = _format_actual_order_display(
        actual_order,
        case_display["name_label_map"],
        required_order,
    )
    return {
        "search_range": f"{MIN_RUNE_SPEED}–{MAX_RUNE_SPEED}",
        "actual_order_at_max": actual_display,
    }


def _build_unit_name_map(
    detail_preset: Dict[str, Any],
    detail_keys: Dict[str, str],
    preset_id: str,
) -> Dict[str, str]:
    base_units = detail_preset.get("allies", []) + detail_preset.get("enemies", [])
    name_map = {unit.get("key"): unit.get("name", unit.get("key")) for unit in base_units}
    reference_index = 1 if preset_id in {"Preset A", "Preset B", "Preset C", "Preset D", "Preset E"} else 0
    reference_unit = detail_preset.get("allies", [])[reference_index]
    mirror_note = f"Mirrored {reference_unit.get('name', 'Unknown')}"
    return {
        "a1": name_map.get(detail_keys["a1"], detail_keys["a1"]),
        "a2": name_map.get(detail_keys["a2"], detail_keys["a2"]),
        "a3": name_map.get(detail_keys["a3"], detail_keys["a3"]),
        "e": f"Enemy ({mirror_note})",
    }


def _format_required_order_display(
    preset_id: str,
    required_order: RequiredOrder,
    label_map: Dict[str, str],
) -> str:
    if preset_id == "Preset A":
        a2, a3, enemy = required_order.order
        unconstrained_keys = [key for key in label_map.keys() if key not in required_order.order]
        unconstrained_label = label_map.get(unconstrained_keys[0], "Ally") if unconstrained_keys else "Ally"
        return (
            f"{label_map.get(a2, a2)} → {label_map.get(a3, a3)} → "
            f"{label_map.get(enemy, enemy)} ({unconstrained_label} unconstrained)"
        )
    return " → ".join(label_map.get(key, key) for key in required_order.order)


def _format_actual_order_display(
    actual_order: List[str],
    unit_display_map: Dict[str, str],
    required_order: RequiredOrder,
) -> str:
    if required_order.mode == "a2_a3_e":
        display = [unit_display_map.get(key, key) for key in actual_order[:4]]
        return " → ".join(display)
    display = [unit_display_map.get(key, key) for key in actual_order[: len(required_order.order)]]
    return " → ".join(display)


def _build_resolved_specs(
    preset_id: str,
    detail_preset: Dict[str, Any],
    detail_keys: Dict[str, str],
    overrides: Dict[str, Dict[str, int]],
    unit_display_map: Dict[str, str],
) -> Dict[str, Dict[str, Any]]:
    leader_percent = get_leader_percent(preset_id)
    summary: Dict[str, Dict[str, Any]] = {}
    units = detail_preset.get("allies", []) + detail_preset.get("enemies", [])
    for unit in units:
        key = unit.get("key")
        if not key or key not in unit_display_map:
            continue
        rune_speed = overrides.get(key, {}).get("rune_speed", unit.get("rune_speed", 0))
        base_speed = unit.get("base_speed", 0)
        v_total = base_speed + rune_speed + (base_speed * (leader_percent + TOWER_PERCENT) / 100)
        has_speed_buff = bool(unit.get("has_speed_buff"))
        v_combat = v_total * (1.3 if has_speed_buff else 1.0)
        summary[unit_display_map[key]] = {
            "base_speed": base_speed,
            "rune_speed": rune_speed,
            "leader_percent": leader_percent,
            "speed_buff": has_speed_buff,
            "v_total": v_total,
            "v_combat": v_combat,
        }
    return summary


def _build_tick_atb_table(
    detail_preset: Dict[str, Any],
    overrides: Dict[str, Dict[str, int]],
    short_label_map: Dict[str, str],
) -> List[Dict[str, Any]]:
    units = {unit.get("key"): unit for unit in detail_preset.get("allies", []) + detail_preset.get("enemies", [])}
    name_map = {unit.get("key"): unit.get("name", unit.get("key")) for unit in units.values()}
    debug_atb_log = simulate_atb_table(
        detail_preset,
        overrides,
        tick_limit=16,
        atb_keys=list(short_label_map.keys()),
        atb_labels=short_label_map,
        atb_names=name_map,
    )
    formatted = _format_atb_log(debug_atb_log, short_label_map)
    return [row for row in formatted if 0 <= int(row.get("tick", 0)) <= 15]


def _build_tick_headers(
    detail_preset: Dict[str, Any],
    overrides: Dict[str, Dict[str, int]],
    name_label_map: Dict[str, str],
) -> List[str]:
    units = {unit.get("key"): unit for unit in detail_preset.get("allies", []) + detail_preset.get("enemies", [])}
    headers = []
    for key in [*name_label_map.keys()]:
        unit = units.get(key, {})
        base_speed = unit.get("base_speed", 0)
        rune_speed = overrides.get(key, {}).get("rune_speed", unit.get("rune_speed", 0))
        label = name_label_map.get(key, unit.get("name", key))
        if unit.get("isAlly") is False:
            label = "적"
        headers.append(f"{label} ({base_speed}+{rune_speed})")
    return headers


def _build_final_tick_table_for_a3(
    detail_preset: Dict[str, Any],
    required_order: RequiredOrder,
    base_overrides: Dict[str, Dict[str, int]],
    target_key: str,
    short_label_map: Dict[str, str],
    deadline: Optional[float],
) -> List[Dict[str, Any]]:
    min_speed = _find_minimum_rune_speed(
        detail_preset,
        required_order,
        base_overrides,
        target_key,
        effect=0,
        start_speed=MIN_RUNE_SPEED,
        deadline=deadline,
        debug=None,
    )
    if min_speed is None:
        return []
    overrides = dict(base_overrides)
    overrides[target_key] = {
        "rune_speed": min_speed,
        "speedIncreasingEffect": 0,
    }
    return _build_tick_atb_table(detail_preset, overrides, short_label_map)


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

    return DetailTable(ranges=_summarize_effect_ranges(effect_to_speed)), None


def _build_no_solution_table() -> DetailTable:
    effect_to_speed = {effect: None for effect in range(0, MAX_EFFECT + 1)}
    return DetailTable(ranges=_summarize_effect_ranges(effect_to_speed))


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
        index_map: Dict[str, int] = {}
        for idx, key in enumerate(actual_order):
            if key is None or key in index_map:
                continue
            index_map[key] = idx
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
    speed_label = "NO SOLUTION" if speed is None else str(speed)
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


def _format_atb_log(
    atb_log: List[Dict[str, Any]],
    label_map: Dict[str, str],
) -> List[Dict[str, Any]]:
    formatted: List[Dict[str, Any]] = []
    for entry in atb_log:
        row: Dict[str, Any] = {
            "tick": entry.get("tick"),
            "act": entry.get("actor_label"),
        }
        atb_values = entry.get("atb", {})
        for key, label in label_map.items():
            row[label] = atb_values.get(key)
        speed_buff_keys = entry.get("speed_buff_keys") or []
        if speed_buff_keys:
            row["speed_buff_labels"] = [label_map.get(key, key) for key in speed_buff_keys]
        ally_atb_low_target = entry.get("ally_atb_low_target")
        if ally_atb_low_target:
            row["ally_atb_low_target"] = label_map.get(ally_atb_low_target, ally_atb_low_target)
            row["ally_atb_low_target_name"] = entry.get("ally_atb_low_target_name")
        formatted.append(row)
    return formatted


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
