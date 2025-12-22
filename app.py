import copy
import hashlib
import json
import streamlit as st

from ui.wb_tab import render_wb_tab
from siege_logs import render_siege_tab
from ui.auth import require_access_or_stop

from artifact_analysis import (
    collect_all_artifacts,
    artifact_attribute_summary,
    artifact_archetype_summary,
)
from ui.artifact_render import render_google_style


# ============================================================
# Utils
# ============================================================

def hash_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


@st.cache_resource
def load_monster_names():
    with open("mapping.txt", "r", encoding="utf-8") as f:
        return {
            int(k): v
            for k, v in json.load(f)["monster"]["names"].items()
            if v
        }

# ============================================================
# Streamlit App
# ============================================================

st.set_page_config(page_title="Summoners War Rune Analyzer", layout="wide")
st.title("Summoners War Rune Analyzer")

# ------------------------------------------------------------
# Sidebar: Access Key Input
# ------------------------------------------------------------

st.sidebar.header("Access Control")
st.sidebar.text_input(
    "Access Key",
    type="password",
    key="access_key_input",
    help="Enter a valid access key to unlock private features",
)

# ------------------------------------------------------------
# Tabs
# ------------------------------------------------------------

tab_wb, tab_artifact, tab_siege = st.tabs(
    ["World Boss", "Artifact Analysis", "Siege Battle"]
)

# ------------------------------------------------------------
# World Boss Tab
# ------------------------------------------------------------

with tab_wb:
    st.subheader("World Boss")

    uploaded = st.file_uploader("Upload JSON file exported from SW", type=["json"], key="wb_json")

    if uploaded is None:
        st.info("Please upload a JSON file to start.")
    else:
        raw = uploaded.getvalue()
        data = json.loads(raw.decode("utf-8"))
        data_hash = hash_bytes(raw)

        if "data_hash" not in st.session_state or st.session_state.data_hash != data_hash:
            st.session_state.data_hash = data_hash
            st.session_state.original_data = data
            st.session_state.working_data = copy.deepcopy(data)

            # World Boss state
            st.session_state.wb_run = False
            st.session_state.wb_ranking = None
            st.session_state.selected_unit_id = None
            st.session_state.opt_ctx = None

        render_wb_tab(st.session_state, load_monster_names())


# ------------------------------------------------------------
# Artifact Tab
# ------------------------------------------------------------

with tab_artifact:
    st.subheader("Artifact Analysis")

    uploaded = st.file_uploader(
        "Upload JSON file exported from SW",
        type=["json"],
        key="artifact_json",
    )

    run_art = st.button("Run analysis", type="primary", key="artifact_run")

    if run_art:
        require_access_or_stop("Artifact analysis")

        if uploaded is None:
            st.error("JSON 파일을 업로드해 주세요.")
            st.stop()

        raw = uploaded.getvalue()
        data = json.loads(raw.decode("utf-8"))

        all_arts = collect_all_artifacts(data)
        df_attr = artifact_attribute_summary(all_arts)
        df_arch = artifact_archetype_summary(all_arts)

        # 여기서 "색칠된 테이블" 렌더링 호출
        render_google_style(df_attr, label_cols=["Attribute","Main"], value_cols=["Fire","Water","Wind","Light","Dark"])
        st.divider()
        render_google_style(df_arch, label_cols=["Archetype","Main"], value_cols=["SPD_INC","S1_REC","S2_REC","S3_REC","S1_ACC","S2_ACC","S3_ACC"])



# ------------------------------------------------------------
# Siege Tab
# ------------------------------------------------------------

with tab_siege:
    render_siege_tab()
