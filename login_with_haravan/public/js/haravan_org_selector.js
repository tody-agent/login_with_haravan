/**
 * Haravan Org Selector — Injects an organization picker into the
 * Helpdesk portal ticket creation form when the user is linked to
 * multiple Haravan organizations (HD Customers).
 *
 * Pattern inspired by frappedesk.com's "Site Name" dropdown.
 *
 * This script runs on every page load but only activates on the
 * helpdesk ticket creation page (/helpdesk/my-tickets/new).
 *
 * Architecture:
 *   1. Fetches user's linked orgs via whitelisted API
 *   2. Injects a dropdown selector into the ticket form DOM
 *   3. Intercepts XMLHttpRequest to inject the selected customer
 *      into HD Ticket creation payloads (frappe.client.insert)
 */
(function () {
  "use strict";

  var SELECTOR_ID = "haravan-org-selector";
  var STATUS_ID = "haravan-org-status";
  var API_METHOD = "login_with_haravan.oauth.get_user_haravan_orgs";
  var POLL_INTERVAL = 500;
  var MAX_POLLS = 40;

  /* ── Activation guard ───────────────────────────────────── */

  function shouldActivate() {
    var path = window.location.pathname;
    return (
      path.indexOf("/helpdesk/my-tickets/new") !== -1 ||
      path.indexOf("/helpdesk/tickets/new") !== -1
    );
  }

  /* ── API call ───────────────────────────────────────────── */

  function fetchOrgs(callback) {
    if (typeof frappe === "undefined" || !frappe.call) {
      return callback([]);
    }
    frappe.call({
      method: API_METHOD,
      async: true,
      callback: function (r) {
        if (r && r.message && Array.isArray(r.message)) {
          callback(r.message);
        } else {
          callback([]);
        }
      },
      error: function () {
        callback([]);
      },
    });
  }

  /* ── XHR interceptor ────────────────────────────────────── */
  // The Helpdesk Vue SPA creates tickets via frappe.call which uses
  // XMLHttpRequest under the hood. We intercept send() to inject the
  // selected customer into the doc payload for frappe.client.insert.

  var _xhrInterceptInstalled = false;

  function installXhrInterceptor() {
    if (_xhrInterceptInstalled) return;
    _xhrInterceptInstalled = true;

    var origOpen = XMLHttpRequest.prototype.open;
    var origSend = XMLHttpRequest.prototype.send;

    XMLHttpRequest.prototype.open = function (method, url) {
      this._hrvUrl = url;
      this._hrvMethod = method;
      return origOpen.apply(this, arguments);
    };

    XMLHttpRequest.prototype.send = function (body) {
      var customer = window.__haravan_selected_customer;
      if (
        customer &&
        this._hrvMethod === "POST" &&
        typeof this._hrvUrl === "string" &&
        typeof body === "string"
      ) {
        try {
          // frappe.call sends form-encoded OR JSON
          // Check if this is a frappe.client.insert for HD Ticket
          var isInsert =
            this._hrvUrl.indexOf("frappe.client.insert") !== -1 ||
            body.indexOf("frappe.client.insert") !== -1;

          if (isInsert && body.indexOf("HD Ticket") !== -1) {
            // Try to parse as form-encoded (frappe.call default)
            if (body.indexOf("doc=") !== -1) {
              var parts = body.split("&");
              var newParts = [];
              var docReplaced = false;

              parts.forEach(function (part) {
                if (part.indexOf("doc=") === 0 && !docReplaced) {
                  var encoded = part.substring(4);
                  var decoded = decodeURIComponent(encoded);
                  var docObj = JSON.parse(decoded);
                  if (docObj.doctype === "HD Ticket" && !docObj.customer) {
                    docObj.customer = customer;
                  }
                  newParts.push("doc=" + encodeURIComponent(JSON.stringify(docObj)));
                  docReplaced = true;
                } else {
                  newParts.push(part);
                }
              });

              if (docReplaced) {
                body = newParts.join("&");
              }
            }
            // Try JSON body
            else {
              var jsonBody = JSON.parse(body);
              if (jsonBody.doc && jsonBody.doc.doctype === "HD Ticket" && !jsonBody.doc.customer) {
                jsonBody.doc.customer = customer;
                body = JSON.stringify(jsonBody);
              }
            }
          }
        } catch (e) {
          // Parsing failed — send original body, don't block the request
        }
      }
      return origSend.call(this, body);
    };
  }

  function getOrgLabel(org) {
    if (!org) return "";
    return org.customer || (org.orgname + " - " + org.orgid);
  }

  function showSelectedCustomer(wrapper, org) {
    var status = wrapper.querySelector("#" + STATUS_ID);
    if (!status) {
      status = document.createElement("div");
      status.id = STATUS_ID;
      wrapper.appendChild(status);
    }

    var label = getOrgLabel(org);
    var orgid = org && org.orgid ? "OrgID: " + org.orgid : "";
    status.textContent = label ? label + (orgid ? " | " + orgid : "") : "";
    status.style.cssText =
      "margin-top: 8px; font-size: 13px; color: var(--text-muted, #6b7280);";
  }

  /* ── DOM injection ──────────────────────────────────────── */

  function injectSelector(orgs) {
    if (orgs.length === 0) return;

    // Don't inject twice
    if (document.getElementById(SELECTOR_ID)) return;

    // Install XHR interceptor so the selected/visible customer is sent with the ticket.
    installXhrInterceptor();

    var pollCount = 0;

    function tryInject() {
      pollCount++;
      if (pollCount > MAX_POLLS) return;

      // Look for the ticket form container in the Vue SPA
      var formContainer =
        document.querySelector("form") ||
        document.querySelector("[class*='new-ticket']") ||
        document.querySelector("[class*='ticket-form']") ||
        document.querySelector(".layout-main-section") ||
        document.querySelector("main");

      if (!formContainer) {
        setTimeout(tryInject, POLL_INTERVAL);
        return;
      }

      // Create the customer context container
      var wrapper = document.createElement("div");
      wrapper.id = SELECTOR_ID;
      wrapper.style.cssText =
        "margin-bottom: 16px; padding: 12px 16px; " +
        "background: var(--subtle-accent, #f4f5f6); " +
        "border-radius: 8px; border: 1px solid var(--border-color, #d1d8dd);";

      var label = document.createElement("label");
      label.textContent = "HD Customer nhận ticket";
      label.style.cssText =
        "display: block; font-weight: 600; font-size: 13px; " +
        "margin-bottom: 6px; color: var(--text-color, #333);";
      label.setAttribute("for", SELECTOR_ID + "-select");

      wrapper.appendChild(label);

      if (orgs.length === 1) {
        window.__haravan_selected_customer = orgs[0].customer;
        showSelectedCustomer(wrapper, orgs[0]);
        formContainer.insertBefore(wrapper, formContainer.firstChild);
        return;
      }

      var select = document.createElement("select");
      select.id = SELECTOR_ID + "-select";
      select.name = "haravan_customer";
      select.style.cssText =
        "width: 100%; padding: 8px 12px; font-size: 14px; " +
        "border: 1px solid var(--border-color, #d1d8dd); " +
        "border-radius: 6px; background: var(--control-bg, #fff); " +
        "color: var(--text-color, #333); cursor: pointer; " +
        "appearance: auto;";

      // Placeholder option
      var placeholder = document.createElement("option");
      placeholder.value = "";
      placeholder.textContent = "\u2014 Ch\u1ECDn HD Customer \u2014";
      placeholder.disabled = true;
      placeholder.selected = true;
      select.appendChild(placeholder);

      // Add org options — display as "[OrgName] - [OrgID]" (matches HD Customer name)
      orgs.forEach(function (org) {
        var opt = document.createElement("option");
        opt.value = org.customer;
        opt.textContent = org.customer || (org.orgname + " - " + org.orgid);
        opt.setAttribute("data-orgid", org.orgid || "");
        opt._haravanOrg = org;
        select.appendChild(opt);
      });

      // On selection change
      select.addEventListener("change", function () {
        window.__haravan_selected_customer = this.value;
        showSelectedCustomer(wrapper, this.options[this.selectedIndex]._haravanOrg);
      });

      wrapper.appendChild(select);
      select.selectedIndex = 1;
      window.__haravan_selected_customer = orgs[0].customer;
      showSelectedCustomer(wrapper, orgs[0]);

      // Insert at the top of the form
      formContainer.insertBefore(wrapper, formContainer.firstChild);
    }

    tryInject();
  }

  /* ── Initialization ─────────────────────────────────────── */

  function init() {
    if (!shouldActivate()) return;

    // Reset selection on navigation
    window.__haravan_selected_customer = null;

    if (typeof frappe !== "undefined" && frappe.ready) {
      frappe.ready(function () {
        fetchOrgs(injectSelector);
      });
    } else {
      // Poll for frappe availability
      var checkCount = 0;
      var checkInterval = setInterval(function () {
        checkCount++;
        if (checkCount > 30) {
          clearInterval(checkInterval);
          return;
        }
        if (typeof frappe !== "undefined" && frappe.call) {
          clearInterval(checkInterval);
          fetchOrgs(injectSelector);
        }
      }, 500);
    }
  }

  // Run on initial load
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // Re-run on SPA navigation (Helpdesk is a Vue SPA)
  var lastPath = window.location.pathname;
  setInterval(function () {
    var currentPath = window.location.pathname;
    if (currentPath !== lastPath) {
      lastPath = currentPath;
      var old = document.getElementById(SELECTOR_ID);
      if (old) old.remove();
      init();
    }
  }, 1000);
})();
