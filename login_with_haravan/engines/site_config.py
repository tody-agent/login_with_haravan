"""Helpers for reading sensitive integration config from Frappe site config.

Secrets should live in `site_config` first. Settings DocTypes are accepted only
as a temporary fallback during production migration.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any
from urllib.parse import urljoin, urlparse

import frappe


HARAVAN_LOGIN_CONFIG_KEYS = ("haravan_account_login", "haravan_login")
HARAVAN_FLAT_CLIENT_ID_KEY = "haravan_client_id"
HARAVAN_FLAT_CLIENT_SECRET_KEY = "haravan_client_secret"
HARAVAN_REDIRECT_URI_KEY = "haravan_redirect_uri"
HARAVAN_PUBLIC_BASE_URL_KEYS = ("haravan_public_base_url", "helpdesk_public_base_url")
HARAVAN_OAUTH_CALLBACK_PATH = "/api/method/login_with_haravan.oauth.login_via_haravan"

HELPDESK_SECRET_CONFIG_KEYS: dict[str, tuple[str, ...]] = {
    "ai": ("gemini_api_key", "gemini_model", "openrouter_api_key"),
    "bitrix": (
        "bitrix_webhook_url",
        "bitrix_access_token",
        "bitrix_refresh_token",
        "bitrix_client_id",
        "bitrix_client_secret",
        "bitrix_base_url",
        "bitrix_domain",
        "bitrix_enabled",
        "bitrix_timeout_seconds",
        "bitrix_refresh_ttl_minutes",
    ),
    "gitlab": ("gitlab_token", "gitlab_base_url"),
}

BITRIX_RUNTIME_DEFAULTS = {
    "bitrix_enabled": 1,
    "bitrix_timeout_seconds": 15,
    "bitrix_refresh_ttl_minutes": 60,
}


def get_site_config_value(key: str, default: Any = None, conf: Any | None = None) -> Any:
    """Read a key from explicit config, `frappe.local.conf`, or `frappe.conf`."""
    source = conf if conf is not None else _get_frappe_conf()
    if source is None:
        return default

    if hasattr(source, "get"):
        return source.get(key, default)

    try:
        return source[key]
    except Exception:
        return default


def get_haravan_login_credentials(
    conf: Any | None = None,
    provider_doc: Any | None = None,
) -> dict[str, str | None]:
    """Return effective Haravan OAuth credentials with masked source metadata."""
    site_credentials = _get_haravan_site_credentials(conf=conf)
    client_id = site_credentials.get("client_id")
    client_secret = site_credentials.get("client_secret")
    client_id_source = site_credentials.get("client_id_source")
    client_secret_source = site_credentials.get("client_secret_source")

    if provider_doc is not None:
        if not _has_value(client_id):
            client_id = getattr(provider_doc, "client_id", None)
            if _has_value(client_id):
                client_id_source = "legacy_doctype"

        if not _has_value(client_secret):
            client_secret = _get_provider_secret(provider_doc)
            if _has_value(client_secret):
                client_secret_source = "legacy_doctype"

    source = _summarize_sources(client_id_source, client_secret_source)
    return {
        "client_id": client_id if _has_value(client_id) else None,
        "client_secret": client_secret if _has_value(client_secret) else None,
        "client_id_source": client_id_source or "missing",
        "client_secret_source": client_secret_source or "missing",
        "source": source,
    }


def get_haravan_redirect_uri_config(
    conf: Any | None = None,
    provider_doc: Any | None = None,
) -> dict[str, str]:
    """Return the effective Haravan OAuth callback URL and where it came from.

    Haravan validates `redirect_uri` by exact string match. Keep this helper as
    the single source used by setup, diagnostics, and token exchange.
    """
    grouped_config = _get_haravan_grouped_config(conf=conf)
    provider_redirect = _non_empty_string(getattr(provider_doc, "redirect_url", None))
    callback_path = _callback_path_from_redirect(provider_redirect)

    redirect_uri = _non_empty_string(grouped_config.get("redirect_uri")) or _non_empty_string(
        get_site_config_value(HARAVAN_REDIRECT_URI_KEY, conf=conf)
    )
    if redirect_uri:
        return {
            "redirect_uri": _normalize_absolute_url(redirect_uri),
            "source": "site_config.redirect_uri",
        }

    public_base_url = _non_empty_string(grouped_config.get("public_base_url")) or _non_empty_string(
        grouped_config.get("redirect_base_url")
    )
    if not public_base_url:
        for key in HARAVAN_PUBLIC_BASE_URL_KEYS:
            public_base_url = _non_empty_string(get_site_config_value(key, conf=conf))
            if public_base_url:
                break

    if public_base_url:
        return {
            "redirect_uri": _build_absolute_url(public_base_url, callback_path),
            "source": "site_config.public_base_url",
        }

    return {
        "redirect_uri": frappe.utils.get_url(callback_path),
        "source": "request_host",
    }


def get_helpdesk_secret_status(conf: Any | None = None) -> dict[str, dict[str, dict[str, Any]]]:
    """Return masked status for known Helpdesk integration site-config keys."""
    status: dict[str, dict[str, dict[str, Any]]] = {}
    for integration, keys in HELPDESK_SECRET_CONFIG_KEYS.items():
        status[integration] = {}
        for key in keys:
            value = get_site_config_value(key, conf=conf)
            status[integration][key] = {
                "configured": _has_value(value),
                "source": "site_config" if _has_value(value) else "missing",
            }
    return status


def get_bitrix_config(conf: Any | None = None) -> dict[str, Any]:
    """Return Bitrix runtime config for server-side callers only."""
    webhook_url = get_site_config_value("bitrix_webhook_url", conf=conf)
    access_token = get_site_config_value("bitrix_access_token", conf=conf)
    base_url = get_site_config_value("bitrix_base_url", conf=conf)
    domain = get_site_config_value("bitrix_domain", conf=conf)
    enabled = _as_bool(
        get_site_config_value(
            "bitrix_enabled",
            BITRIX_RUNTIME_DEFAULTS["bitrix_enabled"],
            conf=conf,
        )
    )
    timeout_seconds = _as_int(
        get_site_config_value(
            "bitrix_timeout_seconds",
            BITRIX_RUNTIME_DEFAULTS["bitrix_timeout_seconds"],
            conf=conf,
        ),
        BITRIX_RUNTIME_DEFAULTS["bitrix_timeout_seconds"],
    )
    refresh_ttl_minutes = _as_int(
        get_site_config_value(
            "bitrix_refresh_ttl_minutes",
            BITRIX_RUNTIME_DEFAULTS["bitrix_refresh_ttl_minutes"],
            conf=conf,
        ),
        BITRIX_RUNTIME_DEFAULTS["bitrix_refresh_ttl_minutes"],
    )

    configured = bool(_has_value(webhook_url) or (_has_value(base_url) and _has_value(access_token)))
    return {
        "enabled": enabled,
        "configured": configured,
        "webhook_url": webhook_url,
        "access_token": access_token,
        "refresh_token": get_site_config_value("bitrix_refresh_token", conf=conf),
        "client_id": get_site_config_value("bitrix_client_id", conf=conf),
        "client_secret": get_site_config_value("bitrix_client_secret", conf=conf),
        "base_url": base_url,
        "domain": domain,
        "timeout_seconds": timeout_seconds,
        "refresh_ttl_minutes": refresh_ttl_minutes,
    }


def get_site_or_legacy_secret(
    config_key: str,
    legacy_doc: Any | None = None,
    legacy_field: str | None = None,
    conf: Any | None = None,
) -> dict[str, Any]:
    """Read a secret from site config first, then a legacy Settings DocType field.

    The return value intentionally includes the value for server-side callers that
    need to authenticate outbound requests. Do not expose it in diagnostics.
    """
    value = get_site_config_value(config_key, conf=conf)
    if _has_value(value):
        return {"value": value, "source": "site_config"}

    if legacy_doc is not None and legacy_field:
        value = _get_legacy_field_value(legacy_doc, legacy_field)
        if _has_value(value):
            return {"value": value, "source": "legacy_doctype"}

    return {"value": None, "source": "missing"}


def _get_haravan_site_credentials(conf: Any | None = None) -> dict[str, str | None]:
    grouped_credentials = _get_haravan_grouped_config(conf=conf)
    client_id = grouped_credentials.get("client_id") or get_site_config_value(
        HARAVAN_FLAT_CLIENT_ID_KEY, conf=conf
    )
    client_secret = grouped_credentials.get("client_secret") or get_site_config_value(
        HARAVAN_FLAT_CLIENT_SECRET_KEY, conf=conf
    )

    return {
        "client_id": client_id if _has_value(client_id) else None,
        "client_secret": client_secret if _has_value(client_secret) else None,
        "client_id_source": "site_config" if _has_value(client_id) else None,
        "client_secret_source": "site_config" if _has_value(client_secret) else None,
    }


def _get_haravan_grouped_config(conf: Any | None = None) -> dict[str, Any]:
    for key in HARAVAN_LOGIN_CONFIG_KEYS:
        grouped_config = _coerce_mapping(get_site_config_value(key, conf=conf))
        if grouped_config:
            return grouped_config
    return {}


def _get_frappe_conf() -> Any | None:
    local = getattr(frappe, "local", None)
    local_conf = getattr(local, "conf", None)
    return local_conf or getattr(frappe, "conf", None)


def _coerce_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)

    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        if isinstance(parsed, Mapping):
            return dict(parsed)

    return {}


def _get_provider_secret(provider_doc: Any) -> str | None:
    return _get_legacy_password(provider_doc, "client_secret")


def _get_legacy_field_value(legacy_doc: Any, legacy_field: str) -> Any:
    password = _get_legacy_password(legacy_doc, legacy_field)
    if _has_value(password):
        return password

    getter = getattr(legacy_doc, "get", None)
    if callable(getter):
        value = getter(legacy_field)
        if _has_value(value):
            return value

    return getattr(legacy_doc, legacy_field, None)


def _get_legacy_password(legacy_doc: Any, legacy_field: str) -> str | None:
    get_password = getattr(legacy_doc, "get_password", None)
    if not callable(get_password):
        return None

    try:
        return get_password(legacy_field, raise_exception=False)
    except TypeError:
        return get_password(legacy_field)


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True


def _non_empty_string(value: Any) -> str | None:
    if not _has_value(value):
        return None
    return str(value).strip()


def _normalize_absolute_url(value: str) -> str:
    url = value.strip()
    parsed = urlparse(url)
    if parsed.scheme and parsed.netloc:
        return url.rstrip("/")
    if url.startswith("//"):
        return f"https:{url}".rstrip("/")
    if url.startswith("/"):
        return frappe.utils.get_url(url)
    return f"https://{url.lstrip('/')}".rstrip("/")


def _build_absolute_url(base_url: str, path: str) -> str:
    return urljoin(_normalize_absolute_url(base_url).rstrip("/") + "/", path.lstrip("/"))


def _callback_path_from_redirect(redirect_url: str | None) -> str:
    if not redirect_url:
        return HARAVAN_OAUTH_CALLBACK_PATH
    parsed = urlparse(redirect_url)
    if parsed.scheme and parsed.netloc:
        return parsed.path or HARAVAN_OAUTH_CALLBACK_PATH
    return redirect_url


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() not in {"0", "false", "no", "off", ""}
    return bool(value)


def _as_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _summarize_sources(client_id_source: str | None, client_secret_source: str | None) -> str:
    sources = {source for source in (client_id_source, client_secret_source) if source}
    if not sources:
        return "missing"
    if sources == {"site_config"}:
        return "site_config"
    if sources == {"legacy_doctype"}:
        return "legacy_doctype"
    return "mixed"
