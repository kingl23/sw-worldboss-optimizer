import os

import streamlit as st
from supabase import create_client


def get_secret(key: str) -> str | None:
    value = st.secrets.get(key)
    if value:
        return value
    return os.environ.get(key)


@st.cache_resource
def get_supabase_client():
    url = get_secret("SUPABASE_URL")
    anon_key = get_secret("SUPABASE_ANON_KEY")
    missing = []
    if not url:
        missing.append("SUPABASE_URL")
    if not anon_key:
        missing.append("SUPABASE_ANON_KEY")
    if missing:
        st.error(
            "Missing Supabase configuration. Add the following keys in Streamlit "
            "Community Cloud → App → Settings → Secrets:\n"
            f"{', '.join(missing)}\n\n"
            "Example:\n"
            'SUPABASE_URL=\"https://YOUR_PROJECT.supabase.co\"\n'
            'SUPABASE_ANON_KEY=\"YOUR_ANON_KEY\"'
        )
        st.stop()
    return create_client(url, anon_key)
