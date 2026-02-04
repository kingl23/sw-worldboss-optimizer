from __future__ import annotations

from typing import Any, Callable, Dict, Optional

import streamlit as st
import pandas as pd

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
        "speedopt_sec3_prev_preset": "Manual",
        "speedopt_sec3_in2": None,
        "speedopt_sec3_in3": 0,
        "speedopt_sec3_in4": 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _render_section_1() -> None:
    st.markdown("### Section 1")
    _render_control_labels([1, 1, 1], ["Input 1", "Input 2", "Input 3"])
    with st.form("speedopt_sec1_form", clear_on_submit=False):
        input_cols, spacer_col, run_col = _section_columns([1, 1, 1])
        with input_cols[0]:
            st.text_input("Input 1", key="speedopt_sec1_in1", label_visibility="collapsed")
        with input_cols[1]:
            st.text_input("Input 2", key="speedopt_sec1_in2", label_visibility="collapsed")
        with input_cols[2]:
            st.text_input("Input 3", key="speedopt_sec1_in3", label_visibility="collapsed")
        with spacer_col:
            st.empty()
        with run_col:
            run_clicked = st.form_submit_button("Run", key="speedopt_sec1_run")

    progress_slot = st.empty()

    if run_clicked:
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
        progress_bar = _render_progress_bar(progress_slot)
        st.session_state.speedopt_sec1_results = _compute_section1_details(
            parsed_input_1,
            parsed_input_2,
            parsed_input_3,
            progress_callback=lambda value: progress_bar.progress(value),
        )
        progress_bar.progress(1.0)
        st.session_state.speedopt_sec1_ran = True

    _render_section_1_details()



def _render_section_2() -> None:
    st.markdown("### Section 2")
    _render_control_labels(
        [1, 1, 1, 1, 1],
        ["Input 1", "Input 2", "Input 3", "Input 4", "Input 5"],
    )
    with st.form("speedopt_sec2_form", clear_on_submit=False):
        input_cols, spacer_col, run_col = _section_columns([1, 1, 1, 1, 1])
        with input_cols[0]:
            st.text_input("Input 1", key="speedopt_sec2_in1", label_visibility="collapsed")
        with input_cols[1]:
            st.text_input("Input 2", key="speedopt_sec2_in2", label_visibility="collapsed")
        with input_cols[2]:
            st.selectbox(
                "Input 3",
                options=DROPDOWN_OPTIONS,
                key="speedopt_sec2_in3",
                index=_resolve_dropdown_index("speedopt_sec2_in3"),
                placeholder="Select value",
                label_visibility="collapsed",
            )
        with input_cols[3]:
            st.number_input("Input 4", key="speedopt_sec2_in4", step=1, label_visibility="collapsed")
        with input_cols[4]:
            st.number_input("Input 5", key="speedopt_sec2_in5", step=1, label_visibility="collapsed")
        with spacer_col:
            st.empty()
        with run_col:
            run_clicked = st.form_submit_button("Run", key="speedopt_sec2_run")

    if run_clicked:
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
    _render_control_labels([1, 1, 1, 1], ["Preset", "Input 2", "Input 3", "Input 4"])
    _apply_preset_if_changed()
    with st.form("speedopt_sec3_form", clear_on_submit=False):
        input_cols, spacer_col, run_col = _section_columns([1, 1, 1, 1])
        with input_cols[0]:
            st.selectbox(
                "Preset",
                options=list(PRESET_VALUES.keys()),
                key="speedopt_sec3_preset",
                label_visibility="collapsed",
            )
        with input_cols[1]:
            st.selectbox(
                "Input 2",
                options=DROPDOWN_OPTIONS,
                key="speedopt_sec3_in2",
                index=_resolve_dropdown_index("speedopt_sec3_in2"),
                placeholder="Select value",
                label_visibility="collapsed",
            )
        with input_cols[2]:
            st.number_input("Input 3", key="speedopt_sec3_in3", step=1, label_visibility="collapsed")
        with input_cols[3]:
            st.number_input("Input 4", key="speedopt_sec3_in4", step=1, label_visibility="collapsed")
        with spacer_col:
            st.empty()
        with run_col:
            run_clicked = st.form_submit_button("Run", key="speedopt_sec3_run")

    if run_clicked:
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


