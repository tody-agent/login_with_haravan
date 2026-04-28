import hashlib
import json
import re
from typing import Any


class HaravanIdentityError(ValueError):
    """Raised when Haravan identity claims are missing required fields."""


def _first_string(payload: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = payload.get(key)
        if value is None:
            continue
        value = str(value).strip()
        if value:
            return value
    return None


def _normalize_roles(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()]


def normalize_haravan_profile(payload: dict[str, Any]) -> dict[str, Any]:
    user_id = _first_string(payload, "sub", "userid", "user_id", "id")
    email = _first_string(payload, "email", "email_address")
    org_id = _first_string(payload, "orgid", "org_id", "organization_id")

    missing = []
    if not user_id:
        missing.append("userid/sub")
    if not email:
        missing.append("email")
    if not org_id:
        missing.append("orgid")
    if missing:
        raise HaravanIdentityError(f"Missing Haravan identity field(s): {', '.join(missing)}")

    normalized = dict(payload)
    normalized.update(
        {
            "sub": user_id,
            "userid": user_id,
            "id": user_id,
            "email": email.lower(),
            "orgid": org_id,
            "org_id": org_id,
            "orgname": _first_string(payload, "orgname", "org_name") or "",
            "orgcat": _first_string(payload, "orgcat", "org_category") or "",
            "name": _first_string(payload, "name", "full_name", "email") or email,
            "role": _normalize_roles(payload.get("role") or payload.get("roles")),
        }
    )
    return normalized


def make_link_name(org_id: str, user_id: str) -> str:
    raw = f"HARAVAN-{org_id}-{user_id}"
    safe = re.sub(r"[^A-Za-z0-9_-]+", "-", raw).strip("-")
    if len(safe) <= 140:
        return safe

    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
    return f"{safe[:127]}-{digest}"


def build_link_fields(user: str, profile: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_haravan_profile(profile)
    return {
        "user": user,
        "email": normalized["email"],
        "haravan_userid": normalized["userid"],
        "haravan_orgid": normalized["orgid"],
        "haravan_orgname": normalized.get("orgname"),
        "haravan_orgcat": normalized.get("orgcat"),
        "haravan_roles": json.dumps(normalized.get("role", []), ensure_ascii=False),
        "raw_profile": json.dumps(normalized, ensure_ascii=False, sort_keys=True),
    }
