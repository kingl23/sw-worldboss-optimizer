import streamlit as st
from copy import deepcopy

from io_utils import load_json_data
from ranking import rank_all_units
from optimizer import optimize_unit
from artifact_analysis import run_artifact_analysis

# ======================================================
# Page Config
# ======================================================
st.set_page_config(layout="wide")

# ======================================================
# Session State Init
# ======================================================
if "worldboss" not in st.session_state:
    st.session_state.worldboss = {
        "raw_data": None,
        "working_data": None,
        "mode": None,
        "analysis_done": False,
        "selected_unit_id": None,
    }

# ======================================================
# Tabs
# ======================================================
tabs = st.tabs(["World Boss", "Artifact Analysis", "Siege"])

# ======================================================
# World Boss TAB
# ======================================================
with tabs[0]:
    st.header("World Boss")

    # ---------- JSON Upload ----------
    uploaded = st.file_uploader(
        "Upload World Boss JSON",
        type=["json"],
        key="wb_json"
    )

    if uploaded:
        st.session_state.worldboss["raw_data"] = load_json_data(uploaded)
        st.session_state.worldboss["working_data"] = None
        st.session_state.worldboss["analysis_done"] = False
        st.session_state.worldboss["selected_unit_id"] = None

    if not st.session_state.worldboss["raw_data"]:
        st.info("Please upload a JSON file to begin.")
        st.stop()

    # ---------- Mode Select ----------
    st.session_state.worldboss["mode"] = st.radio(
        "Mode",
        ["Ranking", "Optimizer"],
        horizontal=True
    )

    # ---------- Run Button ----------
    if st.button("Run World Boss Analysis"):
        st.session_state.worldboss["working_data"] = deepcopy(
            st.session_state.worldboss["raw_data"]
        )
        st.session_state.worldboss["analysis_done"] = True
        st.session_state.worldboss["selected_unit_id"] = None

    if not st.session_state.worldboss["analysis_done"]:
        st.stop()

    # ==================================================
    # Ranking Mode (Click Optimizer)
    # ==================================================
    if st.session_state.worldboss["mode"] == "Ranking":
        left, right = st.columns([2.3, 1.7])

        with left:
            st.subheader("Ranking")

            ranking = rank_all_units(
                st.session_state.worldboss["working_data"]
            )

            for r in ranking:
                cols = st.columns([3, 1])
                cols[0].markdown(
                    f"**{r['name']}**  \nScore: `{r['score']}`"
                )
                if cols[1].button(
                    "Optimize",
                    key=f"rank_opt_{r['unit_id']}"
                ):
                    st.session_state.worldboss["selected_unit_id"] = r["unit_id"]

        with right:
            if st.session_state.worldboss["selected_unit_id"]:
                unit_id = st.session_state.worldboss["selected_unit_id"]
                st.subheader("Optimizer")

                result = optimize_unit(
                    st.session_state.worldboss["working_data"],
                    unit_id=unit_id,
                    rune_limit=150000
                )

                # ----- Current -----
                st.markdown("### Current Runes")
                st.write(result["current_runes"])
                st.markdown(
                    f"Score: **{result['current_score']}**"
                )

                st.markdown("---")

                # ----- Recommended -----
                st.markdown("### Recommended Runes")
                st.write(result["recommended_runes"])
                st.markdown(
                    f"Score: **{result['recommended_score']}**"
                )

                # ----- Apply -----
                if st.button("Apply Rune Change"):
                    st.session_state.worldboss["working_data"] = result["updated_data"]
                    st.success("Runes applied successfully!")

    # ==================================================
    # Optimizer Mode (기존 방식)
    # ==================================================
    else:
        st.subheader("Optimizer")

        unit_id = st.text_input("Enter Unit ID")
        if st.button("Optimize Unit"):
            if not unit_id.isdigit():
                st.error("Unit ID must be a number.")
            else:
                result = optimize_unit(
                    st.session_state.worldboss["working_data"],
                    unit_id=int(unit_id),
                    rune_limit=150000
                )
                st.write(result)

# ======================================================
# Artifact Analysis TAB
# ======================================================
with tabs[1]:
    st.header("Artifact Analysis")

    uploaded = st.file_uploader(
        "Upload JSON for Artifact Analysis",
        type=["json"],
        key="artifact_json"
    )

    if uploaded:
        artifact_data = load_json_data(uploaded)

        if st.button("Run Artifact Analysis"):
            result = run_artifact_analysis(artifact_data)
            st.write(result)

# ======================================================
# Siege TAB
# ======================================================
with tabs[2]:
    st.header("Siege")
    st.info("Siege analysis will be added here.")
