from typing import Any, Dict
import copy

### EDIT HERE: ATB SIMULATOR MONSTER DEFINITIONS ###

ATB_MONSTER_LIBRARY = {
    "swift_support": {
        "key": "swift_support",
        "name": "Swift Support",
        "monster_family": "Fairy",
        "element": "Wind",
        "base_speed": 115,
        "rune_speed": 0,
        "isSwift": True,
        "speedIncreasingEffect": 0,
        # NOTE: Avoid targeting monsters by raw key in skills when using the UI prefixing.
        "skills": [
            {
                "applyOnTurn": 1,
                "target": "allies",
                "atbManipulationType": "add",
                "atbManipulationAmount": 15,
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
    },
}

### EDIT HERE: ATB SIMULATOR PRESET DEFINITIONS ###

_DEFAULT_EFFECTS = {
    "tower": 0,
    "lead": 0,
    "element": None,
}

ATB_SIMULATOR_PRESETS = {
    "Preset A": {
        "allies": {
            "monsters": ["damage_dealer", "swift_support", "enemy_target"],
            "effects": dict(_DEFAULT_EFFECTS),
        },
        "enemies": {
            "monsters": ["damage_dealer", "swift_support", "enemy_target"],
            "effects": dict(_DEFAULT_EFFECTS),
        },
        "tickCount": 100,
    },
    "Preset B": {
        "allies": {
            "monsters": ["damage_dealer", "swift_support", "enemy_target"],
            "effects": dict(_DEFAULT_EFFECTS),
        },
        "enemies": {
            "monsters": ["damage_dealer", "swift_support", "enemy_target"],
            "effects": dict(_DEFAULT_EFFECTS),
        },
        "tickCount": 100,
    },
    "Preset C": {
        "allies": {
            "monsters": ["damage_dealer", "swift_support", "enemy_target"],
            "effects": dict(_DEFAULT_EFFECTS),
        },
        "enemies": {
            "monsters": ["damage_dealer", "swift_support", "enemy_target"],
            "effects": dict(_DEFAULT_EFFECTS),
        },
        "tickCount": 100,
    },
    "Preset D": {
        "allies": {
            "monsters": ["damage_dealer", "swift_support", "enemy_target"],
            "effects": dict(_DEFAULT_EFFECTS),
        },
        "enemies": {
            "monsters": ["damage_dealer", "swift_support", "enemy_target"],
            "effects": dict(_DEFAULT_EFFECTS),
        },
        "tickCount": 100,
    },
    "Preset E": {
        "allies": {
            "monsters": ["damage_dealer", "swift_support", "enemy_target"],
            "effects": dict(_DEFAULT_EFFECTS),
        },
        "enemies": {
            "monsters": ["damage_dealer", "swift_support", "enemy_target"],
            "effects": dict(_DEFAULT_EFFECTS),
        },
        "tickCount": 100,
    },
    "Preset F": {
        "allies": {
            "monsters": ["damage_dealer", "swift_support", "enemy_target"],
            "effects": dict(_DEFAULT_EFFECTS),
        },
        "enemies": {
            "monsters": ["damage_dealer", "swift_support", "enemy_target"],
            "effects": dict(_DEFAULT_EFFECTS),
        },
        "tickCount": 100,
    },
    "Preset G": {
        "allies": {
            "monsters": ["damage_dealer", "swift_support", "enemy_target"],
            "effects": dict(_DEFAULT_EFFECTS),
        },
        "enemies": {
            "monsters": ["damage_dealer", "swift_support", "enemy_target"],
            "effects": dict(_DEFAULT_EFFECTS),
        },
        "tickCount": 100,
    },
}

### ATB SIMULATOR ALLY/ENEMY PRESET LISTS (DERIVED) ###

ATB_SIMULATOR_ALLY_PRESETS = {
    f"Ally {preset_id}": {
        "monsters": preset.get("allies", {}).get("monsters", []),
        "effects": preset.get("allies", {}).get("effects", {}),
        "tickCount": preset.get("tickCount", 0),
    }
    for preset_id, preset in ATB_SIMULATOR_PRESETS.items()
}

ATB_SIMULATOR_ENEMY_PRESETS = {
    f"Enemy {preset_id}": {
        "monsters": preset.get("enemies", {}).get("monsters", []),
        "effects": preset.get("enemies", {}).get("effects", {}),
        "tickCount": preset.get("tickCount", 0),
    }
    for preset_id, preset in ATB_SIMULATOR_PRESETS.items()
}


def build_monsters_for_keys(monster_keys: list[str], is_ally: bool) -> list[Dict[str, Any]]:
    return [_build_monster_from_library(key, is_ally=is_ally) for key in monster_keys]


def build_full_preset(preset_id: str) -> Dict[str, Any]:
    if preset_id not in ATB_SIMULATOR_PRESETS:
        raise ValueError(
            f"Preset '{preset_id}' not found. Please edit config/atb_simulator_presets.py."
        )

    preset_meta = ATB_SIMULATOR_PRESETS[preset_id]
    ally_meta = preset_meta.get("allies", {})
    enemy_meta = preset_meta.get("enemies", {})

    ally_keys = ally_meta.get("monsters", [])
    enemy_keys = enemy_meta.get("monsters", [])
    if len(ally_keys) != 3:
        raise ValueError(
            f"Preset '{preset_id}' must define exactly 3 ally monster keys."
        )
    if len(enemy_keys) < 1:
        raise ValueError(
            f"Preset '{preset_id}' must define at least 1 enemy monster key."
        )

    return {
        "allies": build_monsters_for_keys(ally_keys, is_ally=True),
        "enemies": build_monsters_for_keys(enemy_keys, is_ally=False),
        "allyEffects": ally_meta.get("effects", {}),
        "enemyEffects": enemy_meta.get("effects", {}),
        "tickCount": preset_meta.get("tickCount", 0),
    }


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
