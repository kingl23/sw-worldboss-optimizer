### EDIT HERE: ATB SIMULATOR PRESET DATA ###

ATB_SIMULATOR_PRESET = {
    # EDIT: Add/edit ally base monsters here.
    "allies": [
        {
            "key": "ally_1",
            "isAlly": True,
            "name": "Swift Support",
            "monster_family": "Fairy",
            "element": "Wind",
            "base_speed": 100,
            "rune_speed": 0,
            "isSwift": True,
            "speedIncreasingEffect": 0,
            "skills": [
                {
                    "applyOnTurn": 0,
                    "target": "allies",
                    "atbManipulationType": "add",
                    "atbManipulationAmount": 5,
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
        },
        {
            "key": "ally_2",
            "isAlly": True,
            "name": "Damage Dealer",
            "monster_family": "Warrior",
            "element": "Fire",
            "base_speed": 98,
            "rune_speed": 0,
            "isSwift": False,
            "speedIncreasingEffect": 0,
            "skills": [
                {
                    "applyOnTurn": -1,
                    "target": "enemy_atb_high",
                    "atbManipulationType": "subtract",
                    "atbManipulationAmount": 10,
                    "buffSpeed": False,
                    "speedBuffDuration": 0,
                    "stripSpeed": False,
                    "flatSpeedBuff": False,
                    "flatSpeedBuffType": None,
                    "flatSpeedBuffAmount": 0,
                    "flatSpeedBuffDuration": 0,
                    "slow": False,
                    "slowDuration": 0,
                }
            ],
        },
    ],
    # EDIT: Add/edit enemy base monsters here.
    "enemies": [
        {
            "key": "enemy_1",
            "isAlly": False,
            "name": "Enemy Target",
            "monster_family": "Knight",
            "element": "Water",
            "base_speed": 95,
            "rune_speed": 0,
            "isSwift": False,
            "speedIncreasingEffect": 0,
            "skills": [
                {
                    "applyOnTurn": -1,
                    "target": "self",
                    "atbManipulationType": "add",
                    "atbManipulationAmount": 0,
                    "buffSpeed": False,
                    "speedBuffDuration": 0,
                    "stripSpeed": False,
                    "flatSpeedBuff": True,
                    "flatSpeedBuffType": "add",
                    "flatSpeedBuffAmount": 0,
                    "flatSpeedBuffDuration": 0,
                    "slow": False,
                    "slowDuration": 0,
                }
            ],
        }
    ],
    # EDIT: Ally global effects (tower, lead, element).
    "allyEffects": {
        "tower": 0,
        "lead": 0,
        "element": None,
    },
    # EDIT: Enemy global effects (tower, lead, element).
    "enemyEffects": {
        "tower": 0,
        "lead": 0,
        "element": None,
    },
    # EDIT: Simulation tick count.
    "tickCount": 10,
    # EDIT: Simulation tick size. Leave 0 to use the default 0.07 behavior.
    "tickSize": 0,
}
