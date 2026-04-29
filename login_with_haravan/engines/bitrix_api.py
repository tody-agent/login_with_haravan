"""Server-side Bitrix REST helpers for customer profile enrichment."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote, urljoin

import requests


class BitrixClient:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.timeout = int(config.get("timeout_seconds") or 15)

    def call(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = self._method_url(method)
        payload = params or {}
        if self.config.get("access_token") and not self.config.get("webhook_url"):
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
            filters.append({"UF_CRM_HARAVAN_ORG_ID": haravan_orgid})
        if domain:
            filters.append({"WEB": domain})
            filters.append({"%TITLE": domain})

        for filter_payload in filters:
            result = self.call(
                "crm.company.list",
                {
                    "filter": filter_payload,
                    "select": ["*", "UF_*", "EMAIL", "PHONE", "WEB"],
                    "order": {"DATE_MODIFY": "DESC"},
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

    def _method_url(self, method: str) -> str:
        webhook_url = self.config.get("webhook_url")
        if webhook_url:
            return urljoin(webhook_url.rstrip("/") + "/", f"{method}.json")

        base_url = self.config.get("base_url")
        if not base_url:
            raise ValueError("Bitrix base URL or webhook URL is not configured")
        return urljoin(base_url.rstrip("/") + "/", f"rest/{method}.json")
