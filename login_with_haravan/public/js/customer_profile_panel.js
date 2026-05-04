/**
 * Bitrix Customer Profile Panel
 *
 * Opens an in-ticket customer profile panel instead of sending agents to the
 * raw Contact desk record. All Bitrix data is fetched through server APIs.
 */
(function () {
  "use strict";

  var PANEL_ID = "bitrix-customer-profile-panel";
  var METHOD = "login_with_haravan.customer_profile.get_ticket_customer_profile";

  function isTicketRoute() {
    return window.location.pathname.indexOf("/helpdesk/tickets/") !== -1;
  }

  function ticketNameFromPath() {
    var parts = window.location.pathname.split("/").filter(Boolean);
    return parts[parts.length - 1] || "";
  }

  function ensurePanel() {
    var existing = document.getElementById(PANEL_ID);
    if (existing) return existing;

    var panel = document.createElement("aside");
    panel.id = PANEL_ID;
    panel.style.cssText = [
      "position: fixed",
      "right: 0",
      "top: 0",
      "z-index: 1050",
      "width: min(420px, 100vw)",
      "height: 100vh",
      "background: #fff",
      "border-left: 1px solid #d1d8dd",
      "box-shadow: -8px 0 24px rgba(0,0,0,.12)",
      "display: none",
      "overflow: auto",
      "font-family: Inter, sans-serif",
    ].join(";");
    document.body.appendChild(panel);
    return panel;
  }

  function closePanel() {
    var panel = document.getElementById(PANEL_ID);
    if (panel) panel.style.display = "none";
  }

  function escapeHtml(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function field(label, value) {
    if (value == null || value === "") return "";
    return (
      '<div style="display:flex;justify-content:space-between;gap:12px;padding:7px 0;border-bottom:1px solid #f1f3f5">' +
      '<span style="color:#667085">' +
      escapeHtml(label) +
      "</span>" +
      '<strong style="text-align:right;color:#1f2937;word-break:break-word">' +
      escapeHtml(value) +
      "</strong>" +
      "</div>"
    );
  }

  function section(title, body) {
    if (!body) return "";
    return (
      '<section style="padding:14px 18px">' +
      '<h3 style="font-size:14px;margin:0 0 8px;color:#111827">' +
      escapeHtml(title) +
      "</h3>" +
      body +
      "</section>"
    );
  }

  function render(panel, payload) {
    var data = (payload && payload.data) || {};
    var customer = data.customer || {};
    var contact = data.contact || {};
    var bitrix = data.bitrix || {};
    var company = bitrix.company || {};
    var bitrixContact = bitrix.contact || {};
    var responsible = bitrix.responsible || {};
    var haravanLinks = data.haravan || [];

    panel.innerHTML =
      '<div style="position:sticky;top:0;background:#fff;border-bottom:1px solid #d1d8dd;padding:14px 18px;display:flex;align-items:center;justify-content:space-between;gap:12px">' +
      '<div><div style="font-size:16px;font-weight:650;color:#111827">Customer Profile</div>' +
      '<div style="font-size:12px;color:#667085">Bitrix on-demand enrichment</div></div>' +
      '<button id="bitrix-profile-close" style="border:1px solid #d1d8dd;background:#fff;border-radius:6px;padding:6px 10px;cursor:pointer">Close</button>' +
      "</div>" +
      section(
        "HD Customer",
        field("Name", customer.customer_name || customer.name) +
          field("Domain", customer.domain) +
          field("Haravan Org ID", customer.haravan_orgid) +
          field("MyHaravan", customer.myharavan)
      ) +
      section(
        "Contact",
        field("Name", contact.name) +
          field("Email", contact.email_id) +
          field("Phone", contact.mobile_no || contact.phone)
      ) +
      section(
        "Bitrix Company",
        field("Status", bitrix.status) +
          field("Company ID", company.id || customer.bitrix_company_id) +
          field("Company", company.title) +
          field("URL", company.url || customer.bitrix_company_url) +
          field("Responsible", responsible.email || responsible.name) +
          field("Responsible Status", responsible.status)
      ) +
      section(
        "Bitrix Contact",
        field("Contact ID", bitrixContact.id || contact.bitrix_contact_id) +
          field("Contact", bitrixContact.title) +
          field("URL", bitrixContact.url || contact.bitrix_contact_url)
      ) +
      section(
        "Haravan Links",
        haravanLinks
          .map(function (link) {
            return field(link.haravan_orgid || "Org", link.email || link.user);
          })
          .join("")
      );

    var close = document.getElementById("bitrix-profile-close");
    if (close) close.addEventListener("click", closePanel);
  }

  function openProfile(refresh) {
    if (!isTicketRoute() || typeof frappe === "undefined" || !frappe.call) return;
    var panel = ensurePanel();
    panel.style.display = "block";
    panel.innerHTML = '<div style="padding:18px;color:#667085">Loading customer profile...</div>';

    frappe.call({
      method: METHOD,
      args: { ticket: ticketNameFromPath(), refresh: refresh ? 1 : 0 },
      callback: function (r) {
        render(panel, r.message || {});
      },
      error: function () {
        panel.innerHTML =
          '<div style="padding:18px;color:#b42318">Could not load customer profile.</div>';
      },
    });
  }

  function installWindowOpenInterceptor() {
    if (window.__bitrixCustomerProfileOpenPatched) return;
    window.__bitrixCustomerProfileOpenPatched = true;
    var originalOpen = window.open;
    window.open = function (url, target, features) {
      if (isTicketRoute() && typeof url === "string" && url.indexOf("/app/contact/") !== -1) {
        openProfile(false);
        return null;
      }
      return originalOpen.call(window, url, target, features);
    };
  }

  function init() {
    installWindowOpenInterceptor();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
