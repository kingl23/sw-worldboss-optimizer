from domain.atb_simulator import calculate_combat_speed, simulate_atb_table, simulate_with_turn_log


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


def test_speed_buff_increases_combat_speed():
    preset = {
        "allies": [
            {
                "key": "ally_1",
                "name": "ally_1",
                "isAlly": True,
                "base_speed": 100,
                "rune_speed": 0,
                "isSwift": False,
                "speedIncreasingEffect": 0,
                "skills": [
                    {
                        "applyOnTurn": 1,
                        "target": "self",
                        "buffSpeed": True,
                        "speedBuffDuration": 2,
                        "stripSpeed": False,
                        "flatSpeedBuff": False,
                        "flatSpeedBuffType": None,
                        "flatSpeedBuffAmount": 0,
                        "flatSpeedBuffDuration": 0,
                        "slow": False,
                        "slowDuration": 0,
                    }
                ],
            }
        ],
        "enemies": [
            {
                "key": "enemy_1",
                "name": "enemy_1",
                "isAlly": False,
                "base_speed": 10,
                "rune_speed": 0,
                "isSwift": False,
                "speedIncreasingEffect": 0,
                "skills": [],
            }
        ],
        "allyEffects": {"lead": 0, "tower": 0},
        "enemyEffects": {"lead": 0, "tower": 0},
        "tickCount": 16,
    }

    atb_log = simulate_atb_table(
        preset,
        tick_limit=16,
        atb_keys=["ally_1", "enemy_1"],
        atb_labels={"ally_1": "A1", "enemy_1": "E"},
    )
    base_speed = atb_log[0]["v_combat"]["ally_1"]
    boosted = next(
        (row["v_combat"]["ally_1"] for row in atb_log if row["speed_buff"]["ally_1"]),
        None,
    )
    assert boosted is not None
    assert boosted == base_speed * 1.3
