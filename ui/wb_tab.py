import copy
import json
from collections import defaultdict

import pandas as pd
import streamlit as st

from config import K_PER_SLOT, SET_EFFECTS, SKILLUP_COEF, STAT_COEF, STAT_KEYS
from domain.coef_calibrator import build_calib_items, calibrate_rank60
from domain.core_scores import score_unit_total, unit_base_char
from domain.optimizer import optimize_unit_best_runes
from domain.ranking import rank_all_units
from domain.unit_repo import apply_build_to_working_data
from domain.visualize import render_optimizer_result
from services.wb_service import run_optimizer_for_unit
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
        st.info("Click Run analysis to start.")
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

        st.divider()
        with st.expander("Calibration (Rank-60)", expanded=False):
            st.caption("Current Top 60 list (use unit_id to map true ranks)")
            top_rows = []
            ranking_map = {}
            top_ranking = state.wb_ranking[:60]
            for idx, r in enumerate(top_ranking, start=1):
                unit_id = int(r["unit_id"])
                ranking_map[unit_id] = {**r, "pred_rank": idx}
                top_rows.append(
                    {
                        "pred_rank": idx,
                        "unit_id": unit_id,
                        "unit_master_id": int(r.get("unit_master_id", 0)),
                        "total_score": float(r.get("total_score", 0.0)),
                    }
                )

            top_df = pd.DataFrame(top_rows)
            st.dataframe(top_df, use_container_width=True, hide_index=True)

            st.markdown("#### True ranking input (unit_id order)")
            st.markdown(
                "Workflow: copy the predicted unit_id list, reorder it to match TRUE ranks, "
                "then run calibration."
            )
            fill_pred = st.button("Fill from predicted order")
            if fill_pred:
                st.session_state.calib_true_text = "\n".join(
                    str(row["unit_id"]) for row in top_rows
                )

            true_text = st.text_area(
                "Paste unit_id order for TRUE ranks 1..60 (one per line or comma-separated).",
                key="calib_true_text",
                height=200,
            )

            def _parse_true_order(raw_text: str):
                cleaned = raw_text.replace(",", "\n")
                tokens = [tok.strip() for tok in cleaned.splitlines()]
                tokens = [tok for tok in tokens if tok]
                order = []
                seen = set()
                duplicates = []
                invalid = []
                for tok in tokens:
                    try:
                        unit_id = int(tok)
                    except ValueError:
                        invalid.append(tok)
                        continue
                    if unit_id in seen:
                        duplicates.append(unit_id)
                        continue
                    seen.add(unit_id)
                    order.append(unit_id)
                return order, duplicates, invalid

            true_order, dup_ids, invalid_tokens = _parse_true_order(true_text)
            if invalid_tokens:
                st.error(f"Invalid unit_id values: {', '.join(invalid_tokens)}")
            if dup_ids:
                dup_display = ", ".join(str(uid) for uid in dup_ids)
                st.warning(f"Duplicate unit_id entries ignored: {dup_display}")

            top_unit_ids = {row["unit_id"] for row in top_rows}
            valid_true_map = None
            if true_order:
                missing_from_top = [uid for uid in top_unit_ids if uid not in true_order]
                extra_ids = [uid for uid in true_order if uid not in top_unit_ids]
                if len(true_order) != 60:
                    st.error(f"Expected 60 unit_ids, got {len(true_order)}.")
                elif extra_ids:
                    st.error(
                        "These unit_ids are not in the current Top 60: "
                        + ", ".join(str(uid) for uid in extra_ids)
                    )
                elif missing_from_top:
                    st.error(
                        "Missing unit_ids from the current Top 60: "
                        + ", ".join(str(uid) for uid in missing_from_top)
                    )
                else:
                    valid_true_map = {uid: idx + 1 for idx, uid in enumerate(true_order)}

            if valid_true_map:
                st.session_state.calib_true_order = true_order
                st.session_state.calib_true_rank_map = valid_true_map
                confirm_rows = []
                for unit_id in true_order:
                    pred_row = ranking_map[unit_id]
                    confirm_rows.append(
                        {
                            "true_rank": valid_true_map[unit_id],
                            "unit_id": unit_id,
                            "pred_rank": int(pred_row.get("pred_rank", 0)) if "pred_rank" in pred_row else None,
                            "total_score": float(pred_row.get("total_score", 0.0)),
                        }
                    )
                confirm_df = pd.DataFrame(confirm_rows)
                st.markdown("##### True ranking confirmation")
                st.dataframe(confirm_df, use_container_width=True, hide_index=True)

            st.markdown("#### Calibration Controls")
            iter_col, seed_col, step_col = st.columns(3)
            with iter_col:
                iterations = st.number_input(
                    "Iterations",
                    min_value=500,
                    max_value=30000,
                    value=3000,
                    step=500,
                )
            with seed_col:
                seed = st.number_input("Seed", min_value=0, max_value=999999, value=7, step=1)
            with step_col:
                step0 = st.number_input("Step0", min_value=0.01, max_value=50.0, value=1.0, step=0.05)

            reg_col1, reg_col2, reg_col3 = st.columns(3)
            with reg_col1:
                lambda_stat = st.number_input("λ_stat", min_value=0.0, max_value=1.0, value=0.0001, step=0.0001, format="%.5f")
            with reg_col2:
                lambda_fixed = st.number_input("λ_fixed", min_value=0.0, max_value=1.0, value=0.0001, step=0.0001, format="%.5f")
            with reg_col3:
                lambda_su = st.number_input("λ_su", min_value=0.0, max_value=1.0, value=0.0001, step=0.0001, format="%.5f")

            run_calib = st.button("Run calibration", type="primary")

            if run_calib:
                true_rank_map = st.session_state.get("calib_true_rank_map")
                true_order_ids = st.session_state.get("calib_true_order")
                if not true_rank_map or not true_order_ids:
                    st.error("Provide a valid 60-unit true ranking order before running calibration.")
                    st.stop()

                fixed_set_ids = [10, 11, 13, 14, 15, 16, 17, 18, 22, 23, 24]
                unit_map = {int(u.get("unit_id", 0)): u for u in state.working_data.get("unit_list", [])}
                calib_rows = []

                for unit_id in true_order_ids:
                    unit_id = int(unit_id)
                    unit = unit_map.get(unit_id)
                    if not unit:
                        continue

                    base_stats = unit_base_char(unit)

                    rune_set_counts = defaultdict(int)
                    for r in unit.get("runes", []) or []:
                        rune_set_counts[int(r.get("set_id", 0))] += 1

                    fixed_counts = {}
                    for sid in fixed_set_ids:
                        cfg = SET_EFFECTS.get(int(sid))
                        if not cfg:
                            continue
                        need = int(cfg.get("need", 0))
                        if need <= 0:
                            continue
                        times = rune_set_counts.get(int(sid), 0) // need
                        if need >= 4:
                            times = min(times, 1)
                        if times > 0:
                            fixed_counts[int(sid)] = int(times)

                    skillup_count = 0
                    for skill in unit.get("skills", []) or []:
                        if isinstance(skill, list) and len(skill) >= 2:
                            skillup_count += max(0, int(skill[1]) - 1)

                    calib_rows.append(
                        {
                            "unit_id": unit_id,
                            "true_rank": int(true_rank_map[unit_id]),
                            "stats": base_stats,
                            "fixed_counts": fixed_counts,
                            "skillup_count": skillup_count,
                        }
                    )

                calib_items = build_calib_items(calib_rows, STAT_KEYS)
                init_fixed = {sid: float(SET_EFFECTS[sid]["fixed"]) for sid in fixed_set_ids}

                result = calibrate_rank60(
                    items=calib_items,
                    stat_keys=STAT_KEYS,
                    fixed_ids=fixed_set_ids,
                    init_stat_coef=STAT_COEF,
                    init_fixed_map=init_fixed,
                    init_skillup_coef=SKILLUP_COEF,
                    iterations=int(iterations),
                    seed=int(seed),
                    step0=float(step0),
                    lambdas=(float(lambda_stat), float(lambda_fixed), float(lambda_su)),
                )

                summary = result["summary"]
                st.subheader("Calibration Summary")
                st.write(
                    {
                        "objective": summary["objective"],
                        "pairwise_loss": summary["pairwise_loss"],
                        "concordance": summary["concordance"],
                        "iterations": summary["iterations"],
                    }
                )

                def _delta_pct(init_val: float, tuned_val: float) -> float:
                    if init_val == 0:
                        return 0.0
                    return (tuned_val - init_val) / init_val * 100.0

                stat_rows = []
                for key in STAT_KEYS:
                    init_val = float(STAT_COEF[key])
                    tuned_val = float(result["STAT_COEF"][key])
                    stat_rows.append(
                        {
                            "stat": key,
                            "init": init_val,
                            "tuned": tuned_val,
                            "delta_pct": _delta_pct(init_val, tuned_val),
                        }
                    )
                st.markdown("##### STAT_COEF")
                st.dataframe(pd.DataFrame(stat_rows), use_container_width=True, hide_index=True)

                fixed_rows = []
                for sid in fixed_set_ids:
                    init_val = float(init_fixed[sid])
                    tuned_val = float(result["SET_FIXED"][sid])
                    fixed_rows.append(
                        {
                            "set_id": sid,
                            "init": init_val,
                            "tuned": tuned_val,
                            "delta_pct": _delta_pct(init_val, tuned_val),
                        }
                    )
                st.markdown("##### SET_FIXED")
                st.dataframe(pd.DataFrame(fixed_rows), use_container_width=True, hide_index=True)

                su_init = float(SKILLUP_COEF)
                su_tuned = float(result["SKILLUP_COEF"])
                st.markdown("##### SKILLUP_COEF")
                st.write(
                    {
                        "init": su_init,
                        "tuned": su_tuned,
                        "delta_pct": _delta_pct(su_init, su_tuned),
                    }
                )

                download_payload = {
                    "STAT_COEF": result["STAT_COEF"],
                    "SET_FIXED": {str(k): v for k, v in result["SET_FIXED"].items()},
                    "SKILLUP_COEF": result["SKILLUP_COEF"],
                    "summary": summary,
                }
                download_json = json.dumps(download_payload, indent=2)
                st.download_button(
                    "Download calibrated_coefs.json",
                    data=download_json,
                    file_name="calibrated_coefs.json",
                    mime="application/json",
                )
                st.markdown("##### Copy/paste snippet")
                st.code(download_json, language="json")

                post_rows = []
                tuned_stat = result["STAT_COEF"]
                tuned_fixed = result["SET_FIXED"]
                tuned_skill = float(result["SKILLUP_COEF"])
                for row in calib_rows:
                    unit_id = int(row["unit_id"])
                    pred_info = ranking_map.get(unit_id, {})
                    tuned_score = 0.0
                    for key in STAT_KEYS:
                        tuned_score += float(row["stats"].get(key, 0.0)) * float(tuned_stat[key])
                    for sid, count in row["fixed_counts"].items():
                        tuned_score += int(count) * float(tuned_fixed[int(sid)])
                    tuned_score += int(row["skillup_count"]) * tuned_skill

                    original_total = float(pred_info.get("total_score", 0.0))
                    post_rows.append(
                        {
                            "unit_id": unit_id,
                            "unit_master_id": int(pred_info.get("unit_master_id", 0)),
                            "pred_rank": int(pred_info.get("pred_rank", 0)),
                            "true_rank": int(row["true_rank"]),
                            "original_total_score": original_total,
                            "tuned_score": tuned_score,
                            "score_delta": tuned_score - original_total,
                        }
                    )

                post_rows.sort(key=lambda x: x["tuned_score"], reverse=True)
                for idx, row in enumerate(post_rows, start=1):
                    row["tuned_rank"] = idx

                post_df = pd.DataFrame(
                    [
                        {
                            "tuned_rank": row["tuned_rank"],
                            "true_rank": row["true_rank"],
                            "pred_rank": row["pred_rank"],
                            "unit_id": row["unit_id"],
                            "unit_master_id": row["unit_master_id"],
                            "tuned_score": row["tuned_score"],
                            "score_delta": row["score_delta"],
                        }
                        for row in post_rows
                    ]
                )

                st.subheader("Post-calibration Rank (Top 60)")
                st.dataframe(post_df, use_container_width=True, hide_index=True)

    # ==================================================
    # RIGHT: Optimizer Panel
    # ==================================================
    with right:
        if state.selected_unit_id is None or state.opt_ctx is None:
            st.info("Click Optimize on the left.")
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
