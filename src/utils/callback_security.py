"""
HMAC signature for callback_data buttons.
Protects against callback_data forgery.

Format: flow:{block_id}:{action}:{data}|{signature}
Or: fc:{block_id}:{flow_id}|{signature}
"""
import hmac
import hashlib
import os

SECRET_KEY: str = os.getenv("SECRET_KEY", "")


def sign_callback(prefix: str, *parts: str) -> str:
    """
    Sign callback_data.

    Args:
        prefix: Prefix (flow_ or fc_)
        *parts: Callback parts (block_id, action, data)

    Returns:
        callback_data with HMAC signature
    """
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY not set in environment")

    raw = ":".join([prefix.rstrip("_"), *parts])
    signature = hmac.new(
        SECRET_KEY.encode(),
        raw.encode(),
        hashlib.sha256
    ).hexdigest()[:16]  # 16 hex символов = 64 бита безопасности

    return f"{raw}|{signature}"


def verify_callback(callback_data: str) -> tuple:
    """
    Verify callback_data signature.

    Args:
        callback_data: Full callback_data string

    Returns:
        (valid, raw_callback_without_signature)
    """
    if not SECRET_KEY:
        return False, callback_data

    parts = callback_data.rsplit("|", 1)
    if len(parts) != 2:
        return False, callback_data

    raw, signature = parts

    expected = hmac.new(
        SECRET_KEY.encode(),
        raw.encode(),
        hashlib.sha256
    ).hexdigest()[:16]  # 16 hex символов = 64 бита безопасности

    if hmac.compare_digest(signature, expected):
        return True, raw
    return False, callback_data
