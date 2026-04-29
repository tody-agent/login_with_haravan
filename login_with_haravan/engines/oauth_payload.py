import json
from typing import Any


def decode_json_payload(value: bytes | str) -> dict[str, Any]:
    if isinstance(value, bytes):
        value = value.decode("utf-8")
    return json.loads(value)
