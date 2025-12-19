import copy
import hashlib
import json
import streamlit as st
from ui.wb_tab import render_wb_tab

@st.cache_resource
def load_monster_names():
    with open("mapping.txt", "r", encoding="utf-8") as f:
        return {
            int(k): v
            for k, v in json.load(f)["monster"]["names"].items()
            if v
        }


def hash_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


st.set_page_config(page_title="Summoners War Rune Analyzer", layout="wide")
st.title("Summoners War Rune Analyzer")

uploaded = st.file_uploader("Upload JSON", type=["json"])
if uploaded is None:
    st.stop()

raw = uploaded.getvalue()
data = json.loads(raw.decode("utf-8"))

if "data_hash" not in st.session_state or st.session_state.data_hash != hash_bytes(raw):
    st.session_state.data_hash = hash_bytes(raw)
    st.session_state.original_data = data
    st.session_state.working_data = copy.deepcopy(data)
    st.session_state.wb_run = False
    st.session_state.selected_unit_id = None
    st.session_state.opt_ctx = None

render_wb_tab(st.session_state, load_monster_names())
