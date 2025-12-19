# app.py
import copy
import hashlib
import json

import streamlit as st

from config import K_PER_SLOT
from core_scores import score_unit_total, rune_stat_score, unit_base_char
from optimizer import optimize_unit_best_runes, optimize_unit_best_runes_by_unit_id
from ranking import rank_all_units
from visualize import render_optimizer_result, render_ranking_result

# ----------------------------
# Mapping
# ----------------------------
@st.cache_resource
def load_monster_names():
    with open("mapping.txt", "r", encoding="utf-8") as f:
        m = json.load(f)
    return {
        int(k): v
        for k, v in m.get("monster", {}).get("names", {}).items()
        if v
    }

MONSTER_NAMES = load_monster_names()

# ----------------------------
# Helpers
# ----------------------------
def _hash_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _get_unit_by_unit_id(data, unit_id: int):
    for u in data.get("unit_list", []):
        if int(u.get("unit_id", -1)) == int(unit_id):
            return u
    return None


def _infer_occupied_types(data):
    """
    Try to infer 'equipped' vs 'storage' occupied_type values from the data
    so we don't hardcode 1/2.
    """
    equipped_type = None
    for u in data.get("unit_list", []):
        for r in (u.get("runes", []) or []):
            if "occupied_type" in r:
                equipped_type = int(r.get("occupied_type"))
                break
        if equipped_type is not None:
            break

    storage_type = None
    for r in (data.get("runes", []) or []):
        if "occupied_type" in r:
            storage_type = int(r.get("occupied_type"))
            break

    # reasonable fallbacks (won't matter if keys absent)
    if equipped_type is None:
        equipped_type = 1
    if storage_type is None:
        storage_type = 2
    return equipped_type, storage_type


def _render_current_build(u):
    """
    Build 'current' view using the SAME optimizer renderer style:
    - runes: current equipped runes (sorted by slot)
    - picked: indices [0..5]
    - base_score: rune_stat_score per rune
    """
    ch = unit_base_char(u)
    runes = sorted((u.get("runes", []) or []), key=lambda r: int(r.get("slot_no", 0)))
    base_score = []
    for r in runes:
        s, _ = rune_stat_score(r, ch)
        base_score.append(s)
    picked = list(range(len(runes)))
    return ch, runes, picked, base_score


def _apply_build_to_working_data(working_data, unit_id: int, new_runes):
    """
    Apply the 6-rune build to the target unit, updating in-memory rune ownership:

    - Remove newly equipped runes from global storage (working_data["runes"]) if present
    - Move displaced old runes back into global storage
    - Update occupied_id / occupied_type for consistency

    Assumptions:
    - Global storage/inventory runes are in working_data["runes"]
    - Equipped runes are in unit["runes"]
    """
    u = _get_unit_by_unit_id(working_data, unit_id)
    if u is None:
        return False, "Target unit not found in working_data."

    equipped_type, storage_type = _infer_occupied_types(working_data)

    old_runes = list(u.get("runes", []) or [])

    # Index by rune_id
    def rid(r):
        return r.get("rune_id")

    old_ids = {rid(r) for r in old_runes}
    new_ids = {rid(r) for r in new_runes}

    # Identify changes
    removed_ids = old_ids - new_ids            # will go to storage
    added_ids = new_ids - old_ids              # likely came from storage

    # Remove added runes from storage list
    storage = list(working_data.get("runes", []) or [])
    if added_ids:
        storage = [r for r in storage if rid(r) not in added_ids]

    # Move removed runes to storage
    removed_runes = [r for r in old_runes if rid(r) in removed_ids]
    storage.extend(removed_runes)

    # Update occupied fields
    for r in new_runes:
        if "occupied_id" in r:
            r["occupied_id"] = int(unit_id)
        if "occupied_type" in r:
            r["occupied_type"] = int(equipped_type)

    for r in removed_runes:
        if "occupied_id" in r:
            r["occupied_id"] = 0
        if "occupied_type" in r:
            r["occupied_type"] = int(storage_type)

    # Commit back
    u["runes"] = list(new_runes)
    working_data["runes"] = storage

    return True, "Applied."


# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="Summoners War Rune Analyzer", layout="wide")
st.title("Summoners War Rune Analyzer")
tab_wb, tab_artifact, tab_siege = st.tabs([
    "World Boss (Rank / Optimizer)",
    "Artifact Analysis",
    "Siege",
])


st.sidebar.header("Access Control")
input_key = st.sidebar.text_input(
    "Access Key",
    type="password",
    help="Enter a valid access key to unlock private features",
)
AUTHORIZED = False
if input_key:
    valid_keys = st.secrets.get("ACCESS_KEYS", [])
    if input_key in valid_keys:
        AUTHORIZED = True
        st.sidebar.success("Access granted")
    else:
        st.sidebar.error("Invalid access key")

