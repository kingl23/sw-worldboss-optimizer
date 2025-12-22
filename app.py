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


def require_access_or_stop(context: str):
    """
    Access Key 입력 UI는 사이드바에 상시 노출.
    실제 검증은 각 탭의 Run/Search 버튼 클릭 시점에만 수행.
    """
    allowed = set(st.secrets.get("ACCESS_KEYS", []))
    if not allowed:
        st.error("ACCESS_KEYS is not configured in Streamlit Secrets.")
        st.stop()

    key = st.session_state.get("access_key_input", "")
    if key not in allowed:
        st.warning(f"Access Key required for {context}.")
        st.stop()


# ============================================================
# Streamlit App
# ============================================================

st.set_page_config(page_title="Summoners War Rune Analyzer", layout="wide")
st.title("Summoners War Rune Analyzer")

# ------------------------------------------------------------
# Sidebar: Access Key Input (항상 표시)
# ------------------------------------------------------------

st.sidebar.header("Access Control")
st.sidebar.text_input(
    "Access Key",
    type="password",
    key="access_key_input",
    help="Enter a valid access key to unlock private features",
)

# ------------------------------------------------------------
# Tabs (항상 보이게)
# ------------------------------------------------------------

tab_wb, tab_artifact, tab_siege = st.tabs(
    ["World Boss (Rank / Optimizer)", "Artifact Analysis", "Siege"]
)

# ------------------------------------------------------------
# World Boss Tab
# ------------------------------------------------------------

with tab_wb:
    st.subheader("World Boss (Rank / Optimizer)")

    uploaded = st.file_uploader("Upload JSON file exported from SW", type=["json"], key="wb_json")
    run = st.button("Run analysis", type="primary", key="wb_run_btn")

    if run:
        require_access_or_stop("World Boss analysis")

        if uploaded is None:
            st.error("JSON 파일을 업로드해 주세요.")
            st.stop()

        raw = uploaded.getvalue()
        data = json.loads(raw.decode("utf-8"))
        data_hash = hash_bytes(raw)

        # Session State Init (기존 로직 유지)
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
    else:
        st.info("JSON 업로드 후 'Run analysis'를 누르면 분석이 실행됩니다.")

# ------------------------------------------------------------
# Artifact Tab
# ------------------------------------------------------------

with tab_artifact:
    st.subheader("Artifact Analysis")

    uploaded = st.file_uploader("Upload JSON file exported from SW", type=["json"], key="artifact_json")
    run = st.button("Run analysis", type="primary", key="artifact_run_btn")

    if run:
        require_access_or_stop("Artifact analysis")

        if uploaded is None:
            st.error("JSON 파일을 업로드해 주세요.")
            st.stop()

        st.info("Artifact Analysis – WIP")
    else:
        st.info("JSON 업로드 후 'Run analysis'를 누르면 분석이 실행됩니다. (WIP)")

# ------------------------------------------------------------
# Siege Tab
# ------------------------------------------------------------

with tab_siege:
    # Siege 탭은 업로드 없이 항상 접근 가능.
    # Search/Run 버튼 클릭 시점의 Access Key 검증은 siege_logs.py 내부에서 처리 권장.
    render_siege_tab()
