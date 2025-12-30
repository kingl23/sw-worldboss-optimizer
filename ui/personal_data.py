from __future__ import annotations

import streamlit as st

from config.settings import WIZARD_NAMES
from ui.auth import require_access_or_stop
from ui.table_utils import apply_dataframe_style, build_deck_column, percent_to_float, to_numeric
from services.personal_data_service import (
    get_attack_log_hour_distribution,
    get_offense_deck_details,
    get_record_summary,
    get_top_defense_decks,
    get_top_offense_decks,
)


def _deck_label(row) -> str:
    return f"{row['Unit #1']} / {row['Unit #2']} / {row['Unit #3']}"


def _select_offense_key(df, table_key: str) -> str | None:
    df = df.reset_index(drop=True)
    df_display = df.drop(columns=["key"]).reset_index(drop=True)
    df_display["Offense Deck"] = build_deck_column(df_display, ["Unit #1", "Unit #2", "Unit #3"])
    df_display = df_display.drop(columns=["Unit #1", "Unit #2", "Unit #3"])
    df_display = df_display.rename(columns={"Win Rate (%)": "Win Rate"})
    df_display["Wins"] = to_numeric(df_display["Wins"])
    df_display["Losses"] = to_numeric(df_display["Losses"])
    df_display["Total Games"] = to_numeric(df_display["Total Games"])
    df_display["Win Rate"] = percent_to_float(df_display["Win Rate"])
    df_display = df_display[["Offense Deck", "Wins", "Losses", "Total Games", "Win Rate"]]

    try:
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            selection_mode="single-row",
            on_select="rerun",
            key=table_key,
            column_config={
                "Offense Deck": st.column_config.TextColumn("Offense Deck", width="large"),
                "Wins": st.column_config.NumberColumn("Wins", format="%d", width="small"),
                "Losses": st.column_config.NumberColumn("Losses", format="%d", width="small"),
                "Total Games": st.column_config.NumberColumn("Total Games", format="%d", width="small"),
                "Win Rate": st.column_config.NumberColumn("Win Rate", format="%.1f%%", width="small"),
            },
        )
        selection = st.session_state.get(table_key, {}).get("selection", {})
        rows = selection.get("rows", [])
        if rows:
            return df.iloc[rows[0]]["key"]
        return None
    except TypeError:
        # fallback: selection_mode 미지원 환경
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Offense Deck": st.column_config.TextColumn("Offense Deck", width="large"),
                "Wins": st.column_config.NumberColumn("Wins", format="%d", width="small"),
                "Losses": st.column_config.NumberColumn("Losses", format="%d", width="small"),
                "Total Games": st.column_config.NumberColumn("Total Games", format="%d", width="small"),
                "Win Rate": st.column_config.NumberColumn("Win Rate", format="%.1f%%", width="small"),
            },
        )
        labels = [_deck_label(row) for _, row in df.iterrows()]
        label_map = {label: key for label, key in zip(labels, df["key"].tolist())}
        selected_label = st.selectbox(
            "Select Deck",
            options=[""] + labels,
            index=0,
            key=f"{table_key}_fallback",
        )
        if selected_label:
            return label_map[selected_label]
        return None


