# ui/auth.py
import streamlit as st

def require_access_or_stop(feature: str) -> bool:

    policy = st.secrets.get("ACCESS_POLICY", {})
    key = (st.session_state.get("access_key_input") or "").strip()

    allowed = policy.get(key, []) if key else []
    ok = isinstance(allowed, list) and (("all" in allowed) or (feature in allowed))

    if not ok:
        st.warning(f"Access Key required for: {feature}")
        return False

    return True