def _apply_preset_if_changed() -> None:
    current = st.session_state.get("speedopt_sec3_preset")
    previous = st.session_state.get("speedopt_sec3_prev_preset")
    if current == previous:
        return
    st.session_state.speedopt_sec3_prev_preset = current
    _apply_preset_values()


def _resolve_dropdown_index(state_key: str) -> int | None:
    current_value = st.session_state.get(state_key)
    if current_value in DROPDOWN_OPTIONS:
        return DROPDOWN_OPTIONS.index(current_value)
    return None


def _render_progress_bar(container: st.delta_generator.DeltaGenerator) -> st.delta_generator.DeltaGenerator:
    container.markdown("<div style='height: 6px'></div>", unsafe_allow_html=True)
    progress_row = container.columns([3.5])
    return progress_row[0].progress(0)


def _render_details(prefix: str) -> None:
    ran_key = f"{prefix}_ran"
    payload_key = f"{prefix}_payload"
    with st.expander("Details", expanded=bool(st.session_state.get(ran_key))):
        if not st.session_state.get(ran_key):
            return
        payload = st.session_state.get(payload_key) or {}
        if not payload:
            st.info("No results yet.")
            return
        rows = [{"Field": key, "Value": value} for key, value in payload.items()]
        st.dataframe(rows, use_container_width=True, hide_index=True, height=180)


def _render_section_1_details() -> None:
    with st.expander("Details", expanded=bool(st.session_state.get("speedopt_sec1_ran"))):
        if not st.session_state.get("speedopt_sec1_ran"):
            return
        results = st.session_state.get("speedopt_sec1_results") or []
        if not results:
            st.info("No results yet.")
            return
        for result in results:
            st.markdown(f"#### {result.preset_label}")
            if result.effect_table:
                _render_unit_detail_table("Effect → Min Rune Speed", result.effect_table)
            if result.tick_atb_table:
                st.markdown("**Tick ATB Table (Effect 0)**")
                headers = _parse_preset_headers(result.preset_label)
                _render_tick_table(result.tick_atb_table, headers)


def _render_unit_detail_table(
    title: str,
    detail_table: Optional[Any],
    empty_message: str = "No feasible solution.",
) -> None:
    st.markdown(f"**{title}**")
    if not detail_table or not detail_table.ranges:
        st.caption(empty_message)
        return
    ranges = detail_table.ranges
    effect_ranges = [str(row.get("Effect Range", "")).strip() for row in ranges]
    speeds = [row.get("Rune Speed") for row in ranges]
    speed_values = [speed for effect_range, speed in zip(effect_ranges, speeds) if effect_range]
    display_ranges = [effect_range for effect_range in effect_ranges if effect_range]
    _render_wrapped_range_table(display_ranges, speed_values)


def _render_wrapped_range_table(effect_ranges: list[str], speeds: list[Any]) -> None:
    if not effect_ranges:
        return
    split_index = (len(effect_ranges) + 1) // 2
    parts = [
        (effect_ranges[:split_index], speeds[:split_index]),
        (effect_ranges[split_index:], speeds[split_index:]),
    ]
    for ranges, values in parts:
        if not ranges:
            continue
        table_df = pd.DataFrame(
            [["effect", *ranges], ["speed", *values]],
        )
        html = table_df.to_html(index=False, header=False, escape=False)
        st.markdown(html, unsafe_allow_html=True)


