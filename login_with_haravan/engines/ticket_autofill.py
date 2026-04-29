"""Derive Helpdesk ticket metadata from agent-entered fields."""

from __future__ import annotations

import re
from urllib.parse import urlparse

import frappe


FIELD_ALIASES = {
    "link_web_myharavan": {
        "labels": ("Link Web / MyHaravan", "Link Web/MyHaravan", "Website / MyHaravan"),
        "fallbacks": ("custom_link_web_myharavan",),
    },
    "customer": {
        "labels": ("Customer",),
        "fallbacks": ("customer",),
    },
    "org_id": {
        "labels": ("Org ID", "Haravan Org ID"),
        "fallbacks": ("custom_org_id", "custom_haravan_orgid"),
    },
    "myharavan_domain": {
        "labels": ("MyHaravan Domain", "MyHaravan"),
        "fallbacks": ("custom_myharavan_domain", "custom_myharavan"),
    },
    "product_suggestion": {
        "labels": ("Product Suggestion",),
        "fallbacks": ("custom_product_suggestion",),
    },
    "product_line": {
        "labels": ("Product Line",),
        "fallbacks": ("custom_product_line",),
    },
    "product_feature": {
        "labels": ("Product Feature",),
        "fallbacks": ("custom_product_feature",),
    },
}

DERIVED_FIELD_KEYS = (
    "customer",
    "org_id",
    "myharavan_domain",
    "product_line",
    "product_feature",
)


def get_ticket_autofill_metadata() -> dict:
    """Return field metadata used by the Helpdesk create-ticket customizer."""
    field_map = get_ticket_field_map()
    return {
        "field_map": field_map,
        "required_fields": [
            field_map[key]
            for key in ("link_web_myharavan", "product_suggestion")
            if field_map.get(key)
        ],
        "hidden_fields": [
            field_map[key]
            for key in DERIVED_FIELD_KEYS
            if field_map.get(key)
        ],
        "hidden_labels": [
            "Customer",
            "Org ID",
            "MyHaravan Domain",
            "Product Line",
            "Product Feature",
        ],
    }


def get_ticket_field_map() -> dict[str, str]:
    """Map logical keys to actual HD Ticket fieldnames.

    Existing production fields may have been created manually. Prefer matching
    by label so this app can work with those fields; fall back to the canonical
    custom fieldnames created by ``setup.install``.
    """
    by_label = {}
    by_fieldname = set()

    try:
        meta = frappe.get_meta("HD Ticket")
        fields = list(getattr(meta, "fields", []) or [])
        for field in fields:
            fieldname = str(getattr(field, "fieldname", "") or "")
            label = _normalize_label(getattr(field, "label", "") or "")
            if fieldname:
                by_fieldname.add(fieldname)
            if label and fieldname:
                by_label.setdefault(label, fieldname)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "HD Ticket metadata lookup failed")

    field_map = {}
    for key, config in FIELD_ALIASES.items():
        fieldname = None
        for label in config["labels"]:
            fieldname = by_label.get(_normalize_label(label))
            if fieldname:
                break
        if not fieldname:
            for fallback in config["fallbacks"]:
                if fallback in by_fieldname or fallback == "customer":
                    fieldname = fallback
                    break
        if not fieldname:
            fieldname = config["fallbacks"][0]
        field_map[key] = fieldname

    return field_map


def resolve_ticket_autofill(
    link_web_myharavan: str | None = None,
    product_suggestion: str | None = None,
) -> dict:
    """Resolve ticket values from the two fields agents manually enter."""
    field_map = get_ticket_field_map()
    resolved = {
        "field_map": field_map,
        "values": {},
        "customer": None,
        "org_id": None,
        "myharavan_domain": None,
        "product_line": None,
        "product_feature": None,
    }

    customer_data = resolve_customer_from_link(link_web_myharavan)
    resolved.update(customer_data)

    product_data = parse_product_suggestion(product_suggestion)
    resolved.update(product_data)

    for key in DERIVED_FIELD_KEYS:
        value = resolved.get(key)
        fieldname = field_map.get(key)
        if fieldname and value not in (None, ""):
            resolved["values"][fieldname] = value

    return resolved


