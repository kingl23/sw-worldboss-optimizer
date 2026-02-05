from typing import Any, Dict
import copy

### EDIT HERE: ATB SIMULATOR MONSTER DEFINITIONS ###

ATB_MONSTER_LIBRARY = {
    "light_warewolf": {
        "key": "light_warewolf",
        "name": "light_warewolf",
        "element": "Light",
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
    "water_pumpkin": {
        "key": "water_pumpkin",
        "name": "water_pumpkin",
        "element": "Water",
        "base_speed": 101,
        "rune_speed": 0,
        "isSwift": True,
        "speedIncreasingEffect": 0,
        # NOTE: Avoid targeting monsters by raw key in skills when using the UI prefixing.
        "skills": [
            {
                "applyOnTurn": 1,
                "target": "allies",
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
    "water_pudding": {
        "key": "water_pudding",
        "name": "water_pudding",
        "element": "Water",
        "base_speed": 111,
        "rune_speed": 0,
        "isSwift": True,
        "speedIncreasingEffect": 0,
        # NOTE: Avoid targeting monsters by raw key in skills when using the UI prefixing.
        "skills": [
            {
                "applyOnTurn": 1,
                "target": "allies",
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
    "dark_geomungo": {
        "key": "dark_geomungo",
        "name": "dark_geomungo",
        "element": "Dark",
        "base_speed": 107,
        "rune_speed": 0,
        "isSwift": True,
        "speedIncreasingEffect": 0,
        # NOTE: Avoid targeting monsters by raw key in skills when using the UI prefixing.
        "skills": [
            {
                "applyOnTurn": 1,
                "target": "allies",
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
    "dark_harg": {
        "key": "dark_harg",
        "name": "dark_harg",
        "element": "Dark",
        "base_speed": 120,
        "rune_speed": 0,
        "isSwift": True,
        "speedIncreasingEffect": 0,
        # NOTE: Avoid targeting monsters by raw key in skills when using the UI prefixing.
        "skills": [
            {
                "applyOnTurn": 1,
                "target": "ally_atb_low",
                "atbManipulationType": "add",
                "atbManipulationAmount": 15,
                "stripSpeed": False,
                "flatSpeedBuff": False,
                "flatSpeedBuffType": None,
                "flatSpeedBuffAmount": 0,
                "flatSpeedBuffDuration": 0,
                "slow": False,
                "slowDuration": 0,
            },
            {
                "applyOnTurn": 1,
                "target": "allies",
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
    "water_pirate": {
        "key": "water_pirate",
        "name": "water_pirate",
        "element": "Water",
        "base_speed": 108,
        "rune_speed": 0,
        "isSwift": False,
        "speedIncreasingEffect": 0,
    },
    "fire_mermaid": {
        "key": "fire_mermaid",
        "name": "fire_mermaid",
        "element": "Fire",
        "base_speed": 95,
        "rune_speed": 0,
        "isSwift": False,
        "speedIncreasingEffect": 0,
    },
    "light_archer": {
        "key": "light_archer",
        "name": "light_archer",
        "element": "Light",
        "base_speed": 105,
        "rune_speed": 0,
        "isSwift": False,
        "speedIncreasingEffect": 0,
    },
    "dark_archer": {
        "key": "dark_archer",
        "name": "dark_archer",
        "element": "Dark",
        "base_speed": 120,
        "rune_speed": 0,
        "isSwift": False,
        "speedIncreasingEffect": 0,
    },
    "water_dancer": {
        "key": "water_dancer",
        "name": "water_dancer",
        "element": "Water",
        "base_speed": 101,
        "rune_speed": 220,
        "isSwift": False,
        "speedIncreasingEffect": 22,
    },
    "water_ciri": {
        "key": "water_ciri",
        "name": "water_ciri",
        "element": "Water",
        "base_speed": 106,
        "rune_speed": 220,
        "isSwift": False,
        "speedIncreasingEffect": 22,
    },
    "fire_centa": {
        "key": "fire_centa",
        "name": "fire_centa",
        "element": "Fire",
        "base_speed": 104,
        "rune_speed": 220,
        "isSwift": False,
        "speedIncreasingEffect": 44,
    },
    "fire_twin": {
        "key": "fire_twin",
        "name": "fire_twin",
        "element": "Fire",
        "base_speed": 102,
        "rune_speed": 0,
        "isSwift": False,
        "speedIncreasingEffect": 0,
    },
    "wind_pala": {
        "key": "wind_pala",
        "name": "wind_pala",
        "element": "Wind",
        "base_speed": 102,
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
            "monsters": ["fire_mermaid", "water_pumpkin", "dark_archer"],
            "effects": dict(_DEFAULT_EFFECTS),
        },
        "enemies": {
            "monsters": ["fire_mermaid", "water_pumpkin", "dark_archer"],
            "effects": dict(_DEFAULT_EFFECTS),
        },
        "tickCount": 100,
    },
    "Preset B": {
        "allies": {
            "monsters": ["water_pirate", "water_pumpkin", "light_archer"],
            "effects": dict(_DEFAULT_EFFECTS),
        },
        "enemies": {
            "monsters": ["water_pirate", "water_pumpkin", "light_archer"],
            "effects": dict(_DEFAULT_EFFECTS),
        },
        "tickCount": 100,
    },
    "Preset C": {
        "allies": {
            "monsters": ["water_dancer", "light_warewolf", "fire_twin"],
            "effects": dict(_DEFAULT_EFFECTS),
        },
        "enemies": {
            "monsters": ["water_dancer", "light_warewolf", "fire_twin"],
            "effects": dict(_DEFAULT_EFFECTS),
        },
        "tickCount": 100,
    },
    "Preset D": {
        "allies": {
            "monsters": ["water_dancer", "water_pudding", "fire_twin"],
            "effects": dict(_DEFAULT_EFFECTS),
        },
        "enemies": {
            "monsters": ["water_dancer", "water_pudding", "fire_twin"],
            "effects": dict(_DEFAULT_EFFECTS),
        },
        "tickCount": 100,
    },
    "Preset E": {
        "allies": {
            "monsters": ["water_dancer", "dark_harg", "fire_twin"],
            "effects": dict(_DEFAULT_EFFECTS),
        },
        "enemies": {
            "monsters": ["water_dancer", "dark_harg", "fire_twin"],
            "effects": dict(_DEFAULT_EFFECTS),
        },
        "tickCount": 100,
    },
    "Preset F": {
        "allies": {
            "monsters": ["dark_geomungo", "water_ciri", "fire_twin"],
            "effects": dict(_DEFAULT_EFFECTS),
        },
        "enemies": {
            "monsters": ["dark_geomungo", "water_ciri", "fire_twin"],
            "effects": dict(_DEFAULT_EFFECTS),
        },
        "tickCount": 100,
    },
    "Preset G": {
        "allies": {
            "monsters": ["dark_geomungo", "fire_centa", "wind_pala"],
            "effects": dict(_DEFAULT_EFFECTS),
        },
        "enemies": {
            "monsters": ["dark_geomungo", "fire_centa", "wind_pala"],
            "effects": dict(_DEFAULT_EFFECTS),
        },
        "tickCount": 100,
    },
}

LEADER_PERCENT_BY_PRESET = {
    "Preset A": 24,
    "Preset B": 24,
    "Preset C": 28,
    "Preset D": 28,
    "Preset E": 28,
    "Preset F": 28,
    "Preset G": 24,
}
TOWER_PERCENT = 15


def get_leader_percent(preset_id: str) -> int:
    resolved_id = preset_id.replace("Ally ", "").replace("Enemy ", "")
    return LEADER_PERCENT_BY_PRESET.get(resolved_id, 0)


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

    leader_percent = get_leader_percent(preset_id)
    ally_effects = dict(ally_meta.get("effects", {}))
    enemy_effects = dict(enemy_meta.get("effects", {}))
    ally_effects["tower"] = TOWER_PERCENT
    ally_effects["lead"] = leader_percent
    enemy_effects["tower"] = TOWER_PERCENT
    enemy_effects["lead"] = leader_percent

    return {
        "allies": build_monsters_for_keys(ally_keys, is_ally=True),
        "enemies": build_monsters_for_keys(enemy_keys, is_ally=False),
        "allyEffects": ally_effects,
        "enemyEffects": enemy_effects,
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

    effects = dict(preset_meta.get("effects", {}))
    effects["tower"] = TOWER_PERCENT
    effects["lead"] = get_leader_percent(preset_id)
    return {
        "monsters": build_monsters_for_keys(keys, is_ally=True),
        "effects": effects,
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

    effects = dict(preset_meta.get("effects", {}))
    effects["tower"] = TOWER_PERCENT
    effects["lead"] = get_leader_percent(preset_id)
    return {
        "monsters": build_monsters_for_keys(keys, is_ally=False),
        "effects": effects,
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