def _render_tick_table(raw_table: list[dict[str, Any]], headers: list[str] | None) -> None:
    if not raw_table:
        return
    df = pd.DataFrame(raw_table)
    act_series = df.get("act")
    tick_series = df.get("tick")
    df = df.drop(columns=[col for col in ("act", "note") if col in df.columns])
    name_headers = headers
    if name_headers:
        rename_map = {key: value for key, value in zip(["A1", "A2", "A3", "E"], name_headers)}
        df = df.rename(columns=rename_map)
    highlight_columns = [col for col in df.columns if col not in {"tick"}]

    def _highlight_actor(row: pd.Series) -> list[str]:
        styles = [""] * len(row)
        if act_series is None or tick_series is None:
            return styles
        try:
            idx = row.name
            if tick_series.iloc[idx] == "base+rune":
                return styles
            actor = act_series.iloc[idx]
        except Exception:
            return styles
        if not actor:
            return styles
        column = actor
        if name_headers:
            mapping = {"A1": name_headers[0], "A2": name_headers[1], "A3": name_headers[2], "E": name_headers[3]}
            column = mapping.get(actor, actor)
        if column in row.index:
            col_index = row.index.get_loc(column)
            styles[col_index] = "background-color: #ffe08a"
        return styles

    styler = df.style.apply(_highlight_actor, axis=1)
    styler = styler.set_table_styles(
        [
            {"selector": "th", "props": [("min-width", "60px"), ("max-width", "80px")]},
            {"selector": "td", "props": [("min-width", "60px"), ("max-width", "80px")]},
        ]
    )
    st.dataframe(styler, use_container_width=True, hide_index=True)

def _parse_preset_headers(preset_label: str) -> list[str] | None:
    if not preset_label:
        return None
    title = preset_label.split("|")[0].strip()
    parts = [part.strip() for part in title.split("/") if part.strip()]
    if len(parts) != 3:
        return None
    return [parts[0], parts[1], parts[2], "적"]


def _section_columns(input_weights: list[float]) -> tuple[list[st.delta_generator.DeltaGenerator], st.delta_generator.DeltaGenerator, st.delta_generator.DeltaGenerator]:
    weights = [*input_weights, 1, 0.6]
    cols = st.columns(weights)
    return cols[: len(input_weights)], cols[-2], cols[-1]


def _render_control_labels(weights: list[float], labels: list[str]) -> None:
    input_cols, spacer_col, run_col = _section_columns(weights)
    for col, label in zip(input_cols, labels):
        with col:
            st.caption(label)
    with spacer_col:
        st.empty()
    with run_col:
        st.caption("")


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
    progress_callback: Callable[[float], None] | None = None,
) -> list[Any]:
    debug_mode = False
    cache_key = (input_1, input_2, input_3, debug_mode)
    cached = st.session_state.speedopt_sec1_cache.get(cache_key)
    if cached is not None:
        if progress_callback:
            progress_callback(1.0)
        return cached

    preset_ids = list(ATB_SIMULATOR_PRESETS.keys())
    max_runtime_s = float(st.session_state.get("speedopt_sec1_max_runtime_s") or 10.0)
    results: list[Any] = []
    total = len(preset_ids)
    if total == 0:
        return results

    if progress_callback:
        progress_callback(0.0)
    for index, preset_id in enumerate(preset_ids, start=1):
        try:
            result = build_section1_detail_cached(
                preset_id,
                input_1,
                input_2,
                input_3,
                max_runtime_s,
                debug_mode,
            )
        except ValueError as exc:
            result = _build_error_result(preset_id, str(exc))
        results.append(result)
        if progress_callback:
            progress_callback(index / total)

    st.session_state.speedopt_sec1_cache[cache_key] = results
    return results


def _build_error_result(preset_id: str, message: str):
    return PresetDetailResult(
        preset_name=preset_id,
        preset_label=preset_id,
        leader_percent=0,
        objective=message,
        legend="",
        formula_notes=[],
        formula_table=[],
        no_solution_diagnostic=None,
        effect_table=None,
        min_cut_result=None,
        tick_atb_table=None,
        status="NO VALID SOLUTION",
    )
