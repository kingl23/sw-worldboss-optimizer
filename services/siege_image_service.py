import streamlit as st

from services.supabase_client import get_supabase_client
from data.siege_data import make_key_fixed


# Default object path: siege/{match_id}/{log_id}.png
# Offense key path (when SIEGE_IMAGE_KEY_MODE=offense_key):
#   {SIEGE_IMAGE_KEY_PREFIX}{hangul->qwerty(make_key_fixed(deck1,deck2,deck3).replace("|","_"))}.png
def build_object_path(match_id: str, log_id: str) -> str:
    return f"siege/{match_id}/{log_id}.png"


def build_offense_key_path(deck1: str, deck2: str, deck3: str) -> str | None:
    key = make_key_fixed(deck1, deck2, deck3)
    if not key:
        return None

    converted = _hangul_to_qwerty(key.replace("|", "_"))
    prefix = str(st.secrets.get("SIEGE_IMAGE_KEY_PREFIX", "")).strip()
    filename = f"{prefix}{converted}.png" if prefix else f"{converted}.png"
    return filename


def _normalize_identifier(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def _hangul_to_qwerty(text: str) -> str:
    # 2-beolsik keyboard mapping (Hangul -> QWERTY)
    l_table = [
        "r", "R", "s", "e", "E", "f", "a", "q", "Q", "t",
        "T", "d", "w", "W", "c", "z", "x", "v", "g",
    ]
    v_table = [
        "k", "o", "i", "O", "j", "p", "u", "P", "h", "hk",
        "ho", "hl", "y", "n", "nj", "np", "nl", "b", "m",
        "ml", "l",
    ]
    t_table = [
        "", "r", "R", "rt", "s", "sw", "sg", "e", "f", "fr",
        "fa", "fq", "ft", "fx", "fv", "fg", "a", "q", "qt",
        "t", "T", "d", "w", "c", "z", "x", "v", "g",
    ]

    def convert_char(ch: str) -> str:
        code = ord(ch)
        if 0xAC00 <= code <= 0xD7A3:
            base = code - 0xAC00
            l = base // 588
            v = (base % 588) // 28
            t = base % 28
            return f"{l_table[l]}{v_table[v]}{t_table[t]}"
        return ch

    return "".join(convert_char(ch) for ch in text)


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


def get_siege_image_url(match_id=None, log_id=None, offense_units=None) -> str | None:
    bucket = st.secrets.get("SIEGE_IMAGE_BUCKET")
    if not bucket:
        return None

    mode = str(st.secrets.get("SIEGE_IMAGE_MODE", "public")).lower().strip()
    key_mode = str(st.secrets.get("SIEGE_IMAGE_KEY_MODE", "match_log")).lower().strip()

    if key_mode == "offense_key":
        if not offense_units or len(offense_units) != 3:
            return None
        deck1, deck2, deck3 = offense_units
        path = build_offense_key_path(deck1, deck2, deck3)
        if not path:
            return None
    else:
        match_id = _normalize_identifier(match_id)
        log_id = _normalize_identifier(log_id)
        if not match_id or not log_id:
            return None
        path = build_object_path(match_id, log_id)

    ttl_seconds = int(st.secrets.get("SIEGE_IMAGE_SIGNED_URL_TTL_SECONDS", 3600))

    try:
        if mode == "signed":
            return _get_signed_url_cached(bucket, path, ttl_seconds)
        return _get_public_url(bucket, path)
    except Exception:
        return None
