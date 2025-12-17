# app.py
import streamlit as st
import json

from config import TARGET_MASTER_IDS, K_PER_SLOT
from optimizer import optimize_unit_best_runes
from ranking import rank_all_units
from visualize import (render_optimizer_result, render_ranking_result)

st.set_page_config(page_title="Rune Analyzer", layout="wide")

st.title("Summoners War Rune Analyzer")

# ----------------------------
# Input target
# ----------------------------
st.sidebar.header("Optimizer Settings")

target_input = st.sidebar.text_input(
    "Target Unit Master ID(s)",
    value="",
    help="Enter one or more unit_master_id values, separated by commas (e.g. 21511,23111)"
)

if target_input.strip():
    try:
        TARGET_MASTER_IDS = [
            int(x.strip()) for x in target_input.split(",") if x.strip()
        ]
    except ValueError:
        st.sidebar.error("Please enter valid integer IDs separated by commas.")
        TARGET_MASTER_IDS = []
else:
    TARGET_MASTER_IDS = []


# ----------------------------
# Upload
# ----------------------------
uploaded = st.file_uploader("Upload JSON file exported from SW", type=["json"])

# ----------------------------
# Mode selection
# ----------------------------
mode = st.radio("Select Mode", ["Optimizer", "Ranking", "Both"],
                horizontal=True)


# ----------------------------
# Run
# ----------------------------
if uploaded is not None:
    try:
        data = json.load(uploaded)
    except Exception as e:
        st.error("Invalid JSON file")
        st.stop()

    if st.button("Run Analysis"):
        # -------- Optimizer --------
        if mode in ("Optimizer", "Both"):
            st.subheader("Optimizer Result")

            for mid in TARGET_MASTER_IDS:
                with st.spinner("Running optimizer..."):
                    result = optimize_unit_best_runes(data, mid, K_PER_SLOT)

                if result is None:
                    st.warning(f"Unit master_id {mid} not found")
                    continue

                u, ch, runes, picked, base_score = result
                text = render_optimizer_result(u, ch, runes, picked,
                                               base_score)
                st.text(text)

        # -------- Ranking --------
        if mode in ("Ranking", "Both"):
            st.subheader("Current Ranking (Top 60)")

            with st.spinner("Calculating ranking..."):
                results = rank_all_units(data, top_n=60)

            text = render_ranking_result(results, top_n=60)
            st.text(text)

else:
    st.info("Please upload a JSON file to start.")
