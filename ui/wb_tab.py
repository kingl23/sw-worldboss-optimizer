import copy
import streamlit as st

from services.ranking import rank_all_units
from services.optimizer import optimize_unit_best_runes
from domain.scores import score_unit_total
from ui.text_render import format_optimizer_result
from services.wb_service import run_optimizer_for_unit
from domain.unit_repo import apply_runes_to_working_data
from config.settings import K_PER_SLOT

from ui.auth import require_access_or_stop


def _trim_slot_header(text: str) -> str:
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


def show_wb_tab(state, monster_names):
    """Render the World Boss analysis tab with ranking and optimizer controls."""
    st.subheader("World Boss Analysis")

    top_left, top_right = st.columns([1.3, 1.7])
    
    with top_left:
        run_clicked = st.button("Run analysis", type="primary")
    
    with top_right:
        if state.wb_run:
            c1, c2, c3 = st.columns([0.9, 1.1, 2.0])
            with c1:
                reset = st.button("Reset", help="Reset working state")
            with c2:
                recompute = st.button("Recompute", help="Recompute ranking")
            with c3:
                st.empty()
        else:
            reset = False
            recompute = False
            st.empty()


    if run_clicked:
        if not require_access_or_stop("world_boss"):
            return

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
        st.info("Run analysis 버튼을 눌러 분석을 시작하세요.")
        return

    left, right = st.columns([1.2, 1.8], gap="large")

    with left:
        col_spec = [0.5, 1.0, 0.9, 0.8]

        header = st.columns(col_spec)
        header[0].markdown("**Rank**")
        header[1].markdown("**Monster**")
        header[2].markdown("**TOTAL SCORE**")
        header[3].markdown("**Action**")

        st.markdown(
            """
            <style>
            div[data-testid="stButton"] button {
                padding: 0.18rem 0.55rem !important;
                min-height: 1.8rem !important;
                font-size: 0.82rem !important;
                line-height: 1.0rem !important;
                white-space: nowrap !important;
            }
        
            div[data-testid="stButton"] {
                margin-top: 0.05rem !important;
                margin-bottom: 0.05rem !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        for idx, r in enumerate(state.wb_ranking, start=1):
            unit_id = int(r["unit_id"])
            mid = int(r["unit_master_id"])
            name = monster_names.get(mid, f"Unknown ({mid})")

            row = st.columns(col_spec, vertical_alignment="center")
            row[0].markdown(f"`{idx}`")
            row[1].markdown(f"`{name}`")
            row[2].markdown(f"`{r['total_score']:.1f}`")

            if row[3].button("Optimize", key=f"opt_{unit_id}"):
                ctx = run_optimizer_for_unit(state.working_data, unit_id)
                if ctx:
                    ctx["before_text"] = _trim_slot_header(ctx["before_text"])
                    ctx["after_text"] = _trim_slot_header(ctx["after_text"])
                    state.selected_unit_id = unit_id
                    state.opt_ctx = ctx

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
                txt = format_optimizer_result(
                    u, ch, runes, picked, base, final_score=final
                )
                st.text(_trim_slot_header(txt))

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
            ok, msg = apply_runes_to_working_data(
                state.working_data,
                state.selected_unit_id,
                state.opt_ctx["rec_runes"],
            )
            st.success(msg)
            state.selected_unit_id = None
            state.opt_ctx = None


render_wb_tab = show_wb_tab
