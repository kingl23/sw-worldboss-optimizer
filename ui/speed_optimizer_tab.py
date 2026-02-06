from __future__ import annotations

from typing import Any, Callable, Dict, Optional

import streamlit as st
import pandas as pd
from html import escape

from config.atb_simulator_presets import ATB_MONSTER_LIBRARY, ATB_SIMULATOR_PRESETS
from domain.speed_optimizer_detail import (
    PresetDetailResult,
    build_section1_detail_cached,
)


def render_speed_optimizer_tab(state: Dict[str, Any], monster_names: Dict[int, str]) -> None:
    _initialize_speedopt_state()

    st.subheader("Speed Optimizer")

    _render_section_1()


def _initialize_speedopt_state() -> None:
    defaults = {
        "speedopt_sec1_ran": False,
        "speedopt_sec1_payload": None,
        "speedopt_sec1_results": None,
        "speedopt_sec1_cache": {},
        "speedopt_sec1_max_runtime_s": 10.0,
        "speedopt_sec1_in1": "",
        "speedopt_sec1_in2": "",
        "speedopt_sec1_in3": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _render_section_1() -> None:
    st.markdown("### Section 1")
    _render_control_labels(
        [1, 1, 1],
        ["최신속 (빛늑 기준)", "신의 (물호박 기준)", "적 최신속 (빛늑 기준)"],
    )
    with st.form("speedopt_sec1_form", clear_on_submit=False):
        input_cols, spacer_col, run_col = _section_columns([1, 1, 1])
        with input_cols[0]:
            st.text_input("최신속 (빛늑 기준)", key="speedopt_sec1_in1", label_visibility="collapsed")
        with input_cols[1]:
            st.text_input("신의 (물호박 기준)", key="speedopt_sec1_in2", label_visibility="collapsed")
        with input_cols[2]:
            st.text_input("적 최신속 (빛늑 기준)", key="speedopt_sec1_in3", label_visibility="collapsed")
        with spacer_col:
            st.empty()
        with run_col:
            run_clicked = st.form_submit_button("Run", key="speedopt_sec1_run")

    progress_slot = st.empty()

    if run_clicked:
        input_1 = st.session_state.speedopt_sec1_in1
        input_2 = st.session_state.speedopt_sec1_in2
        input_3 = st.session_state.speedopt_sec1_in3
        parsed_input_1 = _parse_optional_int(input_1, label="최신속 (빛늑 기준)")
        parsed_input_2 = _parse_optional_int(input_2, label="신의 (물호박 기준)")
        parsed_input_3 = _parse_optional_int(input_3, label="적 최신속 (빛늑 기준)")
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
        results = st.session_state.speedopt_sec1_results or []
        if results:
            payload["resolved_enemy_rune_speed"] = results[0].enemy_rune_speed_effective
        progress_bar.progress(1.0)
        st.session_state.speedopt_sec1_ran = True

    _render_section_1_details()



def _render_progress_bar(container: st.delta_generator.DeltaGenerator) -> st.delta_generator.DeltaGenerator:
    container.markdown("<div style='height: 6px'></div>", unsafe_allow_html=True)
    progress_row = container.columns([3.5])
    return progress_row[0].progress(0)




def _effect_table_title_from_monster_key(monster_key: Optional[str]) -> str:
    if not monster_key:
        return "UNKNOWN"
    base_key = monster_key.split("|", 1)[-1]
    monster = ATB_MONSTER_LIBRARY.get(base_key)
    if not isinstance(monster, dict):
        return "UNKNOWN"
    name = monster.get("name")
    return name if isinstance(name, str) and name else "UNKNOWN"

def _render_section_1_details() -> None:
    with st.expander("Details", expanded=bool(st.session_state.get("speedopt_sec1_ran"))):
        if not st.session_state.get("speedopt_sec1_ran"):
            return
        payload = st.session_state.get("speedopt_sec1_payload") or {}
        if payload.get("resolved_enemy_rune_speed") is not None:
            st.caption(f"resolved enemy rune speed: {payload['resolved_enemy_rune_speed']}")
        results = st.session_state.get("speedopt_sec1_results") or []
        if not results:
            st.info("No results yet.")
            return
        for index, result in enumerate(results):
            st.markdown(f"#### {result.preset_label}")
            if result.preset_name == "Preset B":
                title_keys = result.effect_title_keys or {}
                if result.effect_table_step1:
                    _render_unit_detail_table(
                        _effect_table_title_from_monster_key(title_keys.get("step1")),
                        result.effect_table_step1,
                    )
                if result.effect_table:
                    _render_unit_detail_table(
                        _effect_table_title_from_monster_key(title_keys.get("target")),
                        result.effect_table,
                    )
            elif result.effect_table:
                title_keys = result.effect_title_keys or {}
                _render_unit_detail_table(
                    _effect_table_title_from_monster_key(title_keys.get("target")),
                    result.effect_table,
                )
            if result.tick_atb_table:
                with st.expander("틱 테이블 보기", expanded=False):
                    st.markdown("**Tick ATB Table (Effect 0)**")
                    _render_tick_table(result.tick_atb_table, result.tick_headers)
            if index < len(results) - 1:
                st.divider()


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
    tiles = []
    for effect_range, speed in zip(effect_ranges, speeds):
        tiles.append(
            f"""
            <div class='effect-speed-tile'>
                <div class='effect-speed-label'>속증 {escape(str(effect_range))}</div>
                <div class='effect-speed-value'>공속 {escape(str(speed))}</div>
            </div>
            """
        )

    html = (
        "<style>"
        ".effect-speed-container {"
        "display:flex;"
        "flex-wrap:nowrap;"
        "overflow-x:auto;"
        "gap:8px;"
        "padding:4px 2px;"
        "margin:0.25rem 0 0.5rem 0;"
        "}"
        ".effect-speed-tile {"
        "border:1px solid #ddd;"
        "border-radius:8px;"
        "padding:6px 8px;"
        "min-width:90px;"
        "flex:0 0 auto;"
        "background:#fff;"
        "}"
        ".effect-speed-label {"
        "font-size:12px;"
        "font-weight:600;"
        "opacity:0.85;"
        "}"
        ".effect-speed-value {"
        "font-size:12px;"
        "margin-top:2px;"
        "}"
        "</style>"
        f"<div class='effect-speed-container'>{''.join(tiles)}</div>"
    )
    st.markdown(html, unsafe_allow_html=True)


def _render_tick_table(raw_table: list[dict[str, Any]], headers: list[str] | None) -> None:
    if not raw_table:
        return
    df_raw = pd.DataFrame(raw_table)
    df_raw["tick"] = df_raw["tick"].astype(int)
    enemy_ticks = df_raw.loc[df_raw.get("act") == "E", "tick"]
    first_enemy_tick = int(enemy_ticks.min()) if not enemy_ticks.empty else 15
    end_tick = min(15, first_enemy_tick)
    df_raw = df_raw[df_raw["tick"].between(0, end_tick)]
    df_raw["tick"] = df_raw["tick"] + 1
    if df_raw.empty:
        return
    act_series = df_raw.get("act")
    speed_buff_series = df_raw.get("speed_buff")
    df = df_raw.drop(columns=[col for col in ("act", "note") if col in df_raw.columns])
    df = df.drop(columns=[col for col in ("speed_buff", "ally_atb_low_target") if col in df.columns])
    name_headers = headers
    if name_headers:
        rename_map = {key: value for key, value in zip(["A1", "A2", "A3", "E"], name_headers)}
        df = df.rename(columns=rename_map)
        if speed_buff_series is not None:
            def _map_buffs(buffs: Any) -> dict[str, bool]:
                if not isinstance(buffs, dict):
                    return {}
                return {rename_map.get(key, key): value for key, value in buffs.items()}

            speed_buff_series = speed_buff_series.map(_map_buffs)
    for col in df.columns:
        if col == "tick":
            continue
        formatted_values = []
        for idx, value in enumerate(df[col].tolist()):
            formatted = f"{value:.2f}" if isinstance(value, (int, float)) else value
            if speed_buff_series is not None:
                try:
                    buff_map = speed_buff_series.iloc[idx]
                except Exception:
                    buff_map = {}
                if isinstance(buff_map, dict) and buff_map.get(col) and formatted is not None:
                    formatted = f"{formatted} ▲"
            formatted_values.append(formatted)
        df[col] = formatted_values

    def _highlight_actor(row: pd.Series) -> list[str]:
        styles = [""] * len(row)
        if act_series is None:
            return styles
        try:
            idx = row.name
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
            styles[col_index] = f"{styles[col_index]}background-color: #fff2cc; color: #333333"
        return styles

    styler = df.style.apply(_highlight_actor, axis=1)
    styler = styler.set_table_styles(
        [
            {"selector": "th", "props": [("min-width", "60px"), ("max-width", "80px")]},
            {"selector": "td", "props": [("min-width", "60px"), ("max-width", "80px")]},
        ]
    )
    st.dataframe(styler, use_container_width=True, hide_index=True)


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
