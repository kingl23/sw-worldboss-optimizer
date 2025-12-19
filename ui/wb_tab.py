import copy
import streamlit as st

from ranking import rank_all_units
from optimizer import optimize_unit_best_runes
from core_scores import score_unit_total
from visualize import render_optimizer_result
from services.wb_service import run_optimizer_for_unit
from domain.unit_repo import apply_build_to_working_data
from config import K_PER_SLOT


def render_wb_tab(state, monster_names):
    st.subheader("World Boss Analysis")

    # --------------------------------------------------
    # Run = 기준점 생성
    # --------------------------------------------------
    if st.button("Run"):
        state.wb_run = True
        state.wb_ranking = rank_all_units(state.working_data, top_n=60)
        state.selected_unit_id = None
        state.opt_ctx = None

    top_col1, top_col2, _ = st.columns([1, 1, 3])

    with top_col1:
        if st.button("Reset working state"):
            state.working_data = copy.deepcopy(state.original_data)
            state.wb_run = False
            state.wb_ranking = None
            state.selected_unit_id = None
            state.opt_ctx = None

    with top_col2:
        if st.button("Recompute ranking") and state.wb_run:
            state.wb_ranking = rank_all_units(state.working_data, top_n=60)
            state.selected_unit_id = None
            state.opt_ctx = None

    if not state.wb_run:
        st.info("Run 버튼을 눌러 World Boss 분석을 시작하세요.")
        return

    ranking = state.wb_ranking
    if ranking is None:
        st.warning("Ranking data not available.")
        return

    left, right = st.columns([1.5, 1.2], gap="large")

    # --------------------------------------------------
    # LEFT: Ranking (고정)
    # --------------------------------------------------
    with left:
        header = st.columns([1.6, 1.0, 0.8])
        header[0].markdown("**Monster**")
        header[1].markdown("**TOTAL SCORE**")
        header[2].markdown("**Action**")

        for r in ranking:
            unit_id = int(r["unit_id"])
            mid = int(r["unit_master_id"])
            name = monster_names.get(mid, f"Unknown ({mid})")

            row = st.columns([1.6, 1.0, 0.8])
            row[0].code(name)
            row[1].code(f'{r["total_score"]:.1f}')

            if row[2].button("Optimize", key=f"opt_{unit_id}"):
                result = run_optimizer_for_unit(state.working_data, unit_id)
                if result:
                    state.selected_unit_id = unit_id
                    state.opt_ctx = result

        # --------------------------------------------------
        # Manual Optimizer (기존 기능 유지)
        # --------------------------------------------------
        st.divider()
        st.subheader("Manual Optimizer")

        run_manual = st.button("Run manual optimizer")
        manual_target_input = st.text_input(
            "Target Unit Master ID(s) (comma-separated)"
        )

        if run_manual and manual_target_input.strip():
            for tid in manual_target_input.split(","):
                tid = tid.strip()
                if not tid:
                    continue
                u, ch, runes, picked, base = optimize_unit_best_runes(
                    state.working_data, int(tid), K_PER_SLOT
                )
                final = score_unit_total(u)
                st.text(
                    render_optimizer_result(
                        u, ch, runes, picked, base, final_score=final
                    )
                )

    # --------------------------------------------------
    # RIGHT: Before / After
    # --------------------------------------------------
    with right:
        if state.selected_unit_id is None or state.opt_ctx is None:
            st.info("왼쪽 Ranking에서 유닛을 선택해 Optimize를 누르세요.")
            return

        colA, colB = st.columns(2, gap="medium")

        with colA:
            st.markdown("### Before")
            st.text(state.opt_ctx["before_text"])

        with colB:
            st.markdown("### After")
            st.text(state.opt_ctx["after_text"])

        st.divider()

        if st.button("✅ Apply this build"):
            ok, msg = apply_build_to_working_data(
                state.working_data,
                state.selected_unit_id,
                state.opt_ctx["rec_runes"],
            )
            st.success(msg)
            state.selected_unit_id = None
            state.opt_ctx = None