st.sidebar.header("Optimizer Settings")
id_type = st.sidebar.radio(
    "Target ID Type (manual optimizer only)",
    ["Unit Master ID (unit_master_id)", "Unit Instance ID (unit_id)"],
    index=0,
    help="This affects ONLY manual optimizer input below. Ranking-click optimizer always uses unit_id.",
)

# Manual optimizer input
target_input = st.sidebar.text_input(
    "Manual Target ID(s) (comma-separated)",
    value="",
    help="Optional: run optimizer directly by these IDs.",
)

TARGET_IDS = []
if target_input.strip():
    try:
        TARGET_IDS = [int(x.strip()) for x in target_input.split(",") if x.strip()]
    except ValueError:
        st.sidebar.error("Please enter valid integer IDs separated by commas.")
        TARGET_IDS = []

uploaded = st.file_uploader("Upload JSON file exported from SW", type=["json"])

if uploaded is None:
    st.info("Please upload a JSON file to start.")
    st.stop()

# Read bytes to detect changes reliably
raw_bytes = uploaded.getvalue()
file_hash = _hash_bytes(raw_bytes)

try:
    parsed_data = json.loads(raw_bytes.decode("utf-8"))
except Exception:
    st.error("Invalid JSON file.")
    st.stop()

# Initialize / reset working state if new file uploaded
if "data_hash" not in st.session_state or st.session_state.data_hash != file_hash:
    st.session_state.data_hash = file_hash
    st.session_state.original_data = parsed_data
    st.session_state.working_data = copy.deepcopy(parsed_data)
    st.session_state.selected_unit_id = None
    st.session_state.last_opt_result = None  # stores (u, ch, runes, picked, base_score)
    st.session_state.last_before_text = None
    st.session_state.last_after_text = None
    st.session_state.last_before_score = None
    st.session_state.last_after_score = None
    st.session_state.last_delta = None
    st.session_state.last_apply_msg = None

if not AUTHORIZED:
    st.warning("Enter a valid access key to enable analysis.")
    st.stop()

if "wb_run" not in st.session_state:
    st.session_state.wb_run = False



