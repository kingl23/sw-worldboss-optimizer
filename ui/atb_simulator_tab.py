import copy
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

from config.atb_simulator_presets import (
    ATB_SIMULATOR_PRESETS,
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

    if not ATB_SIMULATOR_PRESETS:
        st.warning("No ATB presets found. Please edit config/atb_simulator_presets.py.")
        st.stop()

    preset_ids = list(ATB_SIMULATOR_PRESETS.keys())
    ally_preset_id = st.selectbox("Ally preset", options=preset_ids)
    ally_meta = ATB_SIMULATOR_PRESETS.get(ally_preset_id, {})
    ally_keys = ally_meta.get("allies", [])
    if len(ally_keys) != 3:
        st.warning("Ally preset must define exactly 3 monster keys.")
        st.stop()

    st.caption("Enemy uses the same trio as Ally by default.")
    enemy_options = ["Same as Allies"] + preset_ids
    enemy_selection = st.selectbox("Enemy preset", options=enemy_options, index=0)

    ally_monsters = build_monsters_for_keys(ally_keys, is_ally=True)
    ally_overrides = _render_monster_overrides(
        "Allies",
        ally_monsters,
        prefix="ally",
    )

    if enemy_selection == "Same as Allies":
        enemy_keys = ally_keys
        enemy_monsters = build_monsters_for_keys(enemy_keys, is_ally=False)
        st.markdown("### Enemies")
        st.caption("Enemy overrides mirror the Ally values when using the same preset.")
        _render_monster_overrides(
            "Enemies (Same as Allies)",
            enemy_monsters,
            prefix="enemy",
            defaults=ally_overrides,
            disabled=True,
        )
        enemy_overrides = copy.deepcopy(ally_overrides)
        enemy_meta = ally_meta
    else:
        enemy_meta = ATB_SIMULATOR_PRESETS.get(enemy_selection, {})
        enemy_keys = enemy_meta.get("allies", [])
        if len(enemy_keys) != 3:
            st.warning("Enemy preset must define exactly 3 monster keys.")
            st.stop()
        enemy_monsters = build_monsters_for_keys(enemy_keys, is_ally=False)
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
        "allyEffects": ally_meta.get("allyEffects", {}),
        "enemyEffects": enemy_meta.get("enemyEffects", ally_meta.get("enemyEffects", {})),
        "tickCount": ally_meta.get("tickCount", 0),
    }

    _, turn_events = simulate_with_turn_log(preset, overrides)
    if not turn_events:
        st.warning("No turn events were recorded. Please verify the preset data.")
        st.stop()

    max_turns = st.number_input("Max turns to display", min_value=1, value=20, step=1)

    rows = []
    for index, event in enumerate(turn_events[:max_turns], start=1):
        rows.append({
            "turn_index": index,
            "tick": event.get("tick"),
            "side": "Ally" if event.get("isAlly") else "Enemy",
            "key": event.get("base_key"),
            "name": event.get("name"),
            "turn_number_for_that_monster": event.get("turn_number"),
            "attack_bar_before_reset": event.get("attack_bar_before_reset"),
            "combat_speed_at_turn": event.get("combat_speed"),
        })

    st.dataframe(pd.DataFrame(rows), use_container_width=True)


def _render_monster_overrides(
    title: str,
    monsters: List[Dict[str, Any]],
    prefix: str,
    defaults: Dict[str, Dict[str, Any]] | None = None,
    disabled: bool = False,
) -> Dict[str, Dict[str, Any]]:
    st.markdown(f"### {title}")
    overrides: Dict[str, Dict[str, Any]] = {}
    for monster in monsters:
        key = monster.get("key")
        name = monster.get("name") or key
        st.markdown(f"**{name}** (`{key}`)")
        default_values = (defaults or {}).get(key, {})
        rune_speed = st.number_input(
            "Rune speed",
            min_value=0,
            max_value=400,
            value=int(default_values.get("rune_speed", 0)),
            step=1,
            key=f"{prefix}_{key}_rune_speed",
            disabled=disabled,
        )
        speed_increasing_effect = st.number_input(
            "Speed increasing effect",
            min_value=0,
            max_value=200,
            value=int(default_values.get("speedIncreasingEffect", 0)),
            step=1,
            key=f"{prefix}_{key}_speed_increasing_effect",
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
