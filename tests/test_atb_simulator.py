import math

from config.atb_simulator_presets import ATB_MONSTER_LIBRARY
from domain.atb_simulator import (
    apply_skill_effects,
    calculate_combat_speed,
    get_skill_targets,
    simulate_atb_table,
    simulate_with_turn_log,
)


def test_swift_bonus_disabled():
    base_monster = {
        "base_speed": 100,
        "tower_buff": 0,
        "lead": 0,
        "rune_speed": 0,
        "flatSpeedBuffs": [],
        "has_slow": False,
        "has_speed_buff": False,
        "speedIncreasingEffect": 0,
    }
    swift_speed = calculate_combat_speed({**base_monster, "isSwift": True})
    non_swift_speed = calculate_combat_speed({**base_monster, "isSwift": False})
    assert swift_speed == non_swift_speed


def test_one_action_per_tick_and_tie_breaker():
    preset = {
        "allies": [
            {
                "key": "ally_1",
                "name": "ally_1",
                "isAlly": True,
                "base_speed": 1500,
                "rune_speed": 0,
                "isSwift": False,
                "speedIncreasingEffect": 0,
                "skills": [],
            }
        ],
        "enemies": [
            {
                "key": "enemy_1",
                "name": "enemy_1",
                "isAlly": False,
                "base_speed": 1500,
                "rune_speed": 0,
                "isSwift": False,
                "speedIncreasingEffect": 0,
                "skills": [],
            }
        ],
        "allyEffects": {},
        "enemyEffects": {},
        "tickCount": 1,
    }

    _, turn_events = simulate_with_turn_log(preset)
    assert len(turn_events) == 1
    assert turn_events[0]["tick"] == 1
    assert turn_events[0]["key"] == "ally_1"


def test_debug_atb_log_records_actor_and_values():
    preset = {
        "allies": [
            {
                "key": "ally_1",
                "name": "ally_1",
                "isAlly": True,
                "base_speed": 1500,
                "rune_speed": 0,
                "isSwift": False,
                "speedIncreasingEffect": 0,
                "skills": [],
            }
        ],
        "enemies": [
            {
                "key": "enemy_1",
                "name": "enemy_1",
                "isAlly": False,
                "base_speed": 1400,
                "rune_speed": 0,
                "isSwift": False,
                "speedIncreasingEffect": 0,
                "skills": [],
            }
        ],
        "allyEffects": {},
        "enemyEffects": {},
        "tickCount": 1,
    }

    atb_log = []
    simulate_with_turn_log(
        preset,
        debug_atb_log=atb_log,
        debug_atb_keys=["ally_1", "enemy_1"],
        debug_atb_labels={"ally_1": "A1", "enemy_1": "E"},
    )
    assert len(atb_log) == 1
    assert atb_log[0]["actor_label"] == "A1"
    assert atb_log[0]["atb"]["ally_1"] is not None


def test_combat_speed_uses_effect_multiplier():
    monster = {
        "base_speed": 100,
        "tower_buff": 15,
        "lead": 24,
        "rune_speed": 0,
        "flatSpeedBuffs": [],
        "has_slow": False,
        "has_speed_buff": True,
        "speedIncreasingEffect": 20,
    }
    v_total = 100 + (100 * (24 + 15) / 100)
    expected = v_total * (1 + 0.3 * (100 + 20) / 100)
    assert calculate_combat_speed(monster) == math.ceil(expected)


def test_dark_harg_skill_applies_atb_and_speed_buff():
    dark_harg = dict(ATB_MONSTER_LIBRARY["dark_harg"])
    skills = dark_harg.get("skills", [])
    monsters = [
        {
            "key": "a1",
            "name": "dark_harg",
            "isAlly": True,
            "attack_bar": 10,
            "ally_index": 0,
            "has_speed_buff": False,
            "speedBuffDuration": 0,
            "flatSpeedBuffs": [],
        },
        {
            "key": "a2",
            "name": "ally_two",
            "isAlly": True,
            "attack_bar": 5,
            "ally_index": 1,
            "has_speed_buff": False,
            "speedBuffDuration": 0,
            "flatSpeedBuffs": [],
        },
        {
            "key": "a3",
            "name": "ally_three",
            "isAlly": True,
            "attack_bar": 5,
            "ally_index": 2,
            "has_speed_buff": False,
            "speedBuffDuration": 0,
            "flatSpeedBuffs": [],
        },
    ]

    targets = get_skill_targets(skills, monsters, self_idx=0)
    apply_skill_effects(monsters, skills, targets)

    assert monsters[1]["attack_bar"] == 20
    assert monsters[2]["attack_bar"] == 5
    assert all(monster["has_speed_buff"] for monster in monsters)
    assert all(monster["speedBuffDuration"] == 2 for monster in monsters)
