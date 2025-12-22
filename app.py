import copy
import hashlib
import json
import streamlit as st

from ui.wb_tab import render_wb_tab
from siege_logs import render_siege_tab

from artifact_analysis import (
    collect_all_artifacts,
    artifact_attribute_summary,
    artifact_archetype_summary,
)

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

            # World Boss state (기존대로)
            st.session_state.wb_run = False
            st.session_state.wb_ranking = None
            st.session_state.selected_unit_id = None
            st.session_state.opt_ctx = None

        # ✅ 기존 탭 UI/버튼을 원래대로 렌더링
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

    run = st.button("Run analysis", type="primary", key="artifact_run_btn")

    if run:
        if uploaded is None:
            st.error("JSON 파일을 업로드해 주세요.")
            st.stop()

        raw = uploaded.getvalue()
        data = json.loads(raw.decode("utf-8"))

        # 1) 아티팩트 수집
        all_artifacts = collect_all_artifacts(data)
        if not all_artifacts:
            st.warning("아티팩트 데이터를 찾지 못했습니다.")
            st.stop()

        st.success(f"Collected {len(all_artifacts)} artifacts")

        # 2) Attribute 기반 요약
        st.markdown("### Attribute-based Summary")
        df_attr = artifact_attribute_summary(all_artifacts)
        st.dataframe(df_attr, use_container_width=True)

        # 3) Archetype 기반 요약
        st.markdown("### Archetype-based Summary")
        df_arch = artifact_archetype_summary(all_artifacts)
        st.dataframe(df_arch, use_container_width=True)

    else:
        st.info("JSON 업로드 후 'Run analysis'를 누르면 분석이 실행됩니다.")


# ------------------------------------------------------------
# Siege Tab
# ------------------------------------------------------------

with tab_siege:
    # Siege 탭은 업로드 없이 항상 접근 가능.
    # Search/Run 버튼 클릭 시점의 Access Key 검증은 siege_logs.py 내부에서 처리 권장.
    render_siege_tab()
