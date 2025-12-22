import copy
import hashlib
import json
import streamlit as st

from ui.wb_tab import render_wb_tab
from siege_logs import render_siege_tab
from ui.auth import require_access_or_stop

from artifact_analysis import collect_all_artifacts, artifact_attribute_matrix, artifact_archetype_matrix
from ui.artifact_render import render_matrix


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

@st.cache_data(ttl=300)
def build_worst_defense_list(cutoff: int = 4) -> pd.DataFrame:
    res = (
        sb()
        .table("siege_logs")
        .select(
            "result, "
            "deck2_1,deck2_2,deck2_3"
        )
        .in_("result", ["Win", "Lose"])
        .execute()
    )

    df = pd.DataFrame(res.data or [])
    if df.empty:
        return df

    def make_def_key(r):
        a = r["deck2_1"]
        rest = sorted([r["deck2_2"], r["deck2_3"]])
        return "|".join([a] + rest)

    df["def_key"] = df.apply(make_def_key, axis=1)

    agg = (
        df.groupby("def_key")
        .agg(
            win=("result", lambda x: (x == "Lose").sum()),
            lose=("result", lambda x: (x == "Win").sum()),
        )
        .reset_index()
    )

    agg["total"] = agg["win"] + agg["lose"]
    agg = agg[agg["total"] >= cutoff]

    if agg.empty:
        return agg

    agg["win_rate"] = agg["win"] / agg["total"]
    agg[["d1", "d2", "d3"]] = agg["def_key"].str.split("|", expand=True)

    return agg




# ============================================================
# Streamlit App
# ============================================================

st.set_page_config(page_title="Summoners War Analyzer", layout="wide")
st.title("Summoners War Analyzer")

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

tab_wb, tab_artifact, tab_siege, tab_worst = st.tabs([
    "World Boss",
    "Artifact Analysis",
    "Siege Battle",
    "Worst Offense"
])

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

    uploaded_art = st.file_uploader(
        "Upload JSON file exported from SW",
        type=["json"],
        key="artifact_json",
    )

    run_art = st.button("Run analysis", type="primary", key="artifact_run")

    if run_art:
        # ✅ Run 누를 때만 Access Key 체크
        require_access_or_stop("Artifact analysis")

        if uploaded_art is None:
            st.error("JSON 파일을 업로드해 주세요.")
            st.stop()

        raw = uploaded_art.getvalue()
        data = json.loads(raw.decode("utf-8"))

        all_arts = collect_all_artifacts(data)

        df_attr = artifact_attribute_matrix(all_arts, top_n=3)
        render_matrix(df_attr, label_cols=["Attribute", "Main"], title="Attribute Matrix")

        st.divider()

        df_arch = artifact_archetype_matrix(all_arts, top_n=3)
        render_matrix(df_arch, label_cols=["Archetype", "Main"], title="Archetype Matrix")


# ------------------------------------------------------------
# Siege Tab
# ------------------------------------------------------------

with tab_siege:
    render_siege_tab()




# ------------------------------------------------------------
# Siege Worst Offense Tab
# ------------------------------------------------------------

with tab4:
    render_worst_defense_tab()




