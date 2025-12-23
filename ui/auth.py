# ui/auth.py
import streamlit as st

def has_access(feature: str) -> bool:
    feature = (feature or "").strip()
    key = (st.session_state.get("access_key_input") or "").strip()
    if not key:
        return False
    policy = st.secrets.get("ACCESS_POLICY", {})
    allowed = policy.get(key, [])
    return isinstance(allowed, list) and (("all" in allowed) or (feature in allowed))


def require_access_or_stop(feature: str):
    if not has_access(feature):
        st.warning(f"Access Key required for: {feature}")
        st.stop()
