import copy
import hashlib
import json
from pathlib import Path

import streamlit as st

from ui.auth import require_access_or_stop

from ui.wb_tab import show_wb_tab
from ui.siege_logs import show_siege_tab
from ui.siege_defense import show_siege_defense_tab
from ui.worst_offense import show_worst_offense_tab
from services.artifact_analysis import (
    collect_all_artifacts,
    artifact_attribute_matrix,
    artifact_archetype_matrix,
)
from ui.artifact_render import show_matrix


RESOURCES_DIR = Path(__file__).resolve().parent / "resources"

def hash_bytes(b: bytes) -> str:
    """Return a stable hash for uploaded bytes to detect changes."""
    return hashlib.sha256(b).hexdigest()


@st.cache_resource
def load_monster_names():
    """Load the monster name mapping from the bundled resource file."""
    mapping_path = RESOURCES_DIR / "mapping.txt"
    with mapping_path.open("r", encoding="utf-8") as f:
        return {
            int(k): v
            for k, v in json.load(f)["monster"]["names"].items()
            if v
        }

st.set_page_config(page_title="Summoners War Analyzer", layout="wide")
st.title("Summoners War Analyzer")

st.sidebar.header("Access Control")
st.sidebar.text_input(
    "Access Key",
    type="password",
    key="access_key_input",
    help="Enter a valid access key to unlock private features",
)

tab_wb, tab_artifact, tab_siege, tab_siege_def, tab_worst = st.tabs([
    "World Boss",
    "Artifact Analysis",
    "Siege Battle",
    "Siege Defense",
    "Worst Offense"
])


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

            st.session_state.wb_run = False
            st.session_state.wb_ranking = None
            st.session_state.selected_unit_id = None
            st.session_state.opt_ctx = None

        show_wb_tab(st.session_state, load_monster_names())

with tab_artifact:
    st.subheader("Artifact Analysis")

    uploaded_art = st.file_uploader(
        "Upload JSON file exported from SW",
        type=["json"],
        key="artifact_json",
    )

    run_art = st.button("Run analysis", type="primary", key="artifact_run")

    if run_art:
        if require_access_or_stop("artifact"):
            if uploaded_art is None:
                st.error("JSON 파일을 업로드해 주세요.")
                st.stop()
    
            raw = uploaded_art.getvalue()
            data = json.loads(raw.decode("utf-8"))
    
            all_arts = collect_all_artifacts(data)
    
            df_attr = artifact_attribute_matrix(all_arts, top_n=3)
            show_matrix(df_attr, label_cols=["Attribute", "Main"], title="Attribute Matrix")
    
            st.divider()
    
            df_arch = artifact_archetype_matrix(all_arts, top_n=3)
            show_matrix(df_arch, label_cols=["Archetype", "Main"], title="Archetype Matrix")

with tab_siege:
    show_siege_tab()

with tab_siege_def:
    show_siege_defense_tab()

with tab_worst:
    show_worst_offense_tab()
