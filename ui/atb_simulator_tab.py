import pandas as pd
import streamlit as st

from config.atb_simulator_presets import ATB_SIMULATOR_PRESETS, build_atb_preset
from domain.atb_simulator import simulate


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

    preset_id = st.selectbox("Preset", options=list(ATB_SIMULATOR_PRESETS.keys()))
    st.caption("Enemy uses the same trio as Ally by default.")

    try:
        preset = build_atb_preset(preset_id)
    except ValueError as exc:
        st.warning(str(exc))
        st.stop()

    allies = preset.get("allies", [])
    enemies = preset.get("enemies", [])

    if not allies and not enemies:
        st.warning("No preset monsters found. Please edit config/atb_simulator_presets.py.")
        st.stop()

    monster_keys = [monster.get("key") for monster in allies + enemies if monster.get("key")]
    if not monster_keys:
        st.warning("Preset monsters are missing keys. Please edit config/atb_simulator_presets.py.")
        st.stop()

    st.markdown("### Override One Monster")
    selected_key = st.selectbox("Target monster key", options=monster_keys)
    rune_speed = st.number_input("Rune speed", min_value=0, max_value=400, value=0, step=1)
    speed_increasing_effect = st.number_input(
        "Speed increasing effect",
        min_value=0,
        max_value=200,
        value=0,
        step=1,
    )

    overrides = {
        # NOTE: This mapping is designed for future expansion to multiple monsters.
        selected_key: {
            "rune_speed": rune_speed,
            "speedIncreasingEffect": speed_increasing_effect,
        }
    }

    ticks = simulate(preset, overrides)
    if not ticks:
        st.warning("Simulation produced no ticks. Please verify the preset data.")
        st.stop()

    st.markdown("### Tick Viewer")
    tick_index = st.slider("Tick", min_value=0, max_value=len(ticks) - 1, value=0)
    tick_data = ticks[tick_index]

    df = pd.DataFrame(
        [
            {
                "key": monster.get("key"),
                "combat_speed": monster.get("combat_speed"),
                "attack_bar": monster.get("attack_bar"),
                "turn": monster.get("turn"),
                "tookTurn": monster.get("tookTurn"),
            }
            for monster in tick_data.get("monsters", [])
        ]
    )
    st.dataframe(df, use_container_width=True)

    st.markdown("### Attack Bar Trend")
    chart_key = st.selectbox("Monster key for chart", options=monster_keys)
    chart_rows = []
    for tick in ticks:
        monster = next(
            (item for item in tick.get("monsters", []) if item.get("key") == chart_key),
            None,
        )
        if monster is None:
            continue
        chart_rows.append({
            "tick": tick.get("tick"),
            "attack_bar": monster.get("attack_bar"),
        })

    if chart_rows:
        chart_df = pd.DataFrame(chart_rows).set_index("tick")
        st.line_chart(chart_df)