with tab_wb:
    st.subheader("World Boss Analysis")

    if st.button("▶ Run"):
        st.session_state.wb_run = True

    
    # Top controls
    top_col1, top_col2, top_col3 = st.columns([1, 1, 3])
    with top_col1:
        if st.button("Reset working state"):
            st.session_state.working_data = copy.deepcopy(st.session_state.original_data)
            st.session_state.selected_unit_id = None
            st.session_state.last_opt_result = None
            st.session_state.last_apply_msg = "Working state reset to original upload."
    with top_col2:
        rerank = st.button("Recompute ranking")
    
    if st.session_state.last_apply_msg:
        st.info(st.session_state.last_apply_msg)

    if not st.session_state.wb_run:
        st.info("Mode를 선택한 후 Run을 눌러주세요.")
        st.stop()

    # 기존 코드 그대로 ↓
    left, right = st.columns([1.2, 1.0], gap="large")
    
    with left:
        st.subheader("Ranking (Top 60) — click Optimize")
        with st.spinner("Calculating ranking..."):
            ranking = rank_all_units(st.session_state.working_data, top_n=60)
    
        # Render as interactive list with buttons
        header = st.columns([1.4, 1.0, 0.7])
        header[0].markdown("**Monster**")
        header[1].markdown("**TOTAL SCORE**")
        header[2].markdown("**Action**")
    
        for i, r in enumerate(ranking, start=1):
            row = st.columns([1.4, 1.0, 0.7])
            mid = int(r["unit_master_id"])
            name = MONSTER_NAMES.get(mid, f"Unknown ({mid})")           
            row[0].code(name, language=None)
            row[1].code(f'{r["total_score"]:.1f}', language=None)
    
            if row[2].button("Optimize", key=f"opt_{r['unit_id']}"):
                unit_id = int(r["unit_id"])
                st.session_state.selected_unit_id = unit_id
    
                # BEFORE snapshot (current)
                u = _get_unit_by_unit_id(st.session_state.working_data, unit_id)
                if u is None:
                    st.session_state.last_apply_msg = f"unit_id {unit_id} not found."
                else:
                    before = score_unit_total(u)
                    before_score = before["total_score"] if before else None
    
                    ch0, runes0, picked0, base0 = _render_current_build(u)
                    before_text = render_optimizer_result(u, ch0, runes0, picked0, base0)
    
                    # AFTER (optimized) — always unit_id based pool (equipped + storage), +15 only
                    u1, ch1, runes1, picked1, base1 = optimize_unit_best_runes_by_unit_id(
                        st.session_state.working_data, unit_id, K_PER_SLOT
                    )
                    after_text = None
                    after_score = None
    
                    if u1 is not None:
                        # compute score for this recommended build quickly by reusing the same scorer:
                        # (We will compute after_score by temporarily evaluating with those runes
                        # WITHOUT permanently applying.)
                        # Safer approach: copy unit shallowly for scoring.
                        u_tmp = copy.deepcopy(u)
                        # build recommended 6 runes list from runes1/picked1
                        rec_runes = [runes1[idx] for idx in picked1]
                        u_tmp["runes"] = rec_runes
                        after = score_unit_total(u_tmp)
                        after_score = after["total_score"] if after else None
                        after_text = render_optimizer_result(u1, ch1, runes1, picked1, base1)
    
                        st.session_state.last_opt_result = (unit_id, rec_runes)
                        st.session_state.last_before_text = before_text
                        st.session_state.last_after_text = after_text
                        st.session_state.last_before_score = before_score
                        st.session_state.last_after_score = after_score
                        if before_score is not None and after_score is not None:
                            st.session_state.last_delta = after_score - before_score
                        else:
                            st.session_state.last_delta = None
    
                    else:
                        st.session_state.last_opt_result = None
                        st.session_state.last_before_text = before_text
                        st.session_state.last_after_text = "Optimizer: target not found / no result."
                        st.session_state.last_before_score = before_score
                        st.session_state.last_after_score = None
                        st.session_state.last_delta = None
    
        st.divider()
    
        # Manual optimizer run (kept for convenience)
        st.subheader("Manual Optimizer")
        if st.button("Run manual optimizer"):
            for tid in TARGET_IDS:
                if id_type.startswith("Unit Master"):
                    u, ch, runes, picked, base_score = optimize_unit_best_runes(
                        st.session_state.working_data, tid, K_PER_SLOT
                    )
                    st.text(render_optimizer_result(u, ch, runes, picked, base_score))
                else:
                    u, ch, runes, picked, base_score = optimize_unit_best_runes_by_unit_id(
                        st.session_state.working_data, tid, K_PER_SLOT
                    )
                    st.text(render_optimizer_result(u, ch, runes, picked, base_score))
    
    with right:
        st.subheader("Optimizer Panel (Before vs After)")
    
        if st.session_state.selected_unit_id is None:
            st.info("왼쪽 Ranking에서 유닛을 선택해 Optimize를 누르시면, 여기서 비교/적용이 가능합니다.")
        else:
            unit_id = st.session_state.selected_unit_id
    
            # Score summary
            b = st.session_state.last_before_score
            a = st.session_state.last_after_score
            d = st.session_state.last_delta

            u = _get_unit_by_unit_id(st.session_state.working_data, unit_id)
            mid = int(u.get("unit_master_id"))
            name = MONSTER_NAMES.get(mid, f"Unknown ({mid})")            
            summary = []
            summary.append(f"Selected Monster: {name}")
            if b is not None:
                summary.append(f"Before score: {b:.1f}")
            if a is not None:
                summary.append(f"After score:  {a:.1f}")
            if d is not None:
                summary.append(f"Delta:       {d:+.1f}")
            st.code("\n".join(summary), language=None)
    
            colA, colB = st.columns(2, gap="medium")
            with colA:
                st.markdown("### Before (current equipped)")
                if st.session_state.last_before_text:
                    st.text(st.session_state.last_before_text)
            with colB:
                st.markdown("### After (recommended)")
                if st.session_state.last_after_text:
                    st.text(st.session_state.last_after_text)
    
            st.divider()
    
            # Apply / Cancel
            apply_col1, apply_col2 = st.columns([1, 1])
            with apply_col1:
                if st.button("✅ Apply this build", key="apply_build"):
                    if st.session_state.last_opt_result is None:
                        st.session_state.last_apply_msg = "No optimizer result to apply."
                    else:
                        uid, rec_runes = st.session_state.last_opt_result
                        ok, msg = _apply_build_to_working_data(
                            st.session_state.working_data, uid, rec_runes
                        )
                        st.session_state.last_apply_msg = msg if ok else f"Failed: {msg}"
    
                        # After applying, clear selection so user can click another unit smoothly
                        st.session_state.selected_unit_id = None
                        st.session_state.last_opt_result = None
                        st.session_state.last_before_text = None
                        st.session_state.last_after_text = None
                        st.session_state.last_before_score = None
                        st.session_state.last_after_score = None
                        st.session_state.last_delta = None
    
            with apply_col2:
                if st.button("Cancel / Clear panel", key="clear_panel"):
                    st.session_state.selected_unit_id = None
                    st.session_state.last_opt_result = None
                    st.session_state.last_before_text = None
                    st.session_state.last_after_text = None
                    st.session_state.last_before_score = None
                    st.session_state.last_after_score = None
                    st.session_state.last_delta = None
                    st.session_state.last_apply_msg = "Cleared."
