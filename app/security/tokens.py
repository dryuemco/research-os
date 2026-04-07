from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time


def _b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode((data + padding).encode("utf-8"))


def create_access_token(payload: dict, *, secret: str, ttl_seconds: int) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    body = dict(payload)
    body["exp"] = int(time.time()) + ttl_seconds
    signing_input = (
        f"{_b64_encode(json.dumps(header, separators=(',', ':')).encode('utf-8'))}."
        f"{_b64_encode(json.dumps(body, separators=(',', ':')).encode('utf-8'))}"
    )
    signature = hmac.new(secret.encode("utf-8"), signing_input.encode("utf-8"), hashlib.sha256)
    return f"{signing_input}.{_b64_encode(signature.digest())}"


def decode_access_token(token: str, *, secret: str) -> dict | None:
    try:
        header_segment, payload_segment, signature_segment = token.split(".", maxsplit=2)
    except ValueError:
        return None

    signing_input = f"{header_segment}.{payload_segment}"
    expected = hmac.new(secret.encode("utf-8"), signing_input.encode("utf-8"), hashlib.sha256)
    if not hmac.compare_digest(_b64_encode(expected.digest()), signature_segment):
        return None

    try:
        payload = json.loads(_b64_decode(payload_segment).decode("utf-8"))
    except Exception:
        return None

    exp = payload.get("exp")
    if not isinstance(exp, int) or exp < int(time.time()):
        return None
    return payload
