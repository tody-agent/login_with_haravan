/**
 * Haravan Org Selector — Injects an organization picker into the
 * Helpdesk portal ticket creation form when the user is linked to
 * multiple Haravan organizations (HD Customers).
 *
 * Pattern inspired by frappedesk.com's "Site Name" dropdown.
 *
 * This script runs on every page load but only activates on the
 * helpdesk ticket creation page (/helpdesk/my-tickets/new).
 */
(function () {
  "use strict";

  var SELECTOR_ID = "haravan-org-selector";
  var API_METHOD =
    "login_with_haravan.oauth.get_user_haravan_orgs";
  var POLL_INTERVAL = 500; // ms
  var MAX_POLLS = 40; // max 20 seconds of polling

  /**
   * Only run on helpdesk ticket creation pages.
   */
  function shouldActivate() {
    var path = window.location.pathname;
    return (
      path.indexOf("/helpdesk/my-tickets/new") !== -1 ||
      path.indexOf("/helpdesk/tickets/new") !== -1
    );
  }

  /**
   * Fetch the user's Haravan orgs via the whitelisted API.
   */
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

  /**
   * Build and inject the org selector dropdown into the ticket form.
   * Targets the Helpdesk Vue form — polls until the form container is found.
   */
  function injectSelector(orgs) {
    if (orgs.length <= 1) {
      // 0 or 1 org: no selector needed.
      // If exactly 1, auto-set will be handled by the backend hook.
      return;
    }

    // Don't inject twice
    if (document.getElementById(SELECTOR_ID)) {
      return;
    }

    var pollCount = 0;

    function tryInject() {
      pollCount++;
      if (pollCount > MAX_POLLS) return;

      // Look for the ticket form container.
      // Helpdesk uses a Vue SPA — the form might render as:
      //   - A <form> element
      //   - A div with class containing "ticket" or "new-ticket"
      //   - The main content area of the helpdesk portal
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

      // Create the selector container
      var wrapper = document.createElement("div");
      wrapper.id = SELECTOR_ID;
      wrapper.style.cssText =
        "margin-bottom: 16px; padding: 12px 16px; " +
        "background: var(--subtle-accent, #f4f5f6); " +
        "border-radius: 8px; border: 1px solid var(--border-color, #d1d8dd);";

      var label = document.createElement("label");
      label.textContent = "Tổ chức / Cửa hàng Haravan";
      label.style.cssText =
        "display: block; font-weight: 600; font-size: 13px; " +
        "margin-bottom: 6px; color: var(--text-color, #333);";
      label.setAttribute("for", SELECTOR_ID + "-select");

      var select = document.createElement("select");
      select.id = SELECTOR_ID + "-select";
      select.name = "haravan_customer";
      select.style.cssText =
        "width: 100%; padding: 8px 12px; font-size: 14px; " +
        "border: 1px solid var(--border-color, #d1d8dd); " +
        "border-radius: 6px; background: var(--control-bg, #fff); " +
        "color: var(--text-color, #333); cursor: pointer; " +
        "appearance: auto;";

      // Add placeholder option
      var placeholder = document.createElement("option");
      placeholder.value = "";
      placeholder.textContent = "— Chọn cửa hàng —";
      placeholder.disabled = true;
      placeholder.selected = true;
      select.appendChild(placeholder);

      // Add org options
      orgs.forEach(function (org) {
        var opt = document.createElement("option");
        opt.value = org.customer;
        opt.textContent = org.orgname || org.customer;
        opt.setAttribute("data-orgid", org.orgid || "");
        select.appendChild(opt);
      });

      // When user selects an org, store it for the form submission
      select.addEventListener("change", function () {
        var selectedCustomer = this.value;
        // Store in a global for the doc_events fallback to pick up
        window.__haravan_selected_customer = selectedCustomer;

        // Try to set the customer field directly if it exists in the form
        // (This works if there's a hidden "customer" field in the Frappe form)
        if (typeof cur_frm !== "undefined" && cur_frm) {
          cur_frm.set_value("customer", selectedCustomer);
        }
      });

      wrapper.appendChild(label);
      wrapper.appendChild(select);

      // Insert at the top of the form
      formContainer.insertBefore(wrapper, formContainer.firstChild);
    }

    tryInject();
  }

  /**
   * Main entry point — wait for DOM and check if we should activate.
   */
  function init() {
    if (!shouldActivate()) return;

    // Wait for frappe to be ready
    if (typeof frappe !== "undefined" && frappe.ready) {
      frappe.ready(function () {
        fetchOrgs(injectSelector);
      });
    } else {
      // Fallback: poll for frappe availability
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
      // Remove old selector
      var old = document.getElementById(SELECTOR_ID);
      if (old) old.remove();
      init();
    }
  }, 1000);
})();
