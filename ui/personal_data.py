import json
from typing import Any, Dict, List, Tuple

import streamlit as st

from ui.auth import require_access_or_stop


def _wizard_identity(entry: Dict[str, Any], index: int) -> Tuple[str, str]:
    wizard_id = entry.get("wizard_id") or entry.get("wizard_uid") or entry.get("wizardId")
    wizard_name = entry.get("wizard_name") or entry.get("wizard") or entry.get("name")

    if wizard_name and wizard_id:
        label = f"{wizard_name} ({wizard_id})"
    elif wizard_name:
        label = str(wizard_name)
    elif wizard_id:
        label = f"Wizard {wizard_id}"
    else:
        label = f"Wizard #{index + 1}"

    return label, str(wizard_id) if wizard_id is not None else ""


def _collect_wizard_entries(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []

    wizard_info = data.get("wizard_info")
    if isinstance(wizard_info, dict):
        entries.append(wizard_info)

    wizard_info_list = data.get("wizard_info_list")
    if isinstance(wizard_info_list, list):
        entries.extend([row for row in wizard_info_list if isinstance(row, dict)])

    for value in data.values():
        if isinstance(value, list):
            for row in value:
                if isinstance(row, dict) and ("wizard_id" in row or "wizard_name" in row):
                    entries.append(row)

    deduped: List[Dict[str, Any]] = []
    seen = set()

    for idx, entry in enumerate(entries):
        label, wizard_id = _wizard_identity(entry, idx)
        key = (label, wizard_id)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(entry)

    return deduped


def _render_summary(entry: Dict[str, Any]) -> None:
    simple_items = {
        k: v
        for k, v in entry.items()
        if v is not None and isinstance(v, (str, int, float, bool))
    }

    if simple_items:
        st.markdown("### Summary")
        rows = [
            {"Field": key, "Value": value}
            for key, value in simple_items.items()
        ]
        st.dataframe(rows, use_container_width=True)

    st.markdown("### Raw Data")
    st.json(entry)


def render_personal_data_tab() -> None:
    st.subheader("Personal Data")

    uploaded = st.file_uploader(
        "Upload JSON file exported from SW",
        type=["json"],
        key="personal_data_json",
    )

    if uploaded is None:
        st.info("Please upload a JSON file to start.")
        return

    try:
        data = json.loads(uploaded.getvalue().decode("utf-8"))
    except json.JSONDecodeError:
        st.error("Invalid JSON file.")
        return

    if not isinstance(data, dict):
        st.warning("Unsupported data format.")
        return

    wizard_entries = _collect_wizard_entries(data)
    if not wizard_entries:
        st.warning("No wizard data found in the uploaded file.")
        return

    options = []
    for idx, entry in enumerate(wizard_entries):
        label, _ = _wizard_identity(entry, idx)
        options.append(label)

    selected = st.selectbox("Select wizard", options, key="personal_data_wizard")
    run_personal = st.button("Show personal data", type="primary", key="personal_data_run")

    if not run_personal:
        return

    if not require_access_or_stop("personal_data"):
        return

    selected_index = options.index(selected)
    _render_summary(wizard_entries[selected_index])
