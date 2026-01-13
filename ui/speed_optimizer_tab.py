from __future__ import annotations

from typing import Any, Dict, Optional
import time

import streamlit as st

from config.atb_simulator_presets import ATB_SIMULATOR_PRESETS
from domain.speed_optimizer_detail import (
    PresetDetailResult,
    build_section1_detail_cached,
)

DROPDOWN_OPTIONS = [19, 21, 24, 28, 33]
PRESET_VALUES = {
    "Manual": None,
    "Preset A": {"v2": 19, "v3": 100, "v4": 190},
    "Preset B": {"v2": 24, "v3": 102, "v4": 190},
    "Preset C": {"v2": 33, "v3": 106, "v4": 190},
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
        "speedopt_sec1_results": None,
        "speedopt_sec1_cache": {},
        "speedopt_sec1_debug_only_first": False,
        "speedopt_sec1_max_runtime_s": 10.0,
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
        if _run_button_col(key="speedopt_sec1_run", spacer_px=28):
            input_1 = st.session_state.speedopt_sec1_in1
            input_2 = st.session_state.speedopt_sec1_in2
            input_3 = st.session_state.speedopt_sec1_in3
            parsed_input_1 = _parse_optional_int(input_1, label="Input 1")
            parsed_input_2 = _parse_optional_int(input_2, label="Input 2")
            parsed_input_3 = _parse_optional_int(input_3, label="Input 3")
            if parsed_input_1 is None and input_1.strip():
                st.stop()
            if parsed_input_2 is None and input_2.strip():
                st.stop()
            if parsed_input_3 is None and input_3.strip():
                st.stop()
            effective_input_3 = input_3 or input_1
            payload = {
                "input_1": input_1,
                "input_2": input_2,
                "input_3": effective_input_3,
            }
            st.session_state.speedopt_sec1_payload = payload
            st.session_state.speedopt_sec1_results = _compute_section1_details(
                parsed_input_1,
                parsed_input_2,
                parsed_input_3,
            )
            st.session_state.speedopt_sec1_ran = True

    st.checkbox(
        "Debug: only first preset",
        key="speedopt_sec1_debug_only_first",
        help="Limit calculations to the first preset to speed up debugging.",
    )
    st.number_input(
        "Max runtime per preset (seconds)",
        min_value=1.0,
        max_value=60.0,
        step=1.0,
        key="speedopt_sec1_max_runtime_s",
    )

    _render_section_1_details()


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
        if _run_button_col(key="speedopt_sec2_run", spacer_px=34):
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
        if _run_button_col(key="speedopt_sec3_run", spacer_px=34):
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


def _run_button_col(label: str = "Run", key: str | None = None, spacer_px: int = 28) -> bool:
    st.markdown(
        f"<div style='height: {spacer_px}px'></div>",
        unsafe_allow_html=True,
    )
    return st.button(label, key=key)


def _render_section_1_details() -> None:
    with st.expander("Details", expanded=bool(st.session_state.get("speedopt_sec1_ran"))):
        if not st.session_state.get("speedopt_sec1_ran"):
            return
        results = st.session_state.get("speedopt_sec1_results") or []
        if not results:
            st.info("No results yet.")
            return
        for result in results:
            st.markdown(f"#### {result.preset_id}")
            if result.timing:
                st.caption(
                    "Timing (s) — "
                    f"e_fast: {result.timing.get('e_fast_s', 0):.2f}, "
                    f"a3: {result.timing.get('a3_s', 0):.2f}"
                )
            if result.error:
                st.warning(result.error)
                continue
            _render_unit_detail_table(
                "A3 Detail",
                result.a3_table,
                empty_message="No feasible solution for a3 given a1 fixed by Input 2.",
            )


def _render_unit_detail_table(
    title: str,
    detail_table: Optional[Any],
    empty_message: str = "No feasible solution.",
) -> None:
    st.markdown(f"**{title}**")
    if not detail_table or not detail_table.ranges:
        st.caption(empty_message)
        return
    st.table(detail_table.ranges)


def _parse_optional_int(value: str, label: str) -> Optional[int]:
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    try:
        return int(stripped)
    except ValueError:
        st.warning(f"{label} must be an integer.")
        return None


def _compute_section1_details(
    input_1: Optional[int],
    input_2: Optional[int],
    input_3: Optional[int],
) -> list[Any]:
    cache_key = (input_1, input_2, input_3)
    cached = st.session_state.speedopt_sec1_cache.get(cache_key)
    if cached is not None:
        return cached

    preset_ids = list(ATB_SIMULATOR_PRESETS.keys())
    if st.session_state.get("speedopt_sec1_debug_only_first") and preset_ids:
        preset_ids = preset_ids[:1]

    max_runtime_s = float(st.session_state.get("speedopt_sec1_max_runtime_s") or 10.0)
    results: list[Any] = []
    total = len(preset_ids)
    if total == 0:
        return results

    with st.status("Computing Section 1 details...", expanded=True) as status:
        progress = st.progress(0)
        for index, preset_id in enumerate(preset_ids, start=1):
            status.write(f"Processing {preset_id} ({index}/{total})")
            start = time.perf_counter()
            try:
                result = build_section1_detail_cached(
                    preset_id,
                    input_1,
                    input_2,
                    input_3,
                    max_runtime_s,
                )
            except ValueError as exc:
                result = _build_error_result(preset_id, str(exc))
            results.append(result)
            elapsed = time.perf_counter() - start
            status.write(f"Finished {preset_id} in {elapsed:.2f}s")
            progress.progress(index / total)
        status.update(state="complete")

    st.session_state.speedopt_sec1_cache[cache_key] = results
    return results


def _build_error_result(preset_id: str, message: str):
    return PresetDetailResult(
        preset_id=preset_id,
        a1_table=None,
        a3_table=None,
        error=message,
        timing=None,
    )
