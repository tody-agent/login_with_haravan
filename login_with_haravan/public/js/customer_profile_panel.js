/**
 * Customer Profile Panel
 *
 * Opens an in-ticket customer profile modal instead of sending agents to the
 * raw Contact desk record. The first request is local-only so the modal appears
 * immediately; slow Bitrix enrichment is only requested when needed.
 */
(function () {
  "use strict";

  var PANEL_ID = "bitrix-customer-profile-panel";
  var STYLE_ID = "bitrix-customer-profile-style";
  var PROFILE_METHOD = "login_with_haravan.customer_profile.get_ticket_customer_profile";
  var BITRIX_METHOD = "login_with_haravan.customer_profile.get_ticket_bitrix_profile";

  var state = {
    activeTab: "profile",
    loadingProfile: false,
    loadingBitrix: false,
    profilePayload: null,
    bitrixPayload: null,
    profileError: "",
    bitrixError: "",
  };

  function isTicketRoute() {
    return window.location.pathname.indexOf("/helpdesk/tickets/") !== -1;
  }

  function ticketNameFromPath() {
    var parts = window.location.pathname.split("/").filter(Boolean);
    return parts[parts.length - 1] || "";
  }

  function ensureStyles() {
    if (document.getElementById(STYLE_ID)) return;
    var style = document.createElement("style");
    style.id = STYLE_ID;
    style.textContent = [
      "#" + PANEL_ID + "{position:fixed;inset:0;z-index:1050;display:none;background:rgba(17,24,39,.38);font-family:Inter,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#111827}",
      "#" + PANEL_ID + ".is-open{display:flex;align-items:center;justify-content:center;padding:28px}",
      "#" + PANEL_ID + " .hcp-modal{width:min(760px,calc(100vw - 32px));max-height:min(860px,calc(100vh - 48px));background:#fff;border:1px solid #d1d5db;border-radius:18px;box-shadow:0 18px 42px rgba(15,23,42,.22);display:flex;flex-direction:column;overflow:hidden}",
      "#" + PANEL_ID + " .hcp-head{padding:26px 32px 14px;display:flex;align-items:flex-start;justify-content:space-between;gap:16px}",
      "#" + PANEL_ID + " .hcp-title{font-size:28px;line-height:1.15;font-weight:750;letter-spacing:0;margin:0}",
      "#" + PANEL_ID + " .hcp-subtitle{font-size:13px;color:#667085;margin-top:6px}",
      "#" + PANEL_ID + " .hcp-close{width:34px;height:34px;border:0;background:#fff;border-radius:8px;cursor:pointer;font-size:30px;line-height:30px;color:#111827}",
      "#" + PANEL_ID + " .hcp-tabs{display:flex;gap:22px;margin:0 32px;border-bottom:1px solid #d9dee7;min-height:48px}",
      "#" + PANEL_ID + " .hcp-tab{appearance:none;border:0;background:transparent;color:#98a2b3;font-size:16px;font-weight:700;padding:13px 0 12px;min-width:92px;border-bottom:3px solid transparent;cursor:pointer}",
      "#" + PANEL_ID + " .hcp-tab.is-active{color:#111827;border-bottom-color:#111827}",
      "#" + PANEL_ID + " .hcp-body{padding:20px 32px 32px;overflow:auto}",
      "#" + PANEL_ID + " .hcp-toolbar{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:16px}",
      "#" + PANEL_ID + " .hcp-heading{min-width:0}",
      "#" + PANEL_ID + " .hcp-name{font-size:21px;line-height:1.2;font-weight:800;word-break:break-word}",
      "#" + PANEL_ID + " .hcp-meta{margin-top:4px;color:#667085;font-size:13px;word-break:break-word}",
      "#" + PANEL_ID + " .hcp-actions{display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end}",
      "#" + PANEL_ID + " .hcp-btn{border:1px solid #cfd6df;background:#fff;color:#344054;border-radius:8px;min-height:34px;padding:6px 10px;font-size:13px;font-weight:700;cursor:pointer}",
      "#" + PANEL_ID + " .hcp-btn.primary{background:#111827;border-color:#111827;color:#fff}",
      "#" + PANEL_ID + " .hcp-btn:disabled{opacity:.55;cursor:not-allowed}",
      "#" + PANEL_ID + " .hcp-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin-bottom:18px}",
      "#" + PANEL_ID + " .hcp-stat{border:1px solid #d9dee7;border-radius:8px;padding:12px 14px;min-height:78px}",
      "#" + PANEL_ID + " .hcp-label{display:block;color:#667085;font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.04em;margin-bottom:8px}",
      "#" + PANEL_ID + " .hcp-value{font-size:16px;font-weight:800;color:#111827;word-break:break-word}",
      "#" + PANEL_ID + " .hcp-section{margin-top:18px}",
      "#" + PANEL_ID + " .hcp-section-title{font-size:15px;font-weight:800;margin:0 0 8px}",
      "#" + PANEL_ID + " .hcp-table{border:1px solid #d9dee7;border-radius:8px;padding:10px 14px}",
      "#" + PANEL_ID + " .hcp-row{display:flex;justify-content:space-between;gap:16px;padding:9px 0;border-bottom:1px solid #eef1f5}",
      "#" + PANEL_ID + " .hcp-row:last-child{border-bottom:0}",
      "#" + PANEL_ID + " .hcp-key{color:#667085;min-width:140px}",
      "#" + PANEL_ID + " .hcp-row strong{text-align:right;word-break:break-word}",
      "#" + PANEL_ID + " .hcp-pill{display:inline-flex;align-items:center;min-height:24px;border-radius:999px;padding:2px 10px;background:#eef4ff;color:#175cd3;font-size:13px;font-weight:800}",
      "#" + PANEL_ID + " .hcp-pill.ok{background:#dcfae6;color:#067647}",
      "#" + PANEL_ID + " .hcp-pill.warn{background:#fffaeb;color:#b54708}",
      "#" + PANEL_ID + " .hcp-pill.bad{background:#fef3f2;color:#b42318}",
      "#" + PANEL_ID + " .hcp-empty{border:1px dashed #d0d5dd;border-radius:8px;padding:22px;text-align:center;color:#667085}",
      "#" + PANEL_ID + " .hcp-loading{border:1px solid #d9dee7;border-radius:8px;padding:26px;text-align:center;color:#667085}",
      "#" + PANEL_ID + " .hcp-spinner{width:28px;height:28px;border:3px solid #e5e7eb;border-top-color:#111827;border-radius:50%;margin:0 auto 12px;animation:hcp-spin .8s linear infinite}",
      "@keyframes hcp-spin{to{transform:rotate(360deg)}}",
      "@media(max-width:640px){#" + PANEL_ID + ".is-open{padding:12px}#" + PANEL_ID + " .hcp-modal{width:100%;max-height:calc(100vh - 24px);border-radius:14px}#" + PANEL_ID + " .hcp-head{padding:20px 18px 10px}#" + PANEL_ID + " .hcp-title{font-size:24px}#" + PANEL_ID + " .hcp-tabs{margin:0 18px;gap:18px;overflow:auto}#" + PANEL_ID + " .hcp-tab{min-width:auto;font-size:15px}#" + PANEL_ID + " .hcp-body{padding:18px}#" + PANEL_ID + " .hcp-toolbar{align-items:flex-start;flex-direction:column}#" + PANEL_ID + " .hcp-grid{grid-template-columns:1fr}#" + PANEL_ID + " .hcp-row{flex-direction:column;gap:4px}#" + PANEL_ID + " .hcp-row strong{text-align:left}}",
    ].join("");
    document.head.appendChild(style);
  }

  function ensurePanel() {
    ensureStyles();
    var existing = document.getElementById(PANEL_ID);
    if (existing) return existing;

    var panel = document.createElement("aside");
    panel.id = PANEL_ID;
    panel.setAttribute("role", "dialog");
    panel.setAttribute("aria-modal", "true");
    document.body.appendChild(panel);
    return panel;
  }

  function closePanel() {
    var panel = document.getElementById(PANEL_ID);
    if (panel) panel.classList.remove("is-open");
  }

  function escapeHtml(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function dataOf(payload) {
    return (payload && payload.data) || {};
  }

  function row(label, value, asHtml) {
    if (value == null || value === "") return "";
    return (
      '<div class="hcp-row"><span class="hcp-key">' +
      escapeHtml(label) +
      "</span><strong>" +
      (asHtml ? value : escapeHtml(value)) +
      "</strong></div>"
    );
  }

  function stat(label, value, asHtml) {
    if (value == null || value === "") return "";
    return (
      '<div class="hcp-stat"><span class="hcp-label">' +
      escapeHtml(label) +
      '</span><div class="hcp-value">' +
      (asHtml ? value : escapeHtml(value)) +
      "</div></div>"
    );
  }

  function section(title, body) {
    if (!body) return "";
    return (
      '<section class="hcp-section"><h3 class="hcp-section-title">' +
      escapeHtml(title) +
      '</h3><div class="hcp-table">' +
      body +
      "</div></section>"
    );
  }

  function statusPill(status) {
    var normalized = String(status || "local").toLowerCase();
    var tone = "warn";
    if (["matched", "cached", "local", "complete"].indexOf(normalized) !== -1) tone = "ok";
    if (["error", "missing_config", "disabled", "not_found", "missing_lookup"].indexOf(normalized) !== -1) tone = "bad";
    return '<span class="hcp-pill ' + tone + '">' + escapeHtml(status || "local") + "</span>";
  }

  function renderLoading(label) {
    return (
      '<div class="hcp-loading"><div class="hcp-spinner"></div><div>' +
      escapeHtml(label) +
      "</div></div>"
    );
  }

  function renderProfileTab() {
    if (state.loadingProfile) return renderLoading("Dang tai ho so khach hang...");
    if (state.profileError) return '<div class="hcp-empty">' + escapeHtml(state.profileError) + "</div>";

    var data = dataOf(state.profilePayload);
    var customer = data.customer || {};
    var contact = data.contact || {};
    var bitrix = data.bitrix || {};
    var haravanLinks = data.haravan || [];

    if (!customer.name && !customer.customer_name) {
      return (
        '<div class="hcp-empty">' +
        "Ticket chua co HD Customer. Dang kiem tra Bitrix o tab Bitrix." +
        "</div>"
      );
    }

    var profileRows =
      row("Company", customer.customer_name || customer.name) +
      row("Company ID", customer.haravan_orgid) +
      row("MyHaravan", customer.myharavan) +
      row("Domain", customer.domain) +
      row("Bitrix", customer.bitrix_company_url ? '<button class="hcp-btn" data-action="open-bitrix">Mo Bitrix</button>' : customer.bitrix_company_id, true);

    var contactRows =
      row("Name", contact.name) +
      row("Email", contact.email_id) +
      row("Phone", contact.mobile_no || contact.phone);

    var linkRows = haravanLinks
      .map(function (link) {
        return row(link.haravan_orgid || "Org", link.email || link.user || link.haravan_orgname);
      })
      .join("");

    return (
      '<div class="hcp-toolbar"><div class="hcp-heading"><div class="hcp-name">' +
      escapeHtml(customer.customer_name || customer.name) +
      '</div><div class="hcp-meta">' +
      escapeHtml(["Company ID " + (customer.haravan_orgid || "-"), "Bitrix " + (customer.bitrix_company_id || "-")].join(" / ")) +
      '</div></div><div class="hcp-actions">' +
      (customer.bitrix_company_url ? '<button class="hcp-btn" data-action="open-bitrix">Mo Bitrix</button>' : "") +
      '<button class="hcp-btn primary" data-action="refresh-bitrix">Lam moi Bitrix</button>' +
      "</div></div>" +
      '<div class="hcp-grid">' +
      stat("Status", statusPill(bitrix.status || customer.bitrix_sync_status || "local"), true) +
      stat("Segment", customer.customer_segment || "-") +
      stat("Company ID", customer.haravan_orgid) +
      stat("Bitrix ID", customer.bitrix_company_id) +
      "</div>" +
      section("Khach hang", profileRows) +
      section("Contact", contactRows) +
      section("Haravan Links", linkRows)
    );
  }

  function renderBitrixTab() {
    if (state.loadingBitrix) return renderLoading("Dang doi du lieu Bitrix...");
    if (state.bitrixError) return '<div class="hcp-empty">' + escapeHtml(state.bitrixError) + "</div>";

    var source = state.bitrixPayload || state.profilePayload;
    var data = dataOf(source);
    var customer = data.customer || {};
    var contact = data.contact || {};
    var ticket = data.ticket || {};
    var bitrix = data.bitrix || {};
    var company = bitrix.company || {};
    var bitrixContact = bitrix.contact || {};
    var responsible = bitrix.responsible || {};

    if (!source) return '<div class="hcp-empty">Chua co du lieu Bitrix.</div>';

    var companyRows =
      row("Status", statusPill(bitrix.status), true) +
      row("Company ID", company.id || customer.bitrix_company_id) +
      row("Company", company.title) +
      row("URL", company.url || customer.bitrix_company_url) +
      row("Responsible", responsible.email || responsible.name) +
      row("Responsible Status", responsible.status);

    var contactRows =
      row("Contact ID", bitrixContact.id || contact.bitrix_contact_id) +
      row("Contact", bitrixContact.title || contact.name) +
      row("URL", bitrixContact.url || contact.bitrix_contact_url);

    return (
      '<div class="hcp-toolbar"><div class="hcp-heading"><div class="hcp-name">' +
      escapeHtml(company.title || customer.customer_name || customer.name || "Bitrix") +
      '</div><div class="hcp-meta">' +
      escapeHtml(["Ticket " + (ticket.name || ticketNameFromPath()), "OrgID " + (ticket.orgid || customer.haravan_orgid || "-")].join(" / ")) +
      '</div></div><div class="hcp-actions">' +
      (company.url || customer.bitrix_company_url ? '<button class="hcp-btn" data-action="open-bitrix">Mo Bitrix</button>' : "") +
      '<button class="hcp-btn primary" data-action="refresh-bitrix">Lam moi</button>' +
      "</div></div>" +
      '<div class="hcp-grid">' +
      stat("Status", statusPill(bitrix.status), true) +
      stat("Company", company.title || customer.customer_name) +
      stat("Bitrix ID", company.id || customer.bitrix_company_id) +
      stat("Responsible", responsible.email || responsible.name) +
      "</div>" +
      section("Bitrix Company", companyRows) +
      section("Bitrix Contact", contactRows)
    );
  }

  function render(panel) {
    var profileData = dataOf(state.profilePayload);
    var hasCustomer = !!(profileData.customer && (profileData.customer.name || profileData.customer.customer_name));
    var bitrixLabel = hasCustomer ? "Bitrix" : "Bitrix";

    panel.innerHTML =
      '<div class="hcp-modal">' +
      '<div class="hcp-head"><div><h2 class="hcp-title">Customer Profile</h2><div class="hcp-subtitle">' +
      (hasCustomer ? "HD Customer da co san, khong doi Bitrix." : "Chua co HD Customer, dang lam giau tu Bitrix.") +
      '</div></div><button class="hcp-close" data-action="close" aria-label="Close">&times;</button></div>' +
      '<div class="hcp-tabs">' +
      '<button class="hcp-tab ' +
      (state.activeTab === "profile" ? "is-active" : "") +
      '" data-tab="profile">Profile</button>' +
      '<button class="hcp-tab ' +
      (state.activeTab === "bitrix" ? "is-active" : "") +
      '" data-tab="bitrix">' +
      bitrixLabel +
      "</button>" +
      "</div>" +
      '<div class="hcp-body">' +
      (state.activeTab === "bitrix" ? renderBitrixTab() : renderProfileTab()) +
      "</div></div>";

    bindPanelEvents(panel);
  }

  function notify(message, indicator) {
    if (typeof frappe !== "undefined" && frappe.show_alert) {
      frappe.show_alert({ message: message, indicator: indicator || "blue" });
    }
  }

  function currentBitrixUrl() {
    var bitrixData = dataOf(state.bitrixPayload || state.profilePayload).bitrix || {};
    var profileData = dataOf(state.profilePayload);
    return (
      (bitrixData.company && bitrixData.company.url) ||
      (profileData.customer && profileData.customer.bitrix_company_url) ||
      ""
    );
  }

  function bindPanelEvents(panel) {
    panel.querySelectorAll("[data-tab]").forEach(function (button) {
      button.addEventListener("click", function () {
        state.activeTab = button.getAttribute("data-tab") || "profile";
        render(panel);
      });
    });

    panel.querySelectorAll("[data-action]").forEach(function (button) {
      button.addEventListener("click", function () {
        var action = button.getAttribute("data-action");
        if (action === "close") closePanel();
        if (action === "refresh-bitrix") loadBitrix(panel, true);
        if (action === "open-bitrix") {
          var url = currentBitrixUrl();
          if (url) window.open(url, "_blank", "noopener");
        }
      });
    });
  }

  function loadProfile(panel) {
    state.loadingProfile = true;
    state.profilePayload = null;
    state.profileError = "";
    state.bitrixPayload = null;
    state.bitrixError = "";
    render(panel);

    frappe.call({
      method: PROFILE_METHOD,
      args: { ticket: ticketNameFromPath(), refresh: 0 },
      callback: function (r) {
        state.loadingProfile = false;
        state.profilePayload = r.message || {};
        var data = dataOf(state.profilePayload);
        var hasCustomer = !!(data.customer && (data.customer.name || data.customer.customer_name));
        state.activeTab = hasCustomer ? "profile" : "bitrix";
        render(panel);
        if (!hasCustomer) loadBitrix(panel, false);
      },
      error: function () {
        state.loadingProfile = false;
        state.profileError = "Khong tai duoc ho so khach hang.";
        render(panel);
      },
    });
  }

  function loadBitrix(panel, manual) {
    if (state.loadingBitrix) return;
    state.activeTab = "bitrix";
    state.loadingBitrix = true;
    state.bitrixError = "";
    render(panel);

    frappe.call({
      method: BITRIX_METHOD,
      args: { ticket: ticketNameFromPath(), refresh: 1 },
      callback: function (r) {
        state.loadingBitrix = false;
        state.bitrixPayload = r.message || {};
        render(panel);
        if (manual) notify("Da tai lai du lieu Bitrix.", "green");
      },
      error: function () {
        state.loadingBitrix = false;
        state.bitrixError = "Bitrix phan hoi cham hoac bi loi. Vui long thu lai.";
        render(panel);
      },
    });
  }

  function openProfile() {
    if (!isTicketRoute() || typeof frappe === "undefined" || !frappe.call) return;
    var panel = ensurePanel();
    panel.classList.add("is-open");
    state.activeTab = "profile";
    loadProfile(panel);
  }

  function installWindowOpenInterceptor() {
    if (window.__bitrixCustomerProfileOpenPatched) return;
    window.__bitrixCustomerProfileOpenPatched = true;
    var originalOpen = window.open;
    window.open = function (url, target, features) {
      if (isTicketRoute() && typeof url === "string" && url.indexOf("/app/contact/") !== -1) {
        openProfile();
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
