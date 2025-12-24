import copy
import streamlit as st

from visualize import render_optimizer_result
from services.wb_service import (
    build_optimizer_context,
    build_wb_ranking,
    run_manual_optimizer,
)
from domain.unit_repo import apply_build_to_working_data
from config import K_PER_SLOT

from ui.auth import require_access_or_stop  # Run 클릭 시 Access gate


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
    # Top controls
    # ==================================================
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


    # --------------------------------------------------
    # Button actions
    # --------------------------------------------------
    if run_clicked:
        if not require_access_or_stop("world_boss"):
            return

        state.wb_run = True
        state.wb_ranking = build_wb_ranking(state.working_data, top_n=60)
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
        state.wb_ranking = build_wb_ranking(state.working_data, top_n=60)
        state.selected_unit_id = None
        state.opt_ctx = None

    if not state.wb_run:
        st.info("Run analysis 버튼을 눌러 분석을 시작하세요.")
        return

    # ==================================================
    # Main layout
    # ==================================================
    left, right = st.columns([1.2, 1.8], gap="large")

    # ==================================================
    # LEFT: Ranking
    # ==================================================
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
                ctx = build_optimizer_context(state.working_data, unit_id)
                if ctx:
                    before = ctx.get("before")
                    before_score = before["total_score"] if before else None
                    before_state = ctx.get("before_state", {})
                    before_text = render_optimizer_result(
                        before_state.get("unit"),
                        before_state.get("char"),
                        before_state.get("runes"),
                        before_state.get("picked"),
                        before_state.get("base"),
                        final_score=before,
                    )

                    after_state = ctx.get("after_state", {})
                    after = ctx.get("after")
                    if after_state.get("unit") is None:
                        after_text = "Optimizer: no result."
                        after_score = None
                    else:
                        after_score = after["total_score"] if after else None
                        after_text = render_optimizer_result(
                            after_state.get("unit"),
                            after_state.get("char"),
                            after_state.get("runes"),
                            after_state.get("picked"),
                            after_state.get("base"),
                            final_score=after,
                        )

                    state.selected_unit_id = unit_id
                    state.opt_ctx = {
                        "before_text": _strip_header(before_text),
                        "after_text": _strip_header(after_text),
                        "before_score": before_score,
                        "after_score": after_score,
                        "rec_runes": ctx.get("rec_runes"),
                    }

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
                result = run_manual_optimizer(state.working_data, int(tid), K_PER_SLOT)
                if result is None:
                    continue
                u, ch, runes, picked, base = (
                    result.get("unit"),
                    result.get("char"),
                    result.get("runes"),
                    result.get("picked"),
                    result.get("base"),
                )
                final = result.get("final_score")
                txt = render_optimizer_result(
                    u, ch, runes, picked, base, final_score=final
                )
                st.text(_strip_header(txt))

    # ==================================================
    # RIGHT: Optimizer Panel
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
