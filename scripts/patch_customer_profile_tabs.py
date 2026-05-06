#!/usr/bin/env python3
"""Patch the live Customer Profile HD Form Script to use Profile/Bitrix tabs."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests


FORM_SCRIPT_NAME = "Profile - Ticket Customer Button"
ENV_PATHS = ("/Volumes/Data/Skills/frappe_helpdesk/.env",)


def load_env_files() -> dict[str, str]:
    values: dict[str, str] = {}
    for env_path in ENV_PATHS:
        path = Path(env_path)
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.lstrip().startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip("\"'")
    return values


FILE_ENV = load_env_files()


def env(name: str, fallback: str | None = None) -> str:
    value = os.environ.get(name) or FILE_ENV.get(name) or (
        os.environ.get(fallback) or FILE_ENV.get(fallback, "") if fallback else ""
    )
    value = (value or "").strip()
    if not value:
        raise SystemExit(f"Missing required env var: {name}")
    return value


def request_json(session: requests.Session, method: str, url: str, **kwargs):
    response = session.request(method, url, timeout=30, **kwargs)
    if response.status_code >= 400:
        raise SystemExit(f"{method} {url} failed: {response.status_code} {response.text[:500]}")
    return response.json()


def resource_url(site: str, doctype: str, name: str) -> str:
    return f"{site}/api/resource/{requests.utils.quote(doctype, safe='')}/{requests.utils.quote(name, safe='')}"


def patch_script(source: str) -> tuple[str, bool]:
    if "function setProfileTabs" in source and "data-profile-tab" in source:
        repaired = source.replace("escapeHtml(", "esc(")
        open_marker = "  async function openProfile(refresh) {"
        first_open = repaired.find(open_marker)
        second_open = repaired.find(open_marker, first_open + len(open_marker)) if first_open != -1 else -1
        if second_open != -1:
            repaired = repaired[:first_open] + repaired[second_open:]

        if "const segmentRows =" not in repaired:
            bitrix_rows_end = repaired.find("\n\n  const row = ([label, value]) => {")
            if bitrix_rows_end != -1:
                extra_rows = r'''

  const segmentRows = [
    ["Current HSI Segment", company.current_hsi_segment || company.hsi_segment],
    ["Current HSI Detail", company.current_hsi_detail],
    ["Last HSI Segment", company.last_hsi_segment],
    ["Last HSI Detail", company.last_hsi_detail],
    ["Current Shopplan", company.current_shopplan || company.shopplan],
    ["Plan Status", company.shopplan_status],
    ["Days Left", company.shopplan_days_left],
    ["Expiry", company.shopplan_expiry || company.expiry || company.expired_at],
    ["Signed Current Plan", company.current_shopplan_date],
    ["First Paid", company.first_shopplan_date],
    ["Shop Created", company.shop_created_date],
  ];

  const ownerRows = [
    ["Assigned", company.assigned_by_name || responsible.name || company.assigned_by_id],
    ["Assigned Email", company.assigned_by_email || responsible.email],
    ["Shop Owner", company.owner_name],
    ["Owner Email", company.owner_email],
    ["Owner Phone", company.owner_phone],
  ];

  const bitrixContactRows = [
    ["Contact", bitrixContact.title || bitrixContact.name],
    ["Contact ID", bitrixContact.contact_id || bitrixContact.ID || bitrixContact.id || contact.custom_bitrix_contact_id],
    ["Contact URL", bitrixContact.url || contact.custom_bitrix_contact_url],
  ];

  const helpdeskRows = [
    ["Ticket", ticket.name || doc.name],
    ["Raised By", ticket.raised_by || doc.raised_by],
    ["Contact", contact.full_name || contact.name || doc.contact],
    ["Email", contact.email_id || doc.raised_by],
    ["Phone", contact.mobile_no || contact.phone || doc.custom_contact_phone],
    ["Store URL", doc.custom_store_url],
    ["MyHaravan", doc.custom_myharavan_domain || doc.custom_my_haravan_domain],
    ["Org ID", ticket.custom_orgid || doc.custom_orgid || doc.custom_haravan_profile_orgid],
    ["Service Group", doc.custom_service_group || doc.agent_group],
    ["Service Name", doc.custom_service_name],
  ];
'''
                repaired = repaired[:bitrix_rows_end] + extra_rows + repaired[bitrix_rows_end:]

        duplicate_stats = (
            '${stat("Expiry", company.shopplan_expiry || company.expiry || company.expired_at)}\n'
            '        ${stat("Days Left", company.shopplan_days_left)}\n'
            '        ${stat("Expiry", company.shopplan_expiry || company.expiry || company.expired_at)}\n'
            '        ${stat("Days Left", company.shopplan_days_left)}\n'
            '        ${stat("Assigned", responsible.email || responsible.name || company.assigned_name)}'
        )
        compact_stats = (
            '${stat("Expiry", company.shopplan_expiry || company.expiry || company.expired_at)}\n'
            '        ${stat("Days Left", company.shopplan_days_left)}\n'
            '        ${stat("Assigned", responsible.email || responsible.name || company.assigned_name)}'
        )
        repaired = repaired.replace(duplicate_stats, compact_stats)
        if '${stat("Days Left", company.shopplan_days_left)}' not in repaired:
            repaired = repaired.replace(
                '${stat("Assigned", responsible.email || responsible.name || company.assigned_name)}',
                compact_stats,
            )
        repaired = repaired.replace(
            '<div class="hcp-table">${profileRows.map(row).join("")}</div>\n    `',
            '<div class="hcp-table">${profileRows.map(row).join("")}</div>\n'
            '      ${segmentRows.map(row).join("") ? `<h3>Segment & Shopplan</h3><div class="hcp-table">${segmentRows.map(row).join("")}</div>` : ""}\n'
            '      ${ownerRows.map(row).join("") ? `<h3>Phu trach</h3><div class="hcp-table">${ownerRows.map(row).join("")}</div>` : ""}\n'
            '      ${bitrixContactRows.map(row).join("") ? `<h3>Bitrix Contact</h3><div class="hcp-table">${bitrixContactRows.map(row).join("")}</div>` : ""}\n'
            '      ${helpdeskRows.map(row).join("") ? `<h3>Thong tin ticket</h3><div class="hcp-table">${helpdeskRows.map(row).join("")}</div>` : ""}\n'
            '    `',
        )
        repaired = repaired.replace(
            '<div class="hcp-table">${bitrixRows.map(row).join("")}</div>\n  `',
            '<div class="hcp-table">${bitrixRows.map(row).join("")}</div>\n'
            '    ${segmentRows.map(row).join("") ? `<h3>Segment & Shopplan</h3><div class="hcp-table">${segmentRows.map(row).join("")}</div>` : ""}\n'
            '    ${ownerRows.map(row).join("") ? `<h3>Phu trach</h3><div class="hcp-table">${ownerRows.map(row).join("")}</div>` : ""}\n'
            '    ${bitrixContactRows.map(row).join("") ? `<h3>Bitrix Contact</h3><div class="hcp-table">${bitrixContactRows.map(row).join("")}</div>` : ""}\n'
            '    ${helpdeskRows.map(row).join("") ? `<h3>Thong tin ticket</h3><div class="hcp-table">${helpdeskRows.map(row).join("")}</div>` : ""}\n'
            '  `',
        )

        replacements = {
            ".customer-profile-dialog .modal-dialog{max-width:760px}": (
                ".customer-profile-dialog .modal-dialog{max-width:720px}"
            ),
            ".customer-profile-dialog .modal-content{border-radius:18px}": (
                ".customer-profile-dialog .modal-content{border-radius:14px}"
            ),
            ".hcp-tabs{display:flex;gap:22px;border-bottom:1px solid #d9dee7;margin:4px 0 22px}": (
                ".hcp-tabs{display:flex;gap:18px;border-bottom:1px solid #d9dee7;margin:0 0 16px}"
            ),
            ".hcp-tab{border:0;background:transparent;color:#98a2b3;font-size:16px;font-weight:700;padding:12px 0 11px;min-width:90px;border-bottom:3px solid transparent;cursor:pointer}": (
                ".hcp-tab{border:0;background:transparent;color:#98a2b3;font-size:14px;font-weight:700;padding:9px 0 8px;min-width:82px;border-bottom:3px solid transparent;cursor:pointer}"
            ),
            ".hcp-tab{border:0;background:transparent;color:#98a2b3;font-size:16px;font-weight:700;padding:12px 0 11px;min-width:90px;border-bottom:3px solid transparent}": (
                ".hcp-tab{border:0;background:transparent;color:#98a2b3;font-size:14px;font-weight:700;padding:9px 0 8px;min-width:82px;border-bottom:3px solid transparent}"
            ),
            ".hcp-topline{display:flex;justify-content:space-between;gap:14px;margin-bottom:16px}": (
                ".hcp-topline{display:flex;justify-content:space-between;gap:12px;margin-bottom:12px}"
            ),
            ".hcp-name{font-size:22px;line-height:1.2;font-weight:800;color:#111827;word-break:break-word}": (
                ".hcp-name{font-size:16px;line-height:1.3;font-weight:750;color:#111827;word-break:break-word}"
            ),
            ".hcp-meta{font-size:13px;color:#667085;margin-top:4px}": (
                ".hcp-meta{font-size:12px;color:#667085;margin-top:3px}"
            ),
            ".hcp-actions{display:flex;gap:8px;justify-content:flex-end;flex-wrap:wrap}": (
                ".hcp-actions{display:flex;gap:6px;justify-content:flex-end;flex-wrap:wrap}"
            ),
            ".hcp-small{border:1px solid #cfd6df;background:#fff;color:#344054;border-radius:8px;min-height:34px;padding:6px 10px;font-size:13px;font-weight:700;cursor:pointer}": (
                ".hcp-small{border:1px solid #cfd6df;background:#fff;color:#344054;border-radius:7px;min-height:32px;padding:5px 10px;font-size:12.5px;font-weight:650;cursor:pointer;line-height:1.2}"
            ),
            ".hcp-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin-bottom:18px}": (
                ".hcp-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin-bottom:14px}"
            ),
            ".hcp-stat{border:1px solid #d9dee7;border-radius:8px;padding:12px 14px;min-height:74px}": (
                ".hcp-stat{border:1px solid #d9dee7;border-radius:7px;padding:9px 11px;min-height:58px}"
            ),
            ".hcp-stat span{display:block;color:#667085;font-size:12px;font-weight:800;text-transform:uppercase;margin-bottom:8px}": (
                ".hcp-stat span{display:block;color:#667085;font-size:10.5px;font-weight:750;text-transform:uppercase;margin-bottom:5px;letter-spacing:.03em}"
            ),
            ".hcp-stat strong{font-size:16px;color:#111827;word-break:break-word}": (
                ".hcp-stat strong{font-size:13.5px;color:#111827;word-break:break-word}"
            ),
            ".hcp-pill{display:inline-flex!important;align-items:center;min-height:24px;border-radius:999px;padding:2px 10px;font-size:13px;font-weight:800;text-transform:none!important;margin:0!important}": (
                ".hcp-pill{display:inline-flex!important;align-items:center;min-height:22px;border-radius:999px;padding:2px 8px;font-size:12px;font-weight:750;text-transform:none!important;margin:0!important}"
            ),
            ".hcp-table{border:1px solid #d9dee7;border-radius:8px;padding:10px 14px}": (
                ".hcp-table{border:1px solid #d9dee7;border-radius:7px;padding:6px 10px}"
            ),
            ".hcp-row{display:flex;justify-content:space-between;gap:16px;padding:9px 0;border-bottom:1px solid #eef1f5}": (
                ".hcp-row{display:flex;justify-content:space-between;gap:14px;padding:7px 0;border-bottom:1px solid #eef1f5;font-size:13px}"
            ),
            ".hcp-empty{border:1px dashed #d0d5dd;border-radius:8px;padding:22px;text-align:center;color:#667085}": (
                ".hcp-empty{border:1px dashed #d0d5dd;border-radius:7px;padding:16px;text-align:center;color:#667085;font-size:13px}"
            ),
            ".hcp-loading{border:1px solid #d9dee7;border-radius:8px;padding:26px;text-align:center;color:#667085}": (
                ".hcp-loading{border:1px solid #d9dee7;border-radius:7px;padding:18px;text-align:center;color:#667085;font-size:13px}"
            ),
            ".hcp-spinner{width:28px;height:28px;border:3px solid #e5e7eb;border-top-color:#111827;border-radius:50%;margin:0 auto 12px;animation:hcp-spin .8s linear infinite}": (
                ".hcp-spinner{width:24px;height:24px;border:3px solid #e5e7eb;border-top-color:#111827;border-radius:50%;margin:0 auto 10px;animation:hcp-spin .8s linear infinite}"
            ),
        }
        for old, new in replacements.items():
            repaired = repaired.replace(old, new)

        compact_additions = (
            ".customer-profile-dialog .modal-body{padding:18px 24px 22px}"
            "#cp-profile{font-size:13px;line-height:1.42;color:#111827}"
            "#cp-profile h3{font-size:14px;font-weight:750;margin:14px 0 7px}"
            ".hcp-row span{font-size:13px}"
            ".hcp-row strong{font-size:13px;font-weight:650}"
        )
        if ".customer-profile-dialog .modal-body{padding:18px 24px 22px}" not in repaired:
            repaired = repaired.replace("#cp-profile *{box-sizing:border-box}", "#cp-profile *{box-sizing:border-box}" + compact_additions)
        return repaired, repaired != source

    render_marker = "  const render = (payload) => {"
    render_start = source.find(render_marker)
    if render_start == -1:
        raise SystemExit("Could not find render(payload) in HD Form Script.")

    open_marker = "\n\n  async function openProfile(refresh) {"
    render_end = source.find(open_marker, render_start)
    if render_end == -1:
        raise SystemExit("Could not find openProfile(refresh) after render(payload).")

    actions_marker = "\n\n  actions.push({"
    open_end = source.find(actions_marker, render_end)
    if open_end == -1:
        raise SystemExit("Could not find actions.push after openProfile(refresh).")

    render_replacement = r'''  const render = (payload, activeTabOverride) => {
  const data = payload.data || {};
  const ticket = data.ticket || {};
  const customer = data.customer || {};
  const contact = data.contact || {};
  const bitrix = data.bitrix || {};
  const company = bitrix.company || {};
  const bitrixContact = bitrix.contact || {};
  const responsible = bitrix.responsible || {};
  const sk = `cpProfile_${Date.now()}_${Math.random().toString(36).slice(2)}`;
  const hasCustomer = Boolean(customer.name || customer.customer_name || customer.company_name || doc.customer);
  const activeTab = activeTabOverride || (hasCustomer ? "profile" : "bitrix");

  const status = bitrix.status || customer.bitrix_sync_status || "local";
  const statusClass = ["matched", "cached", "local", "complete"].includes(String(status).toLowerCase())
    ? "ok"
    : "warn";

  const title = esc(customer.customer_name || customer.company_name || customer.name || doc.customer || company.company_name || company.title || "Customer Profile");
  const companyId = esc(customer.haravan_orgid || customer.custom_haravan_orgid || company.company_id || ticket.custom_orgid || doc.custom_orgid || "");
  const bitrixId = esc(company.bitrix_id || company.id || customer.bitrix_company_id || customer.custom_bitrix_company_id || "");
  const bitrixUrl = company.url || customer.bitrix_company_url || customer.custom_bitrix_company_url || "";

  const profileRows = [
    ["Company", customer.customer_name || customer.company_name || customer.name || doc.customer],
    ["Company ID", customer.haravan_orgid || customer.custom_haravan_orgid || company.company_id || ticket.custom_orgid || doc.custom_orgid],
    ["Bitrix ID", company.bitrix_id || company.id || customer.bitrix_company_id || customer.custom_bitrix_company_id],
    ["Membership", customer.membership || company.membership],
    ["Lookup", bitrix.lookup_value || company.company_id || customer.haravan_orgid],
    ["Contact", contact.email_id || contact.email || contact.name || doc.contact],
    ["Raised By", ticket.raised_by || doc.raised_by],
    ["Phone", contact.mobile_no || contact.phone || doc.custom_contact_phone],
    ["MyHaravan", doc.custom_myharavan_domain || doc.custom_my_haravan_domain],
  ];

  const bitrixRows = [
    ["Status", status],
    ["Company", company.company_name || company.title],
    ["Company ID", company.company_id || customer.haravan_orgid],
    ["Bitrix ID", company.bitrix_id || company.id || customer.bitrix_company_id],
    ["Segment", company.current_hsi_segment || company.hsi_segment || customer.customer_segment],
    ["Shopplan", company.current_shopplan || company.shopplan],
    ["Expiry", company.expiry || company.expired_at],
    ["Assigned", responsible.email || responsible.name || company.assigned_name],
  ];

  const row = ([label, value]) => {
    if (value === undefined || value === null || value === "") return "";
    return `<div class="hcp-row"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`;
  };

  const stat = (label, value, html) => {
    if (value === undefined || value === null || value === "") return "";
    return `<div class="hcp-stat"><span>${escapeHtml(label)}</span><strong>${html ? value : escapeHtml(value)}</strong></div>`;
  };

  window[sk] = {
    openBitrix: (url) => {
      if (url) window.open(url, "_blank", "noopener");
    },
    refreshBitrix: async (button) => {
      const oldText = button ? button.textContent : "";
      try {
        if (button) {
          button.disabled = true;
          button.textContent = "Dang tai...";
        }
        const refreshed = unwrap(await call(PROFILE_METHOD, { ticket: doc.name, refresh: 1 }));
        if (!isSuccess(refreshed)) throw new Error(errorMessage(refreshed, "Khong tai duoc Bitrix profile."));
        const root = document.getElementById("cp-profile");
        if (root) root.outerHTML = render(refreshed, "bitrix");
        setTimeout(setProfileTabs, 0);
      } catch (error) {
        toast("Customer Profile", error.message || "Bitrix phan hoi cham hoac bi loi.", "error");
        if (button) {
          button.disabled = false;
          button.textContent = oldText || "Lam moi";
        }
      }
    },
    syncCustomer: async (button) => {
      const oldText = button ? button.textContent : "";
      try {
        if (button) {
          button.disabled = true;
          button.textContent = "Dang dong bo...";
        }
        const syncCompanyId = company.company_id || customer.haravan_orgid || doc.custom_orgid || "";
        const synced = unwrap(await call(SYNC_METHOD, { ticket: doc.name, company_id: syncCompanyId }));
        if (!isSuccess(synced)) throw new Error(errorMessage(synced, "Khong dong bo duoc HD Customer."));
        const syncedTicket = ((synced.data || {}).ticket || {});
        if (syncedTicket.customer) doc.customer = syncedTicket.customer;
        toast("Customer Profile", synced.message || "Da dong bo HD Customer", "success");
        const refreshed = unwrap(await call(PROFILE_METHOD, { ticket: doc.name, refresh: 0 }));
        const root = document.getElementById("cp-profile");
        if (root && isSuccess(refreshed)) root.outerHTML = render(refreshed, "profile");
        setTimeout(setProfileTabs, 0);
      } catch (error) {
        toast("Customer Profile", error.message || "Khong dong bo duoc HD Customer.", "error");
        if (button) {
          button.disabled = false;
          button.textContent = oldText || "Dong bo";
        }
      }
    },
  };

  const profileHtml = hasCustomer
    ? `
      <div class="hcp-topline">
        <div>
          <div class="hcp-name">${title}</div>
          <div class="hcp-meta">Company ID ${companyId || "-"} / Bitrix ${bitrixId || "-"}</div>
        </div>
        <div class="hcp-actions">
          ${bitrixUrl ? `<button class="hcp-small" onclick="window['${sk}'].openBitrix('${esc(bitrixUrl)}')">Mo Bitrix</button>` : ""}
          <button class="hcp-small primary" onclick="window['${sk}'].refreshBitrix(this)">Lam moi Bitrix</button>
        </div>
      </div>
      <div class="hcp-grid">
        ${stat("Status", `<span class="hcp-pill ${statusClass}">${escapeHtml(status)}</span>`, true)}
        ${stat("Segment", company.current_hsi_segment || company.hsi_segment || customer.customer_segment)}
        ${stat("Shopplan", company.current_shopplan || company.shopplan)}
        ${stat("Assigned", responsible.email || responsible.name || company.assigned_name)}
      </div>
      <h3>Khach hang</h3>
      <div class="hcp-table">${profileRows.map(row).join("")}</div>
    `
    : `<div class="hcp-empty">Ticket chua co HD Customer. Bitrix se duoc goi de lam giau du lieu.</div>`;

  const bitrixHtml = `
    <div class="hcp-topline">
      <div>
        <div class="hcp-name">${escapeHtml(company.company_name || company.title || title)}</div>
        <div class="hcp-meta">Lookup ${escapeHtml(bitrix.lookup_value || company.company_id || companyId || "-")}</div>
      </div>
      <div class="hcp-actions">
        ${bitrixUrl ? `<button class="hcp-small" onclick="window['${sk}'].openBitrix('${esc(bitrixUrl)}')">Mo Bitrix</button>` : ""}
        ${company.company_id || company.id ? `<button class="hcp-small" onclick="window['${sk}'].syncCustomer(this)">Dong bo</button>` : ""}
        <button class="hcp-small primary" onclick="window['${sk}'].refreshBitrix(this)">Lam moi</button>
      </div>
    </div>
    <div class="hcp-grid">
      ${stat("Status", `<span class="hcp-pill ${statusClass}">${escapeHtml(status)}</span>`, true)}
      ${stat("Company ID", company.company_id || customer.haravan_orgid)}
      ${stat("Bitrix ID", company.bitrix_id || company.id || customer.bitrix_company_id)}
      ${stat("Assigned", responsible.email || responsible.name || company.assigned_name)}
    </div>
    <h3>Bitrix</h3>
    <div class="hcp-table">${bitrixRows.map(row).join("")}</div>
  `;

  const body = `
    <style>
      .customer-profile-dialog .modal-dialog{max-width:760px}
      .customer-profile-dialog .modal-content{border-radius:18px}
      #cp-profile *{box-sizing:border-box}
      .hcp-tabs{display:flex;gap:22px;border-bottom:1px solid #d9dee7;margin:4px 0 22px}
      .hcp-tab{border:0;background:transparent;color:#98a2b3;font-size:16px;font-weight:700;padding:12px 0 11px;min-width:90px;border-bottom:3px solid transparent;cursor:pointer}
      .hcp-tab.active{color:#111827;border-bottom-color:#111827}
      .hcp-panel{display:none}.hcp-panel.active{display:block}
      .hcp-topline{display:flex;justify-content:space-between;gap:14px;margin-bottom:16px}
      .hcp-name{font-size:22px;line-height:1.2;font-weight:800;color:#111827;word-break:break-word}
      .hcp-meta{font-size:13px;color:#667085;margin-top:4px}
      .hcp-actions{display:flex;gap:8px;justify-content:flex-end;flex-wrap:wrap}
      .hcp-small{border:1px solid #cfd6df;background:#fff;color:#344054;border-radius:8px;min-height:34px;padding:6px 10px;font-size:13px;font-weight:700;cursor:pointer}
      .hcp-small.primary{background:#111827;border-color:#111827;color:#fff}
      .hcp-small:disabled{opacity:.62;cursor:wait}
      .hcp-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin-bottom:18px}
      .hcp-stat{border:1px solid #d9dee7;border-radius:8px;padding:12px 14px;min-height:74px}
      .hcp-stat span{display:block;color:#667085;font-size:12px;font-weight:800;text-transform:uppercase;margin-bottom:8px}
      .hcp-stat strong{font-size:16px;color:#111827;word-break:break-word}
      .hcp-pill{display:inline-flex!important;align-items:center;min-height:24px;border-radius:999px;padding:2px 10px;font-size:13px;font-weight:800;text-transform:none!important;margin:0!important}
      .hcp-pill.ok{background:#dcfae6;color:#067647}.hcp-pill.warn{background:#fffaeb;color:#b54708}
      .hcp-table{border:1px solid #d9dee7;border-radius:8px;padding:10px 14px}
      .hcp-row{display:flex;justify-content:space-between;gap:16px;padding:9px 0;border-bottom:1px solid #eef1f5}
      .hcp-row:last-child{border-bottom:0}.hcp-row span{color:#667085}.hcp-row strong{text-align:right;word-break:break-word;color:#111827}
      .hcp-empty{border:1px dashed #d0d5dd;border-radius:8px;padding:22px;text-align:center;color:#667085}
      .hcp-loading{border:1px solid #d9dee7;border-radius:8px;padding:26px;text-align:center;color:#667085}
      .hcp-spinner{width:28px;height:28px;border:3px solid #e5e7eb;border-top-color:#111827;border-radius:50%;margin:0 auto 12px;animation:hcp-spin .8s linear infinite}
      @keyframes hcp-spin{to{transform:rotate(360deg)}}
      @media(max-width:640px){.hcp-topline{flex-direction:column}.hcp-grid{grid-template-columns:1fr}.hcp-row{flex-direction:column;gap:4px}.hcp-row strong{text-align:left}}
    </style>
    <div id="cp-profile">
    <div class="hcp-tabs">
      <button class="hcp-tab ${activeTab === "profile" ? "active" : ""}" data-profile-tab="profile">Profile</button>
      <button class="hcp-tab ${activeTab === "bitrix" ? "active" : ""}" data-profile-tab="bitrix">Bitrix</button>
    </div>
    <div class="hcp-panel ${activeTab === "profile" ? "active" : ""}" data-profile-panel="profile">${profileHtml}</div>
    <div class="hcp-panel ${activeTab === "bitrix" ? "active" : ""}" data-profile-panel="bitrix">${bitrixHtml}</div>
    </div>
  `;
  return body;
  };

  const renderLoading = () => `
    <style>
      #cp-profile *{box-sizing:border-box}
      .hcp-tabs{display:flex;gap:22px;border-bottom:1px solid #d9dee7;margin:4px 0 22px}
      .hcp-tab{border:0;background:transparent;color:#98a2b3;font-size:16px;font-weight:700;padding:12px 0 11px;min-width:90px;border-bottom:3px solid transparent}
      .hcp-tab.active{color:#111827;border-bottom-color:#111827}
      .hcp-loading{border:1px solid #d9dee7;border-radius:8px;padding:26px;text-align:center;color:#667085}
      .hcp-spinner{width:28px;height:28px;border:3px solid #e5e7eb;border-top-color:#111827;border-radius:50%;margin:0 auto 12px;animation:hcp-spin .8s linear infinite}
      @keyframes hcp-spin{to{transform:rotate(360deg)}}
    </style>
    <div id="cp-profile">
      <div class="hcp-tabs">
        <button class="hcp-tab" data-profile-tab="profile">Profile</button>
        <button class="hcp-tab active" data-profile-tab="bitrix">Bitrix</button>
      </div>
      <div class="hcp-loading"><div class="hcp-spinner"></div><div>Dang doi du lieu Bitrix...</div></div>
    </div>`;

  function setProfileTabs() {
    const root = document.getElementById("cp-profile");
    if (!root) return;
    root.querySelectorAll("[data-profile-tab]").forEach((button) => {
      button.addEventListener("click", () => {
        const tab = button.getAttribute("data-profile-tab");
        root.querySelectorAll("[data-profile-tab]").forEach((node) => node.classList.remove("active"));
        root.querySelector(`[data-profile-tab="${tab}"]`)?.classList.add("active");
        root.querySelectorAll("[data-profile-panel]").forEach((node) => node.classList.remove("active"));
        root.querySelector(`[data-profile-panel="${tab}"]`)?.classList.add("active");
      });
    });
  }'''

    open_replacement = r'''  async function openProfile(refresh) {
    if (doc.customer && !refresh) {
      const localPayload = {
        success: true,
        data: {
          ticket: {
            name: doc.name,
            raised_by: doc.raised_by,
            custom_orgid: doc.custom_orgid || doc.custom_haravan_profile_orgid,
          },
          customer: {
            name: doc.customer,
            customer_name: doc.customer,
            haravan_orgid: doc.custom_orgid || doc.custom_haravan_profile_orgid,
            custom_haravan_orgid: doc.custom_orgid || doc.custom_haravan_profile_orgid,
          },
          contact: {
            name: doc.contact,
            email_id: doc.raised_by,
            phone: doc.custom_contact_phone,
          },
          bitrix: { status: "local" },
        },
        message: "HD Customer loaded locally.",
      };
      $dialog({ title: "Customer Profile", html: render(localPayload, "profile") });
      setTimeout(setProfileTabs, 0);
      return;
    }

    $dialog({ title: "Customer Profile", html: renderLoading() });
    setTimeout(setProfileTabs, 0);
    try {
      const payload = unwrap(await call(PROFILE_METHOD, { ticket: doc.name, refresh: 1 }));
      if (!isSuccess(payload)) throw new Error(errorMessage(payload, "Khong tai duoc ho so khach hang."));
      const root = document.getElementById("cp-profile");
      if (root) root.outerHTML = render(payload, "bitrix");
      setTimeout(setProfileTabs, 0);
    } catch (error) {
      const root = document.getElementById("cp-profile");
      if (root) {
        root.innerHTML = `
          <div class="hcp-tabs">
            <button class="hcp-tab" data-profile-tab="profile">Profile</button>
            <button class="hcp-tab active" data-profile-tab="bitrix">Bitrix</button>
          </div>
          <div class="hcp-empty">Bitrix phan hoi cham hoac bi loi. Vui long thu lai.</div>`;
      }
      toast("Customer Profile", error.message || "Khong tai duoc ho so khach hang.", "error");
    }
  }'''

    patched = source[:render_start] + render_replacement + source[render_end:open_end] + open_replacement + source[open_end:]
    return patched, True


def main() -> int:
    site = env("HARAVAN_HELP_SITE", "SITE_HARAVAN_URL").rstrip("/")
    api_key = env("HARAVAN_HELP_API_KEY", "SITE_HARAVAN_API_KEY")
    api_secret = env("HARAVAN_HELP_API_SECRET", "SITE_HARAVAN_API_SECRET")

    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"token {api_key}:{api_secret}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
    )

    backup_dir = Path("backups") / f"customer_profile_tabs_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    url = resource_url(site, "HD Form Script", FORM_SCRIPT_NAME)
    current = request_json(session, "GET", url)["data"]
    (backup_dir / "HD_Form_Script_Profile_Ticket_Customer_Button_before.json").write_text(
        json.dumps(current, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (backup_dir / "profile_ticket_customer_button_before.js").write_text(current.get("script") or "", encoding="utf-8")

    patched_script, changed = patch_script(current.get("script") or "")
    if changed:
        updated = request_json(session, "PUT", url, data=json.dumps({"script": patched_script}))["data"]
    else:
        updated = current

    (backup_dir / "HD_Form_Script_Profile_Ticket_Customer_Button_after.json").write_text(
        json.dumps(updated, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (backup_dir / "profile_ticket_customer_button_after.js").write_text(updated.get("script") or "", encoding="utf-8")

    print(json.dumps({"changed": changed, "backup_dir": str(backup_dir)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
