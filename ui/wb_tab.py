import copy
import streamlit as st

from ranking import rank_all_units
from optimizer import optimize_unit_best_runes
from core_scores import score_unit_total
from visualize import render_optimizer_result
from services.wb_service import run_optimizer_for_unit
from domain.unit_repo import apply_build_to_working_data
from config import K_PER_SLOT
from ui.auth import require_access_or_stop


def _strip_header(text: str) -> str:
    if not text:
        return text

    lines = text.splitlines()
    out = []
    started = False
    for line in lines:
        if not started and line.strip().startswith("[Slot"):
            started = True
        if started:
            out.append(line)
    return "\n".join(out)


def render_wb_tab(state, monster_names):
    st.subheader("World Boss Analysis")

    # ==================================================
    # ▶ Top controls
    #   - Run : left column
    #   - Reset / Recompute : right column (start aligned)
    # ==================================================
    top_left, top_right = st.columns([1.2, 1.8])

    with top_left:
        run_clicked = st.button("▶ Run")

    with top_right:
        reset_clicked, recompute_clicked = st.columns([1, 1])
        with reset_clicked:
            reset = st.button("Reset working state")
        with recompute_clicked:
            recompute = st.button("Recompute ranking")

    # --------------------------------------------------
    # Button actions
    # --------------------------------------------------
    if run_clicked:
        require_access_or_stop("World Boss Run")
        state.wb_run = True
        state.wb_ranking = rank_all_units(state.working_data, top_n=60)
        state.selected_unit_id = None
        state.opt_ctx = None

    if reset:
        state.working_data = copy.deepcopy(state.original_data)
        state.wb_run = False
        state.wb_ranking = None
        state.selected_unit_id = None
        state.opt_ctx = None
        st.info("Working state reset. Run again.")
        return

    if recompute and state.wb_run:
        state.wb_ranking = rank_all_units(state.working_data, top_n=60)
        state.selected_unit_id = None
        state.opt_ctx = None

    if not state.wb_run:
        st.info("Run 버튼을 눌러 분석을 시작하세요.")
        return

    # ==================================================
    # Main layout (폭 조정)
    # ==================================================
    left, right = st.columns([1.2, 1.8], gap="large")

    # ==================================================
    # LEFT: Ranking (폭 축소)
    # ==================================================
    with left:
        header = st.columns([1.3, 0.9, 0.8])
        header[0].markdown("**Monster**")
        header[1].markdown("**TOTAL SCORE**")
        header[2].markdown("**Action**")

        for r in state.wb_ranking:
            unit_id = int(r["unit_id"])
            mid = int(r["unit_master_id"])
            name = monster_names.get(mid, f"Unknown ({mid})")

            row = st.columns([1.3, 0.9, 0.8])
            row[0].markdown(f"`{name}`")
            row[1].markdown(f"`{r['total_score']:.1f}`")

            if row[2].button("Optimize", key=f"opt_{unit_id}"):
                ctx = run_optimizer_for_unit(state.working_data, unit_id)
                if ctx:
                    ctx["before_text"] = _strip_header(ctx["before_text"])
                    ctx["after_text"] = _strip_header(ctx["after_text"])
                    state.selected_unit_id = unit_id
                    state.opt_ctx = ctx

        # Manual Optimizer 유지
        st.divider()
        st.subheader("Manual Optimizer")

        run_manual = st.button("Run manual optimizer")
        manual_ids = st.text_input("Target Unit Master ID(s)")

        if run_manual and manual_ids.strip():
            for tid in manual_ids.split(","):
                tid = tid.strip()
                if not tid:
                    continue
                u, ch, runes, picked, base = optimize_unit_best_runes(
                    state.working_data, int(tid), K_PER_SLOT
                )
                final = score_unit_total(u)
                txt = render_optimizer_result(
                    u, ch, runes, picked, base, final_score=final
                )
                st.text(_strip_header(txt))

    # ==================================================
    # RIGHT: Optimizer Panel (폭 확장)
    # ==================================================
    with right:
        if state.selected_unit_id is None or state.opt_ctx is None:
            st.info("왼쪽에서 Optimize를 누르세요.")
            return

        colA, colB = st.columns(2)

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