def auto_fill_ticket_fields(doc, method=None):
    """Frappe doc_event hook: set derived HD Ticket fields before validation."""
    field_map = get_ticket_field_map()
    link_value = _get_doc_value(doc, field_map.get("link_web_myharavan"))
    product_value = _get_doc_value(doc, field_map.get("product_suggestion"))
    resolved = resolve_ticket_autofill(link_value, product_value)

    for key in DERIVED_FIELD_KEYS:
        fieldname = field_map.get(key)
        value = resolved.get(key)
        if not fieldname or value in (None, ""):
            continue
        if key == "customer" and _get_doc_value(doc, fieldname):
            continue
        _set_doc_value(doc, fieldname, value)


def resolve_customer_from_link(value: str | None) -> dict:
    """Find HD Customer metadata by website, MyHaravan domain, or org id."""
    normalized = normalize_domain(value)
    org_id = extract_org_id(value, normalized)

    lookups = []
    if normalized:
        lookups.extend(
            [
                {"domain": normalized},
                {"custom_myharavan": normalized},
            ]
        )
    if org_id:
        org_id_int = _safe_int(org_id)
        lookups.append({"custom_haravan_orgid": org_id_int or org_id})

    for filters in lookups:
        row = _lookup_hd_customer(filters)
        if row:
            return _customer_data_from_row(row, normalized, org_id)

    return {
        "customer": None,
        "org_id": org_id,
        "myharavan_domain": normalized if _is_myharavan_domain(normalized) else None,
    }


def parse_product_suggestion(value: str | None) -> dict:
    """Parse values like ``[HaraInventory]:Apps-Social Login``."""
    raw = _clean_text(value)
    if not raw:
        return {"product_line": None, "product_feature": None}

    bracket_match = re.match(r"^\[([^\]]+)\]\s*:?\s*(.+)$", raw)
    if bracket_match:
        return {
            "product_line": bracket_match.group(1).strip() or None,
            "product_feature": bracket_match.group(2).strip() or None,
        }

    for delimiter in (":", " - ", " > ", "/"):
        if delimiter in raw:
            left, right = raw.split(delimiter, 1)
            return {
                "product_line": left.strip(" []") or None,
                "product_feature": right.strip() or None,
            }

    return {"product_line": raw, "product_feature": None}


def normalize_domain(value: str | None) -> str | None:
    raw = _clean_text(value)
    if not raw:
        return None
    if re.fullmatch(r"\d+", raw):
        return f"{raw}.myharavan.com"

    candidate = raw if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", raw) else f"https://{raw}"
    parsed = urlparse(candidate)
    host = (parsed.netloc or parsed.path.split("/", 1)[0]).split("@")[-1]
    host = host.split(":", 1)[0].strip().strip(".").lower()
    if not host:
        return None
    return host


def extract_org_id(value: str | None, normalized_domain: str | None = None) -> str | None:
    raw = _clean_text(value)
    if raw and re.fullmatch(r"\d+", raw):
        return raw
    domain = normalized_domain or normalize_domain(value)
    if domain and domain.endswith(".myharavan.com"):
        first_label = domain.split(".", 1)[0]
        if re.fullmatch(r"\d+", first_label):
            return first_label
    return None


def _lookup_hd_customer(filters: dict):
    try:
        return frappe.db.get_value(
            "HD Customer",
            filters,
            ["name", "domain", "custom_myharavan", "custom_haravan_orgid"],
            as_dict=True,
        )
    except Exception:
        frappe.log_error(frappe.get_traceback(), "HD Customer lookup failed")
        return None


def _customer_data_from_row(row, fallback_domain: str | None, fallback_org_id: str | None) -> dict:
    customer = _row_get(row, "name")
    domain = _row_get(row, "custom_myharavan") or _row_get(row, "domain") or fallback_domain
    org_id = _row_get(row, "custom_haravan_orgid") or fallback_org_id
    return {
        "customer": customer,
        "org_id": str(org_id) if org_id not in (None, "") else None,
        "myharavan_domain": domain,
    }


def _row_get(row, key: str):
    if isinstance(row, dict):
        return row.get(key)
    return getattr(row, key, None)


def _get_doc_value(doc, fieldname: str | None):
    if not fieldname:
        return None
    if hasattr(doc, "get"):
        try:
            return doc.get(fieldname)
        except Exception:
            pass
    return getattr(doc, fieldname, None)


def _set_doc_value(doc, fieldname: str, value):
    if hasattr(doc, "set"):
        try:
            doc.set(fieldname, value)
            return
        except Exception:
            pass
    setattr(doc, fieldname, value)


def _normalize_label(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip()).lower()


def _clean_text(value: str | None) -> str:
    return str(value or "").strip()


def _safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _is_myharavan_domain(value: str | None) -> bool:
    return bool(value and value.endswith(".myharavan.com"))
