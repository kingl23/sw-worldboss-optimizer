import copy
import math
from typing import Any, Dict, List, Optional, Tuple


def simulate(preset: Dict[str, Any], overrides: Optional[Dict[str, Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    allies = preset.get("allies", [])
    enemies = preset.get("enemies", [])
    if not allies and not enemies:
        return []

    tick_count = preset.get("tickCount", 0)
    tick_size = preset.get("tickSize", 0)

    overrides = overrides or {}
    allies = apply_overrides(allies, overrides)
    enemies = apply_overrides(enemies, overrides)

    simulator = {
        "allies": allies,
        "enemies": enemies,
        "allyEffects": preset.get("allyEffects", {}),
        "enemyEffects": preset.get("enemyEffects", {}),
        "tickCount": tick_count,
        "tickSize": tick_size,
        "ticks": [],
    }

    monsters: List[Dict[str, Any]] = []
    for idx, ally in enumerate(allies):
        ally["ally_index"] = idx
        monsters.append(transform_monster(simulator, ally))
    for enemy in enemies:
        monsters.append(transform_monster(simulator, enemy))

    monsters = sorted(monsters, key=lambda item: item["combat_speed"], reverse=True)

    simulator["ticks"].append({
        "tick": 0,
        "monsters": copy.deepcopy(monsters),
    })

    for i in range(1, tick_count + 1):
        tick_monsters = run_tick(simulator, simulator["ticks"][i - 1]["monsters"], tick_index=i)
        simulator["ticks"].append({
            "tick": i,
            "monsters": copy.deepcopy(tick_monsters),
        })

    if simulator["ticks"]:
        simulator["ticks"].pop()

    return simulator["ticks"]


def simulate_with_turn_log(
    preset: Dict[str, Any],
    overrides: Optional[Dict[str, Dict[str, Any]]] = None,
    debug_snapshots: Optional[List[Dict[str, Any]]] = None,
    debug_ticks: int = 0,
    debug_keys: Optional[set[str]] = None,
    debug_atb_log: Optional[List[Dict[str, Any]]] = None,
    debug_atb_keys: Optional[List[str]] = None,
    debug_atb_labels: Optional[Dict[str, str]] = None,
    debug_atb_names: Optional[Dict[str, str]] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    allies = preset.get("allies", [])
    enemies = preset.get("enemies", [])
    if not allies and not enemies:
        return [], []

    tick_count = preset.get("tickCount", 0)
    overrides = overrides or {}
    allies = apply_overrides(allies, overrides)
    enemies = apply_overrides(enemies, overrides)

    simulator = {
        "allies": allies,
        "enemies": enemies,
        "allyEffects": preset.get("allyEffects", {}),
        "enemyEffects": preset.get("enemyEffects", {}),
        "tickCount": tick_count,
        "ticks": [],
    }

    monsters: List[Dict[str, Any]] = []
    for idx, ally in enumerate(allies):
        ally["ally_index"] = idx
        monsters.append(transform_monster(simulator, ally))
    for enemy in enemies:
        monsters.append(transform_monster(simulator, enemy))

    monsters = sorted(monsters, key=lambda item: item["combat_speed"], reverse=True)

    simulator["ticks"].append({
        "tick": 0,
        "monsters": copy.deepcopy(monsters),
    })
    _collect_debug_tick(
        debug_snapshots,
        tick_index=0,
        monsters=simulator["ticks"][0]["monsters"],
        debug_ticks=debug_ticks,
        debug_keys=debug_keys,
    )

    turn_events: List[Dict[str, Any]] = []
    for i in range(1, tick_count + 1):
        tick_monsters = run_tick(
            simulator,
            simulator["ticks"][i - 1]["monsters"],
            tick_index=i,
            turn_events=turn_events,
            atb_log=debug_atb_log,
            atb_log_keys=debug_atb_keys,
            atb_log_labels=debug_atb_labels,
            atb_log_names=debug_atb_names,
        )
        simulator["ticks"].append({
            "tick": i,
            "monsters": copy.deepcopy(tick_monsters),
        })
        _collect_debug_tick(
            debug_snapshots,
            tick_index=i,
            monsters=simulator["ticks"][i]["monsters"],
            debug_ticks=debug_ticks,
            debug_keys=debug_keys,
        )

    if simulator["ticks"]:
        simulator["ticks"].pop()

    return simulator["ticks"], turn_events


def simulate_atb_table(
    preset: Dict[str, Any],
    overrides: Optional[Dict[str, Dict[str, Any]]] = None,
    tick_limit: int = 16,
    atb_keys: Optional[List[str]] = None,
    atb_labels: Optional[Dict[str, str]] = None,
    atb_names: Optional[Dict[str, str]] = None,
) -> List[Dict[str, Any]]:
    if tick_limit <= 0:
        return []
    overrides = overrides or {}
    allies = apply_overrides(preset.get("allies", []), overrides)
    enemies = apply_overrides(preset.get("enemies", []), overrides)

    simulator = {
        "allies": allies,
        "enemies": enemies,
        "allyEffects": preset.get("allyEffects", {}),
        "enemyEffects": preset.get("enemyEffects", {}),
        "tickCount": tick_limit,
        "ticks": [],
    }

    monsters: List[Dict[str, Any]] = []
    for idx, ally in enumerate(allies):
        ally["ally_index"] = idx
        monsters.append(transform_monster(simulator, ally))
    for enemy in enemies:
        monsters.append(transform_monster(simulator, enemy))
    monsters = sorted(monsters, key=lambda item: item["combat_speed"], reverse=True)

    simulator["ticks"].append({
        "tick": 0,
        "monsters": copy.deepcopy(monsters),
    })

    atb_log: List[Dict[str, Any]] = []
    for tick_index in range(tick_limit):
        monsters = run_tick(
            simulator,
            monsters,
            tick_index=tick_index,
            atb_log=atb_log,
            atb_log_keys=atb_keys,
            atb_log_labels=atb_labels,
            atb_log_names=atb_names,
        )
        simulator["ticks"].append({
            "tick": tick_index + 1,
            "monsters": copy.deepcopy(monsters),
        })

    return atb_log


def _collect_debug_tick(
    debug_snapshots: Optional[List[Dict[str, Any]]],
    tick_index: int,
    monsters: List[Dict[str, Any]],
    debug_ticks: int,
    debug_keys: Optional[set[str]],
) -> None:
    if debug_snapshots is None or debug_ticks <= 0:
        return
    if tick_index > debug_ticks:
        return
    for monster in monsters:
        key = monster.get("key")
        if debug_keys and key not in debug_keys:
            continue
        debug_snapshots.append({
            "tick": tick_index,
            "key": key,
            "isAlly": monster.get("isAlly"),
            "attack_bar": monster.get("attack_bar"),
            "combat_speed": monster.get("combat_speed"),
            "has_speed_buff": monster.get("has_speed_buff"),
            "has_slow": monster.get("has_slow"),
            "turn": monster.get("turn"),
        })


def apply_overrides(base_monsters: List[Dict[str, Any]], overrides: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    monsters = copy.deepcopy(base_monsters)
    for monster in monsters:
        override = overrides.get(monster.get("key"))
        if not override:
            continue
        monster.update({
            "rune_speed": override.get("rune_speed", monster.get("rune_speed", 0)),
            "speedIncreasingEffect": override.get(
                "speedIncreasingEffect",
                monster.get("speedIncreasingEffect", 0),
            ),
        })
    return monsters


def calculate_combat_speed(monster: Dict[str, Any]) -> int:
    speed = monster["base_speed"] * (100 + monster["tower_buff"] + monster["lead"]) / 100
    speed += monster.get("rune_speed", 0)

    for flat_speed_buff in monster.get("flatSpeedBuffs", []):
        buff_type = flat_speed_buff.get("type")
        amount = float(flat_speed_buff.get("flatSpeedBuffAmount", 0))
        if buff_type == "add":
            speed += amount
        elif buff_type == "add_percent":
            speed += amount / 100 * monster["base_speed"]
        elif buff_type == "subtract":
            speed -= amount
        elif buff_type == "subtract_percent":
            speed *= 1 - amount / 100

    if monster.get("has_slow"):
        speed *= 0.7

    if monster.get("has_speed_buff"):
        effect = monster.get("speedIncreasingEffect", 0)
        speed *= 1 + 0.3 * (100 + effect) / 100

    return math.ceil(speed)


def transform_monster(simulator: Dict[str, Any], base_monster: Dict[str, Any]) -> Dict[str, Any]:
    if base_monster.get("isAlly"):
        lead = simulator["allyEffects"].get("lead", 0)
        if simulator["allyEffects"].get("element") and simulator["allyEffects"].get("element") != base_monster.get("element"):
            lead = 0
    else:
        lead = simulator["enemyEffects"].get("lead", 0)
        if simulator["enemyEffects"].get("element") and simulator["enemyEffects"].get("element") != base_monster.get("element"):
            lead = 0

    monster = {
        "key": base_monster.get("key"),
        "name": base_monster.get("name"),
        "base_key": base_monster.get("base_key", base_monster.get("key")),
        "isAlly": base_monster.get("isAlly"),
        "combat_speed": 0,
        "tower_buff": simulator["allyEffects"].get("tower", 0)
        if base_monster.get("isAlly")
        else simulator["enemyEffects"].get("tower", 0),
        "lead": lead,
        "base_speed": base_monster.get("base_speed", 0),
        "rune_speed": base_monster.get("rune_speed", 0),
        "has_speed_buff": False,
        "speedIncreasingEffect": base_monster.get("speedIncreasingEffect", 0),
        "speedBuffDuration": 0,
        "has_slow": False,
        "isSwift": False,
        "slowDuration": 0,
        "flatSpeedBuffs": [],
        "skills": base_monster.get("skills", []),
        "attack_bar": 0,
        "turn": 0,
        "element": base_monster.get("element"),
        "tookTurn": False,
        "image": base_monster.get("image"),
    }
    monster["combat_speed"] = calculate_combat_speed(monster)
    return monster


def run_tick(
    simulator: Dict[str, Any],
    monsters: List[Dict[str, Any]],
    tick_index: int,
    turn_events: Optional[List[Dict[str, Any]]] = None,
    atb_log: Optional[List[Dict[str, Any]]] = None,
    atb_log_keys: Optional[List[str]] = None,
    atb_log_labels: Optional[Dict[str, str]] = None,
    atb_log_names: Optional[Dict[str, str]] = None,
) -> List[Dict[str, Any]]:
    if len(simulator["ticks"]) == 1:
        for i, monster in enumerate(monsters):
            actual_monster = find_base_monster(simulator, monster)
            if not actual_monster:
                continue
            skills = [skill for skill in actual_monster.get("skills", []) if skill.get("applyOnTurn") == 0]
            skill_targets = get_skill_targets(skills, monsters, i)
            apply_skill_effects(monsters, skills, skill_targets)

    for monster in monsters:
        monster["combat_speed"] = calculate_combat_speed(monster)
        monster["attack_bar"] += monster["combat_speed"] * 0.07
        monster["tookTurn"] = False

    move_index = get_monster_that_moves(monsters)
    actor_key = monsters[move_index].get("key") if move_index is not None else None
    actor_label = atb_log_labels.get(actor_key) if atb_log_labels and actor_key else None
    actual_monster = find_base_monster(simulator, monsters[move_index]) if move_index is not None else None
    skills = []
    if actual_monster:
        skills = [
            skill for skill in actual_monster.get("skills", [])
            if skill.get("applyOnTurn") == monsters[move_index]["turn"] or skill.get("applyOnTurn") == -1
        ]
    skill_targets = get_skill_targets(skills, monsters, move_index) if move_index is not None else []
    ally_atb_low_target = None
    for skill, targets in zip(skills, skill_targets):
        if skill.get("target") == "ally_atb_low" and targets:
            ally_atb_low_target = monsters[targets[0]].get("key")
            break
    if atb_log is not None and atb_log_keys:
        atb_snapshot = {}
        combat_snapshot = {}
        for key in atb_log_keys:
            monster = next((item for item in monsters if item.get("key") == key), None)
            atb_snapshot[key] = monster.get("attack_bar") if monster else None
            combat_snapshot[key] = monster.get("combat_speed") if monster else None
        speed_buff_keys = [monster.get("key") for monster in monsters if monster.get("has_speed_buff")]
        atb_log.append({
            "tick": tick_index,
            "atb": atb_snapshot,
            "v_combat": combat_snapshot,
            "actor_key": actor_key,
            "actor_label": actor_label,
            "speed_buff_keys": speed_buff_keys,
            "ally_atb_low_target": ally_atb_low_target,
            "ally_atb_low_target_name": atb_log_names.get(ally_atb_low_target) if atb_log_names else None,
        })
    if move_index is not None:
        monsters[move_index]["turn"] += 1
        if turn_events is not None:
            turn_events.append({
                "tick": tick_index,
                "key": monsters[move_index].get("key"),
                "base_key": monsters[move_index].get("base_key", monsters[move_index].get("key")),
                "name": monsters[move_index].get("name"),
                "isAlly": monsters[move_index].get("isAlly"),
                "turn_number": monsters[move_index].get("turn"),
                "attack_bar_before_reset": monsters[move_index].get("attack_bar"),
                "combat_speed": monsters[move_index].get("combat_speed"),
            })
        monsters[move_index]["attack_bar"] = 0

        if monsters[move_index].get("has_speed_buff"):
            monsters[move_index]["speedBuffDuration"] -= 1
            monsters[move_index]["has_speed_buff"] = monsters[move_index]["speedBuffDuration"] > 0
        if monsters[move_index].get("has_slow"):
            monsters[move_index]["slowDuration"] -= 1
            monsters[move_index]["has_slow"] = monsters[move_index]["slowDuration"] > 0
        for buff in monsters[move_index].get("flatSpeedBuffs", []):
            buff["flatSpeedBuffDuration"] -= 1
        monsters[move_index]["flatSpeedBuffs"] = [
            buff for buff in monsters[move_index].get("flatSpeedBuffs", [])
            if buff.get("flatSpeedBuffDuration", 0) > 0
        ]

        apply_skill_effects(monsters, skills, skill_targets)
        monsters[move_index]["tookTurn"] = True

    return monsters


def get_monster_that_moves(monsters: List[Dict[str, Any]]) -> Optional[int]:
    candidate_index = None
    candidate_attack_bar = None
    for idx, monster in enumerate(monsters):
        if monster.get("attack_bar", 0) < 100:
            continue
        attack_bar = monster.get("attack_bar", 0)
        if candidate_index is None or attack_bar > candidate_attack_bar:
            candidate_index = idx
            candidate_attack_bar = attack_bar
        elif attack_bar == candidate_attack_bar and idx < candidate_index:
            candidate_index = idx
    return candidate_index


def apply_skill_effects(
    monsters: List[Dict[str, Any]],
    skills: List[Dict[str, Any]],
    targets: List[List[int]],
) -> None:
    for skill_index, skill in enumerate(skills):
        target_indexes = targets[skill_index] if skill_index < len(targets) else []
        for target_index in target_indexes:
            if target_index < 0 or target_index >= len(monsters):
                continue
            if skill.get("atbManipulationType") == "add":
                monsters[target_index]["attack_bar"] += skill.get("atbManipulationAmount", 0)
            elif skill.get("atbManipulationType") == "subtract":
                monsters[target_index]["attack_bar"] -= skill.get("atbManipulationAmount", 0)
            elif skill.get("atbManipulationType") == "set":
                monsters[target_index]["attack_bar"] = skill.get("atbManipulationAmount", 0)

            if skill.get("buffSpeed"):
                monsters[target_index]["has_speed_buff"] = True
                monsters[target_index]["speedBuffDuration"] = skill.get("speedBuffDuration", 0)
            if skill.get("stripSpeed"):
                monsters[target_index]["has_speed_buff"] = False
                monsters[target_index]["speedBuffDuration"] = 0
            if skill.get("flatSpeedBuff"):
                monsters[target_index]["flatSpeedBuffs"].append({
                    "type": skill.get("flatSpeedBuffType"),
                    "flatSpeedBuffAmount": skill.get("flatSpeedBuffAmount", 0),
                    "flatSpeedBuffDuration": skill.get("flatSpeedBuffDuration", 0),
                })
            if skill.get("slow"):
                monsters[target_index]["has_slow"] = True
                monsters[target_index]["slowDuration"] = skill.get("slowDuration", 0)


def get_skill_targets(
    skills: List[Dict[str, Any]],
    monsters: List[Dict[str, Any]],
    self_idx: int,
) -> List[List[int]]:
    skill_targets: List[List[int]] = []
    for skill in skills:
        targets: List[int] = []
        target_type = skill.get("target")
        if target_type == "allies":
            targets = [index for index, item in enumerate(monsters) if item.get("isAlly")]
        elif target_type == "enemies":
            targets = [index for index, item in enumerate(monsters) if not item.get("isAlly")]
        elif target_type == "self":
            targets = [self_idx]
        elif target_type == "ally_atb_high":
            allies = [(m, idx) for idx, m in enumerate(monsters) if m.get("isAlly")]
            if allies:
                best = max(allies, key=lambda item: item[0].get("attack_bar", 0))
                targets = [best[1]]
        elif target_type == "ally_atb_low":
            allies = [(m, idx) for idx, m in enumerate(monsters) if m.get("isAlly")]
            if allies:
                best = min(
                    allies,
                    key=lambda item: (
                        item[0].get("attack_bar", 0),
                        item[0].get("ally_index", item[1]),
                    ),
                )
                targets = [best[1]]
        elif target_type == "enemy_atb_high":
            enemies = [(m, idx) for idx, m in enumerate(monsters) if not m.get("isAlly")]
            if enemies:
                best = max(enemies, key=lambda item: item[0].get("attack_bar", 0))
                targets = [best[1]]
        elif target_type == "enemy_atb_low":
            enemies = [(m, idx) for idx, m in enumerate(monsters) if not m.get("isAlly")]
            if enemies:
                best = min(enemies, key=lambda item: item[0].get("attack_bar", 0))
                targets = [best[1]]
        else:
            target_index = next(
                (index for index, item in enumerate(monsters) if item.get("key") == target_type),
                None,
            )
            if target_index is not None:
                targets = [target_index]

        skill_targets.append(targets)
    return skill_targets


def find_base_monster(simulator: Dict[str, Any], monster: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    source = simulator["allies"] if monster.get("isAlly") else simulator["enemies"]
    return next((item for item in source if item.get("key") == monster.get("key")), None)