def render_personal_data_tab():
    st.subheader("Personal Data")
    apply_dataframe_style()

    # --- state keys ---
    run_key = "personal_data_run"
    wizard_key = "personal_wizard_select"
    last_wizard_key = "personal_last_wizard"

    # wizard selection
    wizard_name = st.selectbox(
        "Wizard",
        options=[""] + WIZARD_NAMES,
        index=0,
        key=wizard_key,
    )

    # reset when wizard changes
    if st.session_state.get(last_wizard_key) != wizard_name:
        st.session_state[last_wizard_key] = wizard_name
        st.session_state[run_key] = False
        # reset selected deck state
        st.session_state.pop("personal_offense_table", None)
        st.session_state.pop("personal_offense_table_fallback", None)

    if not wizard_name:
        st.info("Select a wizard.")
        return

    # search button
    cols = st.columns([1, 3])
    with cols[0]:
        clicked = st.button("Search", type="primary", use_container_width=True, key="personal_search_btn")

    if clicked:
        # 버튼 클릭 시에만 access gate
        if not require_access_or_stop("personal_data"):
            return
        st.session_state[run_key] = True

    # hide results until search runs
    if not st.session_state.get(run_key, False):
        st.info("Click Search to load data.")
        return

    # --- 이하 결과 렌더 ---
    st.markdown("### Record Summary")
    summary_df = get_record_summary(wizard_name)
    if summary_df.empty:
        st.info("No record summary data available.")
    else:
        summary_display = summary_df.rename(columns={"Win Rate (%)": "Win Rate"})
        summary_display["Wins"] = to_numeric(summary_display["Wins"])
        summary_display["Losses"] = to_numeric(summary_display["Losses"])
        summary_display["Total Games"] = to_numeric(summary_display["Total Games"])
        summary_display["Win Rate"] = percent_to_float(summary_display["Win Rate"])
        st.dataframe(
            summary_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Category": st.column_config.TextColumn("Category", width="small"),
                "Total Games": st.column_config.NumberColumn("Total Games", format="%d", width="small"),
                "Wins": st.column_config.NumberColumn("Wins", format="%d", width="small"),
                "Losses": st.column_config.NumberColumn("Losses", format="%d", width="small"),
                "Win Rate": st.column_config.NumberColumn("Win Rate", format="%.1f%%", width="small"),
            },
        )

    st.divider()

    st.markdown("### Top Offense Decks")
    off_limit = st.number_input(
        "Top Offense Limit",
        min_value=1,
        max_value=200,
        value=10,
        step=1,
        key="personal_offense_limit",
    )
    off_df = get_top_offense_decks(wizard_name, int(off_limit))
    selected_key = None
    if off_df.empty:
        st.info("No top offense deck data available.")
    else:
        selected_key = _select_offense_key(off_df, "personal_offense_table")

    st.divider()

    st.markdown("### Top Defense Decks")
    def_limit = st.number_input(
        "Top Defense Limit",
        min_value=1,
        max_value=200,
        value=10,
        step=1,
        key="personal_defense_limit",
    )
    def_df = get_top_defense_decks(wizard_name, int(def_limit))
    if def_df.empty:
        st.info("No top defense deck data available.")
    else:
        def_display = def_df.drop(columns=["key"]).reset_index(drop=True)
        def_display["Defense Deck"] = build_deck_column(def_display, ["Unit #1", "Unit #2", "Unit #3"])
        def_display = def_display.drop(columns=["Unit #1", "Unit #2", "Unit #3"])
        def_display = def_display.rename(columns={"Win Rate (%)": "Win Rate"})
        def_display["Wins"] = to_numeric(def_display["Wins"])
        def_display["Losses"] = to_numeric(def_display["Losses"])
        def_display["Total Games"] = to_numeric(def_display["Total Games"])
        def_display["Win Rate"] = percent_to_float(def_display["Win Rate"])
        def_display = def_display[["Defense Deck", "Win Rate", "Wins", "Losses", "Total Games"]]
        st.dataframe(
            def_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Defense Deck": st.column_config.TextColumn("Defense Deck", width="large"),
                "Wins": st.column_config.NumberColumn("Wins", format="%d", width="small"),
                "Losses": st.column_config.NumberColumn("Losses", format="%d", width="small"),
                "Total Games": st.column_config.NumberColumn("Total Games", format="%d", width="small"),
                "Win Rate": st.column_config.NumberColumn("Win Rate", format="%.1f%%", width="small"),
            },
        )

    st.divider()

    st.markdown("### Offense Deck Detail Logs")
    if not selected_key:
        st.info("Select a row from Top Offense Decks to see detail logs.")
    else:
        detail_limit = st.number_input(
            "Detail Log Limit",
            min_value=1,
            max_value=500,
            value=100,
            step=10,
            key="personal_detail_limit",
        )

        detail_df = get_offense_deck_details(wizard_name, selected_key, int(detail_limit))
        if detail_df.empty:
            st.info("No detail logs available for the selected deck.")
        else:
            detail_display = detail_df.copy()
            selected_offense = build_deck_column(
                detail_display.iloc[[0]],
                ["Offense Deck 1", "Offense Deck 2", "Offense Deck 3"],
            ).iloc[0]
            st.write(f"Selected Offense Deck: **{selected_offense}**")
            detail_display["Offense Deck"] = build_deck_column(
                detail_display,
                ["Offense Deck 1", "Offense Deck 2", "Offense Deck 3"],
            )
            detail_display["Defense Deck"] = build_deck_column(
                detail_display,
                ["Defense Deck 1", "Defense Deck 2", "Defense Deck 3"],
            )
            detail_display = detail_display.drop(
                columns=[
                    "Offense Deck 1",
                    "Offense Deck 2",
                    "Offense Deck 3",
                    "Defense Deck 1",
                    "Defense Deck 2",
                    "Defense Deck 3",
                ]
            )
            detail_display = detail_display[["Defense Deck", "Result", "Defense Guild", "Defender"]]
            st.dataframe(
                detail_display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Defense Deck": st.column_config.TextColumn("Defense Deck", width="large"),
                    "Defense Guild": st.column_config.TextColumn("Defense Guild", width="medium"),
                    "Defender": st.column_config.TextColumn("Defender", width="small"),
                    "Result": st.column_config.TextColumn("Result", width="small"),
                },
            )

    st.divider()

    st.markdown("### Hourly Log Distribution (12–23)")
    st.caption("Counts of siege_logs for the selected wizard grouped by hour (date ignored).")
    hour_df = get_attack_log_hour_distribution(wizard_name)
    st.bar_chart(hour_df.set_index("Hour"), height=240)
