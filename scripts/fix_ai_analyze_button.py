#!/usr/bin/env python3
"""Patch the Haravan Helpdesk AI analyze HD Form Script.

The production button currently treats any response without an explicit
`success: true` as a failure. Frappe/Helpdesk form `call(...)` wrappers may
return the server payload directly, under `message`, or under `data`, so the
button can show "API tra ve loi." even when the API returned usable data.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests


SCRIPT_NAME = "AI - Ticket Analyze Action"

PATCHED_SCRIPT = r'''function setupForm({ doc, call, createToast }) {
  const actions = [];
  if (!doc.name) return { actions };

  const state = window.__haravanAiAnalyzeState || (window.__haravanAiAnalyzeState = {});
  const toast = (title, message, variant = "info") =>
    createToast?.({ title, message, variant });

  const unwrap = (response) => {
    const first = response?.message ?? response?.data ?? response;
    return first?.message && typeof first.message === "object" ? first.message : first || {};
  };

  const isSuccess = (payload) => {
    if (payload.success === false) return false;
    if (payload.exc || payload.exception || payload._server_messages) return false;
    return true;
  };

  const errorMessage = (payload) => {
    if (typeof payload.message === "string") return payload.message;
    if (payload.error) return payload.error;
    if (payload.exception) return payload.exception;
    return "API tra ve loi.";
  };

  actions.push({
    group: "AI",
    hideLabel: true,
    items: [
      {
        label: "AI Phan tich",
        variant: "solid",
        theme: "gray",
        onClick: async () => {
          if (state[doc.name]) {
            toast("AI dang xu ly", "Ticket nay dang duoc AI phan tich.", "info");
            return;
          }

          state[doc.name] = true;
          try {
            toast("Dang phan tich", "AI dang cap nhat thong tin ticket.");
            const payload = unwrap(await call("haravan_ai_analyze_ticket", { name: doc.name }));

            if (!isSuccess(payload)) {
              throw new Error(errorMessage(payload));
            }

            const data = payload.data || payload;
            const updatedFields = data.updated_fields || [];
            const message =
              typeof payload.message === "string"
                ? payload.message
                : updatedFields.length
                  ? `AI da cap nhat ${updatedFields.length} truong.`
                  : "AI da phan tich ticket.";

            toast("Da phan tich", message, "success");
            setTimeout(() => window.location.reload(), 600);
          } catch (error) {
            toast("Loi AI", error.message || "Khong the phan tich ticket.", "error");
          } finally {
            delete state[doc.name];
          }
        },
      },
    ],
  });

  return { actions };
}
'''


def env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"Missing required env var: {name}")
    return value


def request(session: requests.Session, method: str, url: str, **kwargs):
    response = session.request(method, url, timeout=30, **kwargs)
    if response.status_code >= 400:
        raise SystemExit(f"{method} {url} failed: {response.status_code} {response.text[:500]}")
    return response.json()


def main() -> int:
    site = env("HARAVAN_HELP_SITE").rstrip("/")
    api_key = env("HARAVAN_HELP_API_KEY")
    api_secret = env("HARAVAN_HELP_API_SECRET")

    session = requests.Session()
    session.headers.update({
        "Authorization": f"token {api_key}:{api_secret}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    })

    encoded_name = requests.utils.quote(SCRIPT_NAME, safe="")
    doc_url = f"{site}/api/resource/HD%20Form%20Script/{encoded_name}"
    current = request(session, "GET", doc_url)["data"]

    backup_dir = Path("backups") / f"ai_analyze_button_fix_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    (backup_dir / "hd_form_script_before.json").write_text(
        json.dumps(current, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    payload = {"script": PATCHED_SCRIPT, "enabled": 1}
    updated = request(session, "PUT", doc_url, data=json.dumps(payload))["data"]
    (backup_dir / "hd_form_script_after.json").write_text(
        json.dumps(updated, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Patched {SCRIPT_NAME}. Backup: {backup_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
