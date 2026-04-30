(function () {
  var COOKIE_NAME = "haravan_login_redirect_to";
  var PROVIDER_CLASS = "btn-haravan_account";
  var CALLBACK_PATH = "/api/method/login_with_haravan.oauth.login_via_haravan";

  function sameOriginUrl(value) {
    try {
      var url = new URL(value, window.location.origin);
      return url.origin === window.location.origin ? url : null;
    } catch (e) {
      return null;
    }
  }

  function getRedirectTarget() {
    var params = new URLSearchParams(window.location.search);
    var redirectTo = params.get("redirect-to");
    var url = redirectTo ? sameOriginUrl(redirectTo) : null;
    if (url && url.pathname !== "/login") {
      return url.pathname + url.search + url.hash;
    }

    url = document.referrer ? sameOriginUrl(document.referrer) : null;
    if (url && url.pathname.indexOf("/helpdesk") === 0) {
      return url.pathname + url.search + url.hash;
    }

    return null;
  }

  function setRedirectCookie(target) {
    var cookie = COOKIE_NAME + "=" + encodeURIComponent(target) + "; Max-Age=600; Path=/; SameSite=Lax";
    if (window.location.protocol === "https:") {
      cookie += "; Secure";
    }
    document.cookie = cookie;
  }

  function shouldRewriteRedirectUri(redirectUri) {
    if (!redirectUri) {
      return false;
    }

    try {
      var redirectUrl = new URL(redirectUri, window.location.origin);
      if (redirectUrl.origin === window.location.origin && redirectUrl.pathname === CALLBACK_PATH) {
        return false;
      }

      var currentHost = window.location.hostname;
      var currentIsFrappeCloud = currentHost.indexOf("frappe.cloud") !== -1;
      var redirectIsFrappeCloud = redirectUrl.hostname.indexOf("frappe.cloud") !== -1;

      return !currentIsFrappeCloud && (redirectIsFrappeCloud || redirectUrl.origin !== window.location.origin);
    } catch (e) {
      return false;
    }
  }

  function rewriteHaravanLink(target) {
    var link = document.querySelector("a." + PROVIDER_CLASS);
    if (!link) {
      return;
    }

    try {
      var changed = false;
      var authUrl = new URL(link.href);
      if (target) {
        var state = JSON.parse(window.atob(authUrl.searchParams.get("state")));
        state.redirect_to = new URL(target, window.location.origin).href;
        authUrl.searchParams.set("state", window.btoa(JSON.stringify(state)));
        changed = true;
      }

      if (shouldRewriteRedirectUri(authUrl.searchParams.get("redirect_uri"))) {
        authUrl.searchParams.set("redirect_uri", new URL(CALLBACK_PATH, window.location.origin).href);
        changed = true;
      }

      if (changed) {
        link.href = authUrl.toString();
      }
    } catch (e) {
      // The callback cookie still preserves the redirect if the link cannot be rewritten.
    }
  }

  function init() {
    if (window.location.pathname !== "/login") {
      return;
    }

    var target = getRedirectTarget();
    if (target) {
      setRedirectCookie(target);
    }

    rewriteHaravanLink(target);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
