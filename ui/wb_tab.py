import copy
import streamlit as st

from ranking import rank_all_units
from optimizer import optimize_unit_best_runes
from core_scores import score_unit_total
from visualize import render_optimizer_result
from services.wb_service import run_optimizer_for_unit
from domain.unit_repo import apply_build_to_working_data
from config import K_PER_SLOT

from ui.auth import require_access_or_stop  # ✅ Run 클릭 시 Access gate


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
    # - Run (primary/red 느낌) + Reset + Recompute를 한 줄에 가깝게 배치
    # ==================================================
    ctl1, ctl2, ctl3 = st.columns([1.0, 1.0, 1.6])

    with ctl1:
        # ✅ 1) Artifact Run analysis처럼 (색/텍스트)
        run_clicked = st.button("Run analysis", type="primary")

    with ctl2:
        reset = st.button("Reset working state")

    with ctl3:
        # ✅ 4) recompute를 reset 근처(같은 라인)로 이동
        recompute = st.button("Recompute ranking")

    # --------------------------------------------------
    # Button actions
    # --------------------------------------------------
    if run_clicked:
        # ✅ Run 시점 Access Key 검증
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
        st.info("Run analysis 버튼을 눌러 분석을 시작하세요.")
        return

    # ==================================================
    # Main layout
    # ==================================================
    left, right = st.columns([1.2, 1.8], gap="large")

    # ==================================================
    # LEFT: Ranking table
    # 요청:
    #  3) Monster 열 폭 줄이고, 왼쪽에 Rank 열 추가
    # ==================================================
    with left:
        # Header
        header = st.columns([0.35, 1.15, 0.9, 0.8])
        header[0].markdown("**Rank**")
        header[1].markdown("**Monster**")
        header[2].markdown("**TOTAL SCORE**")
        header[3].markdown("**Action**")

        for idx, r in enumerate(state.wb_ranking, start=1):
            unit_id = int(r["unit_id"])
            mid = int(r["unit_master_id"])
            name = monster_names.get(mid, f"Unknown ({mid})")

            # Row columns: Rank | Monster | Score | Action
            row = st.columns([0.35, 1.15, 0.9, 0.8], vertical_alignment="center")

            row[0].markdown(f"`{idx}`")
            row[1].markdown(f"`{name}`")
            row[2].markdown(f"`{r['total_score']:.1f}`")

            # ✅ 2) Optimize 버튼 크기 조정: 기본 버튼은 커보이므로
            #     label을 짧게 + CSS로 padding/height 축소
            #     (Streamlit 버튼은 기본적으로 크게 잡힘)
            btn_key = f"opt_{unit_id}"

            row[3].markdown(
                """
                <style>
                div[data-testid="stButton"] > button[kind="secondary"] {
                    padding: 0.25rem 0.6rem;
                    min-height: 2.0rem;
                    line-height: 1.1rem;
                    font-size: 0.9rem;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )

            if row[3].button("Optimize", key=btn_key):
                # (원하면 여기에도 Access gate 걸 수 있음. 지금은 요구사항대로 Run에서만.)
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
