import copy
from typing import Any, Dict

### EDIT HERE: ATB SIMULATOR MONSTER DEFINITIONS ###

ATB_MONSTER_LIBRARY = {
    "swift_support": {
        "key": "swift_support",
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
    "damage_dealer": {
        "key": "damage_dealer",
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
    "enemy_target": {
        "key": "enemy_target",
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
    },
}

### EDIT HERE: ATB SIMULATOR PRESET TRIOS ###

ATB_SIMULATOR_PRESETS = {
    "Default Trio": {
        "allies": ["swift_support", "damage_dealer", "enemy_target"],
        "allyEffects": {
            "tower": 0,
            "lead": 0,
            "element": None,
        },
        "enemyEffects": {
            "tower": 0,
            "lead": 0,
            "element": None,
        },
        "tickCount": 10,
        "tickSize": 0,
    }
}


def build_atb_preset(preset_id: str) -> Dict[str, Any]:
    if preset_id not in ATB_SIMULATOR_PRESETS:
        raise ValueError(f"Preset '{preset_id}' not found. Please edit config/atb_simulator_presets.py.")

    preset_meta = ATB_SIMULATOR_PRESETS[preset_id]
    ally_keys = preset_meta.get("allies", [])
    if len(ally_keys) != 3:
        raise ValueError(
            f"Preset '{preset_id}' must define exactly 3 ally monster keys."
        )

    enemy_keys = preset_meta.get("enemies") or ally_keys
    if len(enemy_keys) != 3:
        raise ValueError(
            f"Preset '{preset_id}' must define exactly 3 enemy monster keys."
        )

    allies = [_build_monster_from_library(key, is_ally=True) for key in ally_keys]
    enemies = [_build_monster_from_library(key, is_ally=False) for key in enemy_keys]

    ally_effects = preset_meta.get("allyEffects", {})
    enemy_effects = preset_meta.get("enemyEffects") or copy.deepcopy(ally_effects)

    return {
        "allies": allies,
        "enemies": enemies,
        "allyEffects": ally_effects,
        "enemyEffects": enemy_effects,
        "tickCount": preset_meta.get("tickCount", 0),
        "tickSize": preset_meta.get("tickSize", 0),
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
