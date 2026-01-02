from typing import Any, Dict

### EDIT HERE: ATB SIMULATOR MONSTER DEFINITIONS ###

ATB_MONSTER_LIBRARY = {
    "swift_support": {
        "key": "swift_support",
        "name": "Swift Support",
        "monster_family": "Fairy",
        "element": "Wind",
        "base_speed": 100,
        "rune_speed": 0,
        "isSwift": True,
        "speedIncreasingEffect": 0,
        # NOTE: Avoid targeting monsters by raw key in skills when using the UI prefixing.
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
    "damage_dealer": {
        "key": "damage_dealer",
        "name": "Damage Dealer",
        "monster_family": "Warrior",
        "element": "Fire",
        "base_speed": 98,
        "rune_speed": 0,
        "isSwift": False,
        "speedIncreasingEffect": 0,
        # NOTE: Avoid targeting monsters by raw key in skills when using the UI prefixing.
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
    "enemy_target": {
        "key": "enemy_target",
        "name": "Enemy Target",
        "monster_family": "Knight",
        "element": "Water",
        "base_speed": 95,
        "rune_speed": 0,
        "isSwift": False,
        "speedIncreasingEffect": 0,
        # NOTE: Avoid targeting monsters by raw key in skills when using the UI prefixing.
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
    },
}

### EDIT HERE: ATB SIMULATOR ALLY PRESET TRIOS ###

ATB_SIMULATOR_ALLY_PRESETS = {
    "Ally Preset A": {
        "monsters": ["swift_support", "damage_dealer", "enemy_target"],
        "effects": {
            "tower": 0,
            "lead": 0,
            "element": None,
        },
        "tickCount": 10,
    },
}

### EDIT HERE: ATB SIMULATOR ENEMY PRESET TRIOS ###

ATB_SIMULATOR_ENEMY_PRESETS = {
    "Enemy Preset A": {
        "monsters": ["swift_support", "damage_dealer", "enemy_target"],
        "effects": {
            "tower": 0,
            "lead": 0,
            "element": None,
        },
        "tickCount": 10,
    },
}


def build_monsters_for_keys(monster_keys: list[str], is_ally: bool) -> list[Dict[str, Any]]:
    return [_build_monster_from_library(key, is_ally=is_ally) for key in monster_keys]


def build_ally_preset(preset_id: str) -> Dict[str, Any]:
    if preset_id not in ATB_SIMULATOR_ALLY_PRESETS:
        raise ValueError(
            f"Ally preset '{preset_id}' not found. Please edit config/atb_simulator_presets.py."
        )

    preset_meta = ATB_SIMULATOR_ALLY_PRESETS[preset_id]
    keys = preset_meta.get("monsters", [])
    if len(keys) != 3:
        raise ValueError(
            f"Ally preset '{preset_id}' must define exactly 3 monster keys."
        )

    return {
        "monsters": build_monsters_for_keys(keys, is_ally=True),
        "effects": preset_meta.get("effects", {}),
        "tickCount": preset_meta.get("tickCount", 0),
    }


def build_enemy_preset(preset_id: str) -> Dict[str, Any]:
    if preset_id not in ATB_SIMULATOR_ENEMY_PRESETS:
        raise ValueError(
            f"Enemy preset '{preset_id}' not found. Please edit config/atb_simulator_presets.py."
        )

    preset_meta = ATB_SIMULATOR_ENEMY_PRESETS[preset_id]
    keys = preset_meta.get("monsters", [])
    if len(keys) != 3:
        raise ValueError(
            f"Enemy preset '{preset_id}' must define exactly 3 monster keys."
        )

    return {
        "monsters": build_monsters_for_keys(keys, is_ally=False),
        "effects": preset_meta.get("effects", {}),
        "tickCount": preset_meta.get("tickCount", 0),
    }


def _build_monster_from_library(key: str, is_ally: bool) -> Dict[str, Any]:
    if key not in ATB_MONSTER_LIBRARY:
        raise ValueError(
            f"Monster key '{key}' not found in ATB_MONSTER_LIBRARY. "
            "Please edit config/atb_simulator_presets.py."
        )

    monster = copy.deepcopy(ATB_MONSTER_LIBRARY[key])
    monster["isAlly"] = is_ally
    return monster
