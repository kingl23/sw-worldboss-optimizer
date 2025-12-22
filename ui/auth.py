import streamlit as st

def require_access_or_stop(context: str = "this action"):
    allowed = set(st.secrets.get("ACCESS_KEYS", []))
    if not allowed:
        st.error("ACCESS_KEYS is not configured in Streamlit Secrets.")
        st.stop()

    key = st.session_state.get("access_key_input", "")
    if key not in allowed:
        st.warning(f"Access Key required for {context}.")
        st.stop()
