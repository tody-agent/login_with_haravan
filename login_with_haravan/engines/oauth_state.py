import base64
import json
from typing import Any


def decode_oauth_state(state: str | bytes) -> dict[str, Any]:
    try:
        if isinstance(state, str):
            state = state.encode("utf-8")
        return json.loads(base64.b64decode(state).decode("utf-8"))
    except Exception:
        return {}


def encode_oauth_state(state: dict[str, Any]) -> str:
    return base64.b64encode(json.dumps(state).encode("utf-8")).decode("utf-8")
