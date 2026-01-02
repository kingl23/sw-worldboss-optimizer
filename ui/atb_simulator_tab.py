import copy
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

from config.atb_simulator_presets import (
    ATB_SIMULATOR_ALLY_PRESETS,
    ATB_SIMULATOR_ENEMY_PRESETS,
    build_ally_preset,
    build_enemy_preset,
    build_monsters_for_keys,
)
from domain.atb_simulator import simulate_with_turn_log


def render_atb_simulator_tab() -> None:
    st.subheader("ATB Simulator")
    st.markdown(
        """
This tab runs a Summoners War style ATB tick simulation.

**Preset data lives in** `config/atb_simulator_presets.py` and can be edited directly.
"""
    )

    if not ATB_SIMULATOR_ALLY_PRESETS:
        st.warning("No ally presets found. Please edit config/atb_simulator_presets.py.")
        st.stop()

    ally_preset_ids = list(ATB_SIMULATOR_ALLY_PRESETS.keys())
    ally_preset_id = st.selectbox("Ally preset", options=ally_preset_ids)
    try:
        ally_preset = build_ally_preset(ally_preset_id)
    except ValueError as exc:
        st.warning(str(exc))
        st.stop()

    ally_monsters = ally_preset["monsters"]
    ally_overrides = _render_monster_overrides(
        "Allies",
        ally_monsters,
        prefix="ally",
    )

    st.caption("Enemy preset defaults to mirroring the Ally trio and overrides.")
    enemy_preset_ids = list(ATB_SIMULATOR_ENEMY_PRESETS.keys())
    enemy_options = ["Default"] + enemy_preset_ids
    enemy_selection = st.selectbox("Enemy preset", options=enemy_options, index=0)

    if enemy_selection == "Default":
        enemy_keys = [monster.get("key") for monster in ally_monsters]
        enemy_monsters = build_monsters_for_keys(enemy_keys, is_ally=False)
        st.caption("Enemy values are mirrored from Allies when using Default.")
        _render_monster_overrides(
            "Enemies",
            enemy_monsters,
            prefix="enemy_default",
            defaults=ally_overrides,
            disabled=True,
        )
        enemy_overrides = copy.deepcopy(ally_overrides)
        enemy_preset = {
            "monsters": enemy_monsters,
            "effects": ally_preset.get("effects", {}),
            "tickCount": ally_preset.get("tickCount", 0),
        }
    else:
        if not ATB_SIMULATOR_ENEMY_PRESETS:
            st.warning("No enemy presets found. Please edit config/atb_simulator_presets.py.")
            st.stop()
        try:
            enemy_preset = build_enemy_preset(enemy_selection)
        except ValueError as exc:
            st.warning(str(exc))
            st.stop()
        enemy_monsters = enemy_preset["monsters"]
        enemy_overrides = _render_monster_overrides(
            "Enemies",
            enemy_monsters,
            prefix="enemy",
        )

    st.caption(
        "When using per-monster key targets in skills, note that the UI prefixes keys per side."
    )

    prefixed_allies, ally_key_map = _prefix_monsters(ally_monsters, prefix="A")
    prefixed_enemies, enemy_key_map = _prefix_monsters(enemy_monsters, prefix="E")

    overrides: Dict[str, Dict[str, Any]] = {}
    for key, values in ally_overrides.items():
        overrides[ally_key_map[key]] = values
    for key, values in enemy_overrides.items():
        overrides[enemy_key_map[key]] = values

    preset = {
        "allies": prefixed_allies,
        "enemies": prefixed_enemies,
        "allyEffects": ally_preset.get("effects", {}),
        "enemyEffects": enemy_preset.get("effects", {}),
        "tickCount": ally_preset.get("tickCount", 0),
    }

    _, turn_events = simulate_with_turn_log(preset, overrides)
    if not turn_events:
        st.warning("No turn events were recorded. Please verify the preset data.")
        st.stop()

    max_turns = st.number_input("Max turns to display", min_value=1, value=20, step=1)

    rows = []
    for event in turn_events[:max_turns]:
        rows.append({
            "tick": event.get("tick"),
            "side": "Ally" if event.get("isAlly") else "Enemy",
            "key": event.get("base_key"),
            "turn_number_for_that_monster": event.get("turn_number"),
        })

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _render_monster_overrides(
    title: str,
    monsters: List[Dict[str, Any]],
    prefix: str,
    defaults: Dict[str, Dict[str, Any]] | None = None,
    disabled: bool = False,
) -> Dict[str, Dict[str, Any]]:
    st.markdown(f"### {title}")
    overrides: Dict[str, Dict[str, Any]] = {}
    columns = st.columns(3)
    for index, monster in enumerate(monsters):
        key = monster.get("key")
        name = monster.get("name") or key
        default_values = (defaults or {}).get(key, {})
        rune_speed_key = f"{prefix}_{key}_rune_speed"
        speed_effect_key = f"{prefix}_{key}_speed_increasing_effect"
        if disabled:
            st.session_state[rune_speed_key] = int(default_values.get("rune_speed", 0))
            st.session_state[speed_effect_key] = int(default_values.get("speedIncreasingEffect", 0))
        with columns[index % 3]:
            st.markdown(f"**{name}** (`{key}`)")
            rune_speed = st.number_input(
                "Rune speed",
                min_value=0,
                max_value=400,
                value=int(default_values.get("rune_speed", 0)),
                step=1,
                key=rune_speed_key,
                disabled=disabled,
            )
            speed_increasing_effect = st.number_input(
                "Speed increasing effect",
                min_value=0,
                max_value=200,
                value=int(default_values.get("speedIncreasingEffect", 0)),
                step=1,
                key=speed_effect_key,
                disabled=disabled,
            )
        overrides[key] = {
            "rune_speed": rune_speed,
            "speedIncreasingEffect": speed_increasing_effect,
        }
    return overrides


def _prefix_monsters(
    monsters: List[Dict[str, Any]],
    prefix: str,
) -> tuple[list[Dict[str, Any]], Dict[str, str]]:
    key_map: Dict[str, str] = {}
    for monster in monsters:
        original_key = monster.get("key")
        if original_key:
            key_map[original_key] = f"{prefix}|{original_key}"

    prefixed = []
    for monster in monsters:
        original_key = monster.get("key")
        prefixed_monster = copy.deepcopy(monster)
        if original_key and original_key in key_map:
            prefixed_monster["base_key"] = original_key
            prefixed_monster["key"] = key_map[original_key]
        prefixed_monster["skills"] = _prefix_skill_targets(
            prefixed_monster.get("skills", []),
            key_map,
        )
        prefixed.append(prefixed_monster)

    return prefixed, key_map


def _prefix_skill_targets(
    skills: List[Dict[str, Any]],
    key_map: Dict[str, str],
) -> List[Dict[str, Any]]:
    updated = []
    for skill in skills:
        new_skill = copy.deepcopy(skill)
        target = new_skill.get("target")
        if target in key_map:
            new_skill["target"] = key_map[target]
        updated.append(new_skill)
    return updated
