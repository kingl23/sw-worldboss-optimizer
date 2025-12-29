import streamlit as st

from services.supabase_client import get_supabase_client


# Expected object path: siege/{match_id}/{log_id}.png
def build_object_path(match_id: str, log_id: str) -> str:
    return f"siege/{match_id}/{log_id}.png"


def _normalize_identifier(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def _extract_url(payload, keys: tuple[str, ...]) -> str | None:
    if isinstance(payload, str):
        return payload
    if isinstance(payload, dict):
        for key in keys:
            if payload.get(key):
                return payload[key]
    return None


def _get_public_url(bucket: str, path: str) -> str | None:
    result = get_supabase_client().storage.from_(bucket).get_public_url(path)
    return _extract_url(result, ("publicUrl", "publicURL", "public_url"))


@st.cache_data(ttl=300)
def _get_signed_url_cached(bucket: str, path: str, ttl_seconds: int) -> str | None:
    result = get_supabase_client().storage.from_(bucket).create_signed_url(path, ttl_seconds)
    return _extract_url(result, ("signedUrl", "signedURL", "signed_url"))


def get_siege_image_url(match_id, log_id) -> str | None:
    bucket = st.secrets.get("SIEGE_IMAGE_BUCKET")
    if not bucket:
        return None

    match_id = _normalize_identifier(match_id)
    log_id = _normalize_identifier(log_id)
    if not match_id or not log_id:
        return None

    path = build_object_path(match_id, log_id)
    mode = str(st.secrets.get("SIEGE_IMAGE_MODE", "public")).lower().strip()
    ttl_seconds = int(st.secrets.get("SIEGE_IMAGE_SIGNED_URL_TTL_SECONDS", 3600))

    try:
        if mode == "signed":
            return _get_signed_url_cached(bucket, path, ttl_seconds)
        return _get_public_url(bucket, path)
    except Exception:
        return None
