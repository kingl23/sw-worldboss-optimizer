from __future__ import annotations

from typing import Any, Dict

import streamlit as st

DROPDOWN_OPTIONS = [19, 21, 24, 28, 33]
PRESET_VALUES = {
    "Manual": None,
    "Preset A": {"v2": 19, "v3": 5, "v4": 10},
    "Preset B": {"v2": 24, "v3": 8, "v4": 12},
    "Preset C": {"v2": 33, "v3": 15, "v4": 20},
}


def render_speed_optimizer_tab(state: Dict[str, Any], monster_names: Dict[int, str]) -> None:
    _initialize_speedopt_state()

    st.subheader("Speed Optimizer")

    _render_section_1()
    st.divider()
    _render_section_2()
    st.divider()
    _render_section_3()


def _initialize_speedopt_state() -> None:
    defaults = {
        "speedopt_sec1_ran": False,
        "speedopt_sec1_payload": None,
        "speedopt_sec2_ran": False,
        "speedopt_sec2_payload": None,
        "speedopt_sec3_ran": False,
        "speedopt_sec3_payload": None,
        "speedopt_sec1_in1": "",
        "speedopt_sec1_in2": "",
        "speedopt_sec1_in3": "",
        "speedopt_sec2_in1": "",
        "speedopt_sec2_in2": "",
        "speedopt_sec2_in3": None,
        "speedopt_sec2_in4": 0,
        "speedopt_sec2_in5": 0,
        "speedopt_sec3_preset": "Manual",
        "speedopt_sec3_in2": None,
        "speedopt_sec3_in3": 0,
        "speedopt_sec3_in4": 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _render_section_1() -> None:
    st.markdown("### Section 1")
    row = st.columns([1, 1, 1, 0.5])
    with row[0]:
        st.text_input("Input 1", key="speedopt_sec1_in1")
    with row[1]:
        st.text_input("Input 2", key="speedopt_sec1_in2")
    with row[2]:
        st.text_input("Input 3", key="speedopt_sec1_in3")
    with row[3]:
        if st.button("Run", key="speedopt_sec1_run"):
            input_1 = st.session_state.speedopt_sec1_in1
            input_2 = st.session_state.speedopt_sec1_in2
            input_3 = st.session_state.speedopt_sec1_in3
            effective_input_3 = input_3 or input_1
            payload = {
                "input_1": input_1,
                "input_2": input_2,
                "input_3": effective_input_3,
            }
            st.session_state.speedopt_sec1_payload = payload
            st.session_state.speedopt_sec1_ran = True

    _render_details("speedopt_sec1")


def _render_section_2() -> None:
    st.markdown("### Section 2")
    row = st.columns([1, 1, 1, 1, 1, 0.5])
    with row[0]:
        st.text_input("Input 1", key="speedopt_sec2_in1")
    with row[1]:
        st.text_input("Input 2", key="speedopt_sec2_in2")
    with row[2]:
        st.selectbox(
            "Input 3",
            options=DROPDOWN_OPTIONS,
            key="speedopt_sec2_in3",
            index=_resolve_dropdown_index("speedopt_sec2_in3"),
            placeholder="Select value",
        )
    with row[3]:
        st.number_input("Input 4", key="speedopt_sec2_in4", step=1)
    with row[4]:
        st.number_input("Input 5", key="speedopt_sec2_in5", step=1)
    with row[5]:
        if st.button("Run", key="speedopt_sec2_run"):
            payload = {
                "input_1": st.session_state.speedopt_sec2_in1,
                "input_2": st.session_state.speedopt_sec2_in2,
                "input_3": st.session_state.speedopt_sec2_in3,
                "input_4": st.session_state.speedopt_sec2_in4,
                "input_5": st.session_state.speedopt_sec2_in5,
            }
            st.session_state.speedopt_sec2_payload = payload
            st.session_state.speedopt_sec2_ran = True

    _render_details("speedopt_sec2")


def _render_section_3() -> None:
    st.markdown("### Section 3")
    row = st.columns([1.2, 1, 1, 1, 0.5])
    with row[0]:
        st.selectbox(
            "Preset",
            options=list(PRESET_VALUES.keys()),
            key="speedopt_sec3_preset",
            on_change=_apply_preset_values,
        )
    with row[1]:
        st.selectbox(
            "Input 2",
            options=DROPDOWN_OPTIONS,
            key="speedopt_sec3_in2",
            index=_resolve_dropdown_index("speedopt_sec3_in2"),
            placeholder="Select value",
        )
    with row[2]:
        st.number_input("Input 3", key="speedopt_sec3_in3", step=1)
    with row[3]:
        st.number_input("Input 4", key="speedopt_sec3_in4", step=1)
    with row[4]:
        if st.button("Run", key="speedopt_sec3_run"):
            payload = {
                "preset": st.session_state.speedopt_sec3_preset,
                "input_2": st.session_state.speedopt_sec3_in2,
                "input_3": st.session_state.speedopt_sec3_in3,
                "input_4": st.session_state.speedopt_sec3_in4,
            }
            st.session_state.speedopt_sec3_payload = payload
            st.session_state.speedopt_sec3_ran = True

    _render_details("speedopt_sec3")


def _apply_preset_values() -> None:
    preset_key = st.session_state.speedopt_sec3_preset
    preset = PRESET_VALUES.get(preset_key)
    if not preset:
        return
    preset_v2 = preset.get("v2")
    if preset_v2 in DROPDOWN_OPTIONS:
        st.session_state.speedopt_sec3_in2 = preset_v2
    st.session_state.speedopt_sec3_in3 = preset.get("v3", 0)
    st.session_state.speedopt_sec3_in4 = preset.get("v4", 0)


def _resolve_dropdown_index(state_key: str) -> int | None:
    current_value = st.session_state.get(state_key)
    if current_value in DROPDOWN_OPTIONS:
        return DROPDOWN_OPTIONS.index(current_value)
    return None


def _render_details(prefix: str) -> None:
    ran_key = f"{prefix}_ran"
    payload_key = f"{prefix}_payload"
    with st.expander("Details", expanded=bool(st.session_state.get(ran_key))):
        if st.session_state.get(ran_key):
            st.markdown("TODO: details")
            st.json(st.session_state.get(payload_key) or {})
