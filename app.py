import copy
import hashlib
import json
import streamlit as st

from ui.wb_tab import render_wb_tab
from siege_logs import render_siege_tab

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
# Access Control (복구됨)
# ------------------------------------------------------------

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

if not AUTHORIZED:
    st.warning("Enter a valid access key to enable analysis.")
    st.stop()

# ------------------------------------------------------------
# File Upload
# ------------------------------------------------------------

uploaded = st.file_uploader("Upload JSON file exported from SW", type=["json"])
if uploaded is None:
    st.info("Please upload a JSON file to start.")
    st.stop()

raw = uploaded.getvalue()
data = json.loads(raw.decode("utf-8"))
data_hash = hash_bytes(raw)

# ------------------------------------------------------------
# Session State Init
# ------------------------------------------------------------

if "data_hash" not in st.session_state or st.session_state.data_hash != data_hash:
    st.session_state.data_hash = data_hash
    st.session_state.original_data = data
    st.session_state.working_data = copy.deepcopy(data)

    # World Boss state
    st.session_state.wb_run = False
    st.session_state.wb_ranking = None
    st.session_state.selected_unit_id = None
    st.session_state.opt_ctx = None
    

# ------------------------------------------------------------
# Tabs
# ------------------------------------------------------------

tab_wb, tab_artifact, tab_siege = st.tabs(
    ["World Boss (Rank / Optimizer)", "Artifact Analysis", "Siege"]
)

with tab_wb:
    render_wb_tab(st.session_state, load_monster_names())

with tab_artifact:
    st.info("Artifact Analysis – WIP")

with tab_siege:
    render_siege_tab()
