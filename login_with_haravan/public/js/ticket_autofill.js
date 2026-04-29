/**
 * Helpdesk ticket autofill.
 *
 * Agents enter only Link Web / MyHaravan and Product Suggestion. Derived
 * fields are hidden in the create-ticket UI and filled by backend APIs/hooks.
 */
(function () {
  "use strict";

  var META_METHOD = "login_with_haravan.ticket_context.get_create_ticket_metadata";
  var RESOLVE_METHOD = "login_with_haravan.ticket_context.resolve_create_ticket_context";
  var POLL_INTERVAL = 500;
  var MAX_POLLS = 40;

  var state = {
    initialized: false,
    fieldMap: {},
    hiddenLabels: ["Customer", "Org ID", "MyHaravan Domain", "Product Line", "Product Feature"],
    values: {},
    lastLink: "",
    lastProduct: "",
    resolveTimer: null,
  };

  function shouldActivate() {
    var path = window.location.pathname;
    return (
      path.indexOf("/helpdesk/tickets/new") !== -1 ||
      path.indexOf("/helpdesk/my-tickets/new") !== -1
    );
  }

  function responseData(response) {
    var message = response && response.message;
    if (message && message.data) return message.data;
    return message || {};
  }

  function fetchMetadata(callback) {
    if (typeof frappe === "undefined" || !frappe.call) {
      callback({});
      return;
    }
    frappe.call({
      method: META_METHOD,
      callback: function (response) {
        callback(responseData(response));
      },
      error: function () {
        callback({});
      },
    });
  }

  function resolveContext(linkValue, productValue) {
    if (typeof frappe === "undefined" || !frappe.call) return;

    frappe.call({
      method: RESOLVE_METHOD,
      args: {
        link_web_myharavan: linkValue || "",
        product_suggestion: productValue || "",
      },
      callback: function (response) {
        var data = responseData(response);
        state.fieldMap = data.field_map || state.fieldMap;
        state.values = data.values || {};
        window.__haravan_ticket_autofill_values = state.values;
      },
      error: function () {},
    });
  }

  function normalizeText(value) {
    return String(value || "")
      .replace(/\s+/g, " ")
      .replace(/\s+\*/g, "")
      .trim();
  }

  function labelMatches(node, label) {
    return normalizeText(node.textContent) === label;
  }

  function findFieldWrapper(label) {
    var candidates = document.querySelectorAll("label, div, span, p");
    for (var i = 0; i !== candidates.length; i++) {
      if (!labelMatches(candidates[i], label)) continue;

      var current = candidates[i];
      for (var depth = 0; current && depth < 7; depth++) {
        if (
          current !== document.body &&
          current.querySelector &&
          current.querySelector("input, textarea, select, button, [role='combobox']")
        ) {
          return current;
        }
        current = current.parentElement;
      }
    }
    return null;
  }

  function hideDerivedFields() {
    if (!shouldActivate()) return;
    state.hiddenLabels.forEach(function (label) {
      var wrapper = findFieldWrapper(label);
      if (wrapper) {
        wrapper.style.display = "none";
        wrapper.setAttribute("data-haravan-hidden", "1");
      }
    });
  }

  function readFieldValue(label) {
    var wrapper = findFieldWrapper(label);
    if (!wrapper) return "";

    var input = wrapper.querySelector("input, textarea, select");
    if (input) {
      if (input.tagName === "SELECT") {
        return input.options[input.selectedIndex] ? input.options[input.selectedIndex].text : "";
      }
      return input.value || "";
    }

    var combobox = wrapper.querySelector("[role='combobox'], button");
    if (combobox) {
      var text = normalizeText(combobox.textContent);
      if (text && text !== "Select an option" && text !== "Type something") return text;
    }

    return "";
  }

  function scheduleResolve() {
    if (!shouldActivate()) return;
    clearTimeout(state.resolveTimer);
    state.resolveTimer = setTimeout(function () {
      var linkValue = readFieldValue("Link Web / MyHaravan");
      var productValue = readFieldValue("Product Suggestion");
      if (linkValue === state.lastLink && productValue === state.lastProduct) return;
      state.lastLink = linkValue;
      state.lastProduct = productValue;
      resolveContext(linkValue, productValue);
    }, 250);
  }

  function ensureDocValues(doc) {
    if (!doc || doc.doctype !== "HD Ticket") return doc;

    var fieldMap = state.fieldMap || {};
    var values = window.__haravan_ticket_autofill_values || state.values || {};
    Object.keys(values).forEach(function (fieldname) {
      if (values[fieldname] !== undefined && values[fieldname] !== null && values[fieldname] !== "") {
        doc[fieldname] = values[fieldname];
      }
    });

    var linkField = fieldMap.link_web_myharavan || "custom_link_web_myharavan";
    var productField = fieldMap.product_suggestion || "custom_product_suggestion";
    if (!doc[linkField]) doc[linkField] = readFieldValue("Link Web / MyHaravan");
    if (!doc[productField]) doc[productField] = readFieldValue("Product Suggestion");

    return doc;
  }

  var xhrInstalled = false;

  function installXhrInterceptor() {
    if (xhrInstalled) return;
    xhrInstalled = true;

    var originalOpen = XMLHttpRequest.prototype.open;
    var originalSend = XMLHttpRequest.prototype.send;

    XMLHttpRequest.prototype.open = function (method, url) {
      this._hrvTicketUrl = url;
      this._hrvTicketMethod = method;
      return originalOpen.apply(this, arguments);
    };

    XMLHttpRequest.prototype.send = function (body) {
      if (
        shouldActivate() &&
        this._hrvTicketMethod === "POST" &&
        typeof this._hrvTicketUrl === "string" &&
        typeof body === "string" &&
        (this._hrvTicketUrl.indexOf("frappe.client.insert") !== -1 ||
          body.indexOf("frappe.client.insert") !== -1) &&
        body.indexOf("HD Ticket") !== -1
      ) {
        try {
          if (body.indexOf("doc=") !== -1) {
            var parts = body.split("&");
            for (var i = 0; i !== parts.length; i++) {
              if (parts[i].indexOf("doc=") !== 0) continue;
              var doc = JSON.parse(decodeURIComponent(parts[i].substring(4)));
              parts[i] = "doc=" + encodeURIComponent(JSON.stringify(ensureDocValues(doc)));
              body = parts.join("&");
              break;
            }
          } else {
            var jsonBody = JSON.parse(body);
            if (jsonBody.doc) {
              jsonBody.doc = ensureDocValues(jsonBody.doc);
              body = JSON.stringify(jsonBody);
            }
          }
        } catch (e) {
          // Keep the original request if Helpdesk changes its payload shape.
        }
      }

      return originalSend.call(this, body);
    };
  }

  function bindWatchers() {
    document.addEventListener("input", scheduleResolve, true);
    document.addEventListener("change", scheduleResolve, true);
    document.addEventListener("click", function () {
      setTimeout(scheduleResolve, 150);
    }, true);
  }

  function init() {
    if (!shouldActivate() || state.initialized) return;
    state.initialized = true;
    installXhrInterceptor();
    bindWatchers();

    fetchMetadata(function (metadata) {
      state.fieldMap = metadata.field_map || state.fieldMap;
      state.hiddenLabels = metadata.hidden_labels || state.hiddenLabels;
      hideDerivedFields();
      scheduleResolve();
    });

    var polls = 0;
    var poll = setInterval(function () {
      polls++;
      if (!shouldActivate() || polls > MAX_POLLS) {
        clearInterval(poll);
        return;
      }
      hideDerivedFields();
      scheduleResolve();
    }, POLL_INTERVAL);
  }

  function boot() {
    if (typeof frappe !== "undefined" && frappe.ready) {
      frappe.ready(init);
    } else {
      init();
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }

  var lastPath = window.location.pathname;
  setInterval(function () {
    var path = window.location.pathname;
    if (path !== lastPath) {
      lastPath = path;
      state.initialized = false;
      state.values = {};
      window.__haravan_ticket_autofill_values = {};
      boot();
    }
  }, 1000);
})();
