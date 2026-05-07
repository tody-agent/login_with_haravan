"""Server-side Bitrix REST helpers for customer profile enrichment."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote, urljoin

import requests


COMPANY_PROFILE_SELECT_FIELDS = [
    "ID",
    "TITLE",
    "DATE_CREATE",
    "DATE_MODIFY",
    "ASSIGNED_BY_ID",
    "ADDRESS_REGION",
    "ADDRESS_COUNTRY",
    "UF_CRM_VERIFIED_STATUS",
    "UF_CRM_COMPANY_STAGE",
    "UF_CRM_ID_FRESHSALES",
    "UF_CRM_COMPANY_ID",
    "UF_CRM_SHOP_OWNER_NAME",
    "UF_CRM_SHOP_OWNER_EMAIL",
    "UF_CRM_SHOP_OWNER_PHONE_NUMBER",
    "UF_CRM_DATE_CREATED_SHOP",
    "UF_CRM_FIRST_PAID_DATE",
    "UF_CRM_CURRENT_SHOPPLAN",
    "UF_CRM_DATE_SIGNED_CURRENT_SHOPPLAN",
    "UF_CRM_DATE_EXPIRED_SHOPPLAN",
    "UF_CRM_CURRENT_HSI_SEGMENT",
    "UF_CRM_CURRENT_HSI_DETAIL",
    "UF_CRM_HARAVAN_MEMBERSHIP",
    "UF_CRM_1778130421650",
    "EMAIL",
    "PHONE",
    "WEB",
]


class BitrixClient:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.timeout = int(config.get("timeout_seconds") or 15)

    def call(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        webhook_url: str | None = None,
    ) -> dict[str, Any]:
        url = self._method_url(method, webhook_url=webhook_url)
        payload = params or {}
        if self.config.get("access_token") and not (webhook_url or self.config.get("webhook_url")):
            payload = dict(payload)
            payload["auth"] = self.config["access_token"]

        response = requests.post(url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict):
            return data
        return {"result": data}

    def find_companies(
        self,
        domain: str | None = None,
        haravan_orgid: str | None = None,
    ) -> list[dict[str, Any]]:
        filters: list[dict[str, Any]] = []
        if haravan_orgid:
            filters.append({"UF_CRM_COMPANY_ID": haravan_orgid})
            filters.append({"UF_CRM_HARAVAN_ORG_ID": haravan_orgid})
        if domain:
            filters.append({"WEB": domain})
            filters.append({"%TITLE": domain})

        for filter_payload in filters:
            result = self.call(
                "crm.company.list",
                {
                    "filter": filter_payload,
                    "select": COMPANY_PROFILE_SELECT_FIELDS,
                    "order": {"DATE_MODIFY": "DESC"},
                    "start": 0,
                },
            ).get("result") or []
            if result:
                return result
        return []

    def find_contacts(
        self,
        email: str | None = None,
        phone: str | None = None,
    ) -> list[dict[str, Any]]:
        filters: list[dict[str, Any]] = []
        if email:
            filters.append({"EMAIL": email})
        if phone:
            filters.append({"PHONE": phone})

        for filter_payload in filters:
            result = self.call(
                "crm.contact.list",
                {
                    "filter": filter_payload,
                    "select": ["*", "UF_*", "EMAIL", "PHONE", "WEB"],
                    "order": {"DATE_MODIFY": "DESC"},
                },
            ).get("result") or []
            if result:
                return result
        return []

    def get_user(self, user_id: str | int | None) -> dict[str, Any] | None:
        if not user_id:
            return None
        responsible_webhook_url = self.config.get("responsible_webhook_url")
        if not responsible_webhook_url:
            return None

        if "user.get" in responsible_webhook_url:
            url = responsible_webhook_url.replace("{ASSIGNED_BY_ID}", quote(str(user_id)))
            if "{ID}" in url:
                url = url.replace("{ID}", quote(str(user_id)))
            elif "ID=" not in url:
                separator = "&" if "?" in url else "?"
                url = f"{url}{separator}ID={quote(str(user_id))}"
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            result = data.get("result") if isinstance(data, dict) else data
            if isinstance(result, list):
                return result[0] if result else None
            if isinstance(result, dict):
                return result
            return None

        result = self.call(
            "user.get",
            {"ID": str(user_id)},
            webhook_url=responsible_webhook_url,
        ).get("result")
        if isinstance(result, list):
            return result[0] if result else None
        if isinstance(result, dict):
            return result
        return None

    def build_entity_url(self, entity: str, entity_id: str | int | None) -> str | None:
        if not entity_id:
            return None
        base = self.config.get("base_url") or self.config.get("bitrix_base_url")
        domain = self.config.get("domain") or self.config.get("bitrix_domain")
        if not base and domain:
            base = f"https://{domain}"
        if not base:
            return None
        return urljoin(base.rstrip("/") + "/", f"crm/{quote(entity)}/details/{quote(str(entity_id))}/")

    def _method_url(self, method: str, webhook_url: str | None = None) -> str:
        webhook_url = webhook_url or self.config.get("webhook_url")
        if webhook_url:
            return urljoin(webhook_url.rstrip("/") + "/", f"{method}.json")

        base_url = self.config.get("base_url")
        if not base_url:
            raise ValueError("Bitrix base URL or webhook URL is not configured")
        return urljoin(base_url.rstrip("/") + "/", f"rest/{method}.json")
