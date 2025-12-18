import json
import hashlib
import streamlit as st

from config import K_PER_SLOT
from ranking import rank_all_units
from optimizer import optimize_unit_best_runes
from visualize import render_optimizer_result


# ----------------------------
# Helpers
# ----------------------------
def _hash_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="Summoners War Analyzer", layout="wide")
st.title("Summoners War Analyzer")

# ----------------------------
# JSON Upload (always on top)
# ----------------------------
uploaded = st.file_uploader("Upload JSON file exported from SW", type=["json"])

if uploaded is None:
    st.info("Please upload a JSON file to start.")
    st.stop()

raw_bytes = uploaded.getvalue()
file_hash = _hash_bytes(raw_bytes)

try:
    data = json.loads(raw_bytes.decode("utf-8"))
except Exception:
    st.error("Invalid JSON file.")
    st.stop()

# ----------------------------
# Tabs
# ----------------------------
tab_wb, tab_artifact, tab_siege = st.tabs([
    "World Boss",
    "Artifact Analysis",
    "Siege",
])

# ======================================================
# World Boss
# ======================================================
with tab_wb:
    st.subheader("World Boss")

    wb_mode = st.radio(
        "Mode",
        ["Ranking", "Optimizer"],
        horizontal=True
    )

    run = st.button("▶ Run")

    if not run:
        st.info("Mode를 선택한 후 Run을 눌러주세요.")
        st.stop()

    st.divider()

    # -------------------------
    # Ranking Mode
    # -------------------------
    if wb_mode == "Ranking":
        st.markdown("### Ranking (Top 60)")

        with st.spinner("Calculating ranking..."):
            ranking = rank_all_units(data, top_n=60)

        header = st.columns([1, 1, 1])
        header[0].markdown("**unit_id**")
        header[1].markdown("**unit_master_id**")
        header[2].markdown("**TOTAL SCORE**")

        for r in ranking:
            row = st.columns([1, 1, 1])
            row[0].code(str(r["unit_id"]), language=None)
            row[1].code(str(r["unit_master_id"]), language=None)
            row[2].code(f'{r["total_score"]:.1f}', language=None)

    # -------------------------
    # Optimizer Mode (legacy / original behavior)
    # -------------------------
    else:
        st.markdown("### Optimizer (Storage Runes Only)")

        unit_master_id_input = st.text_input(
            "Unit Master ID",
            help="Enter unit_master_id (e.g. 229 for Cannon Girl)"
        )

        if not unit_master_id_input.strip():
            st.info("unit_master_id를 입력하세요.")
            st.stop()

        try:
            unit_master_id = int(unit_master_id_input)
        except ValueError:
            st.error("unit_master_id must be an integer.")
            st.stop()

        with st.spinner("Optimizing..."):
            u, ch, runes, picked, base_score = optimize_unit_best_runes(
                data,
                unit_master_id,
                K_PER_SLOT
            )

        if u is None:
            st.warning("No optimization result found.")
        else:
            result_text = render_optimizer_result(
                u, ch, runes, picked, base_score
            )
            st.text(result_text)


# ======================================================
# Artifact Analysis
# ======================================================
with tab_artifact:
    st.subheader("Artifact Analysis")
    st.info("Artifact analysis UI will be restored here (existing code).")


# ======================================================
# Siege
# ======================================================
with tab_siege:
    st.subheader("Siege")
    st.info("Coming soon.")
