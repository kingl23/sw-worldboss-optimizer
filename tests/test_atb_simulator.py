from domain.atb_simulator import calculate_combat_speed, simulate_with_turn_log


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
