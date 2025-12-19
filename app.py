import copy
import hashlib
import json

import streamlit as st

from config import K_PER_SLOT
from core_scores import score_unit_total, rune_stat_score, unit_base_char
from optimizer import optimize_unit_best_runes, optimize_unit_best_runes_by_unit_id
from ranking import rank_all_units
from visualize import render_optimizer_result

# ============================================================
# Mapping
# ============================================================

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

# ============================================================
# Helpers
# ============================================================

def _hash_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _get_unit_by_unit_id(data, unit_id: int):
    for u in data.get("unit_list", []):
        if int(u.get("unit_id", -1)) == int(unit_id):
            return u
    return None


def _infer_occupied_types(data):
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

    if equipped_type is None:
        equipped_type = 1
    if storage_type is None:
        storage_type = 2

    return equipped_type, storage_type


def _render_current_build(u):
    ch = unit_base_char(u)
    runes = sorted((u.get("runes", []) or []), key=lambda r: int(r.get("slot_no", 0)))
    base_score = []
    for r in runes:
        s, _ = rune_stat_score(r, ch)
        base_score.append(s)
    picked = list(range(len(runes)))
    return ch, runes, picked, base_score


def _apply_build_to_working_data(working_data, unit_id: int, new_runes):
    u = _get_unit_by_unit_id(working_data, unit_id)
    if u is None:
        return False, "Target unit not found."

    equipped_type, storage_type = _infer_occupied_types(working_data)

    old_runes = list(u.get("runes", []) or [])

    def rid(r):
        return r.get("rune_id")

    old_ids = {rid(r) for r in old_runes}
    new_ids = {rid(r) for r in new_runes}

    removed_ids = old_ids - new_ids
    added_ids = new_ids - old_ids

    storage = list(working_data.get("runes", []) or [])
    storage = [r for r in storage if rid(r) not in added_ids]

    removed_runes = [r for r in old_runes if rid(r) in removed_ids]
    storage.extend(removed_runes)

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

    u["runes"] = list(new_runes)
    working_data["runes"] = storage

    return True, "Applied."


def _run_optimizer_for_unit(working_data, unit_id):
    u = _get_unit_by_unit_id(working_data, unit_id)
    if u is None:
        return None

    # BEFORE
    ch0, runes0, picked0, base0 = _render_current_build(u)
    before = score_unit_total(u)
    before_score = before["total_score"] if before else None
    before_text = render_optimizer_result(
        u, ch0, runes0, picked0, base0, final_score=before
    )

    # AFTER
    u1, ch1, runes1, picked1, base1 = optimize_unit_best_runes_by_unit_id(
        working_data, unit_id, K_PER_SLOT
    )

    if u1 is None:
        return {
            "before_text": before_text,
            "before_score": before_score,
            "after_text": "Optimizer: no result.",
            "after_score": None,
            "rec_runes": None,
        }

    rec_runes = [runes1[idx] for idx in picked1]
    u_tmp = copy.deepcopy(u)
    u_tmp["runes"] = rec_runes
    after = score_unit_total(u_tmp)
    after_score = after["total_score"] if after else None
    after_text = render_optimizer_result(
        u1, ch1, runes1, picked1, base1, final_score=after
    )

    return {
        "before_text": before_text,
        "before_score": before_score,
        "after_text": after_text,
        "after_score": after_score,
        "rec_runes": rec_runes,
    }

# ============================================================
# Streamlit UI
# ============================================================

st.set_page_config(page_title="Summoners War Rune Analyzer", layout="wide")
st.title("Summoners War Rune Analyzer")

tab_wb, tab_artifact, tab_siege = st.tabs([
    "World Boss (Rank / Optimizer)",
    "Artifact Analysis",
    "Siege",
])

# ----------------------------
# Access control
# ----------------------------

st.sidebar.header("Access Control")
input_key = st.sidebar.text_input("Access Key", type="password")
AUTHORIZED = False
if input_key:
    if input_key in st.secrets.get("ACCESS_KEYS", []):
        AUTHORIZED = True
        st.sidebar.success("Access granted")
    else:
        st.sidebar.error("Invalid access key")

uploaded = st.file_uploader("Upload JSON file exported from SW", type=["json"])
if uploaded is None:
    st.stop()

raw_bytes = uploaded.getvalue()
file_hash = _hash_bytes(raw_bytes)

parsed_data = json.loads(raw_bytes.decode("utf-8"))

if "data_hash" not in st.session_state or st.session_state.data_hash != file_hash:
    st.session_state.data_hash = file_hash
    st.session_state.original_data = parsed_data
    st.session_state.working_data = copy.deepcopy(parsed_data)
    st.session_state.selected_unit_id = None
    st.session_state.last_apply_msg = None
    st.session_state.last_before_text = None
    st.session_state.last_after_text = None
    st.session_state.last_before_score = None
    st.session_state.last_after_score = None
    st.session_state.last_delta = None
    st.session_state.last_opt_result = None

if not AUTHORIZED:
    st.warning("Enter a valid access key.")
    st.stop()

# ============================================================
# World Boss Tab
# ============================================================

with tab_wb:
    st.subheader("World Boss Analysis")

    if st.button("Run"):
        st.session_state.wb_run = True

    if not st.session_state.get("wb_run", False):
        st.stop()

    left, right = st.columns([1.2, 1.0])

    with left:
        ranking = rank_all_units(st.session_state.working_data, top_n=60)

        for r in ranking:
            unit_id = int(r["unit_id"])
            mid = int(r["unit_master_id"])
            name = MONSTER_NAMES.get(mid, f"Unknown ({mid})")

            col1, col2, col3 = st.columns([1.4, 1.0, 0.7])
            col1.code(name)
            col2.code(f'{r["total_score"]:.1f}')

            if col3.button("Optimize", key=f"opt_{unit_id}"):
                result = _run_optimizer_for_unit(
                    st.session_state.working_data, unit_id
                )
                if result:
                    st.session_state.selected_unit_id = unit_id
                    st.session_state.last_before_text = result["before_text"]
                    st.session_state.last_after_text = result["after_text"]
                    st.session_state.last_before_score = result["before_score"]
                    st.session_state.last_after_score = result["after_score"]
                    st.session_state.last_delta = (
                        result["after_score"] - result["before_score"]
                        if result["after_score"] is not None
                        and result["before_score"] is not None
                        else None
                    )
                    st.session_state.last_opt_result = (
                        unit_id, result["rec_runes"]
                    )

    with right:
        if st.session_state.selected_unit_id is None:
            st.info("Select a unit to optimize.")
        else:
            st.text("Before")
            st.text(st.session_state.last_before_text)

            st.text("After")
            st.text(st.session_state.last_after_text)

            if st.button("Apply"):
                uid, runes = st.session_state.last_opt_result
                ok, msg = _apply_build_to_working_data(
                    st.session_state.working_data, uid, runes
                )
                st.success(msg)
                st.session_state.selected_unit_id = None
