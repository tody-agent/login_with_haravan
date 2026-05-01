/**
 * Helpdesk Vietnamese UI Override
 *
 * Last-resort customer portal localization for Frappe Helpdesk strings that
 * are rendered outside Frappe's normal translation layer. Keep this file
 * isolated so it can be removed when upstream Vietnamese support is complete.
 */
(function () {
  "use strict";

  var NAMESPACE = "HaravanHelpdeskViOverride";
  var DISABLE_FLAG = "HARAVAN_HELPDESK_VI_OVERRIDE_DISABLED";
  var LOCAL_STORAGE_DISABLE_KEY = "haravan_helpdesk_vi_override_disabled";
  var OBSERVER_DEBOUNCE_MS = 80;
  var ROUTE_POLL_MS = 800;

  var TARGET_ROUTES = {
    "/helpdesk": true,
    "/helpdesk/tickets": true,
    "/helpdesk/my-tickets": true,
    "/helpdesk/my-tickets/new": true,
    "/my-tickets": true,
    "/my-tickets/new": true,
  };

  var CONTENT_SKIP_SELECTOR = [
    "script",
    "style",
    "code",
    "pre",
    "svg",
    "canvas",
    "[contenteditable='true']",
    "[contenteditable='']",
    ".ProseMirror",
    ".ql-editor",
    ".tiptap",
    ".text-editor",
    ".comment-content",
    ".article-content",
    ".ticket-subject",
    ".ticket-description",
    "[data-haravan-no-translate]",
    "[data-haravan-user-content]",
    "[data-user-content]",
  ].join(",");

  var TEXT_SKIP_SELECTOR = [
    CONTENT_SKIP_SELECTOR,
    "input",
    "textarea",
  ].join(",");

  var TRANSLATIONS = {
    "Helpdesk": "Trung tâm hỗ trợ",
    "Tickets": "Yêu cầu hỗ trợ",
    "Ticket": "Yêu cầu",
    "My Tickets": "Yêu cầu của tôi",
    "New Ticket": "Tạo yêu cầu mới",
    "New Support Ticket": "Phiếu hỗ trợ mới",
    "Knowledge Base": "Cơ sở Kiến thức",
    "Articles": "Bài viết",
    "Article": "Bài viết",
    "List": "Danh sách",
    "Views": "Chế độ xem",
    "View": "Chế độ xem",
    "Default": "Mặc định",

    "Create": "Tạo",
    "CREATE": "Tạo",
    "create": "Tạo",
    "+ Create": "Tạo",
    "Create Ticket": "Tạo yêu cầu",
    "Submit": "Gửi",
    "Save": "Lưu",
    "Cancel": "Hủy",
    "Close": "Đóng",
    "Apply": "Áp dụng",
    "Clear": "Xóa",
    "Reset": "Đặt lại",
    "Delete": "Xóa",
    "Remove": "Gỡ bỏ",
    "Edit": "Chỉnh sửa",
    "Update": "Cập nhật",
    "Add": "Thêm",
    "Back": "Quay lại",
    "Next": "Tiếp theo",
    "Previous": "Trước đó",
    "Send": "Gửi",
    "Upload": "Tải lên",
    "Download": "Tải xuống",
    "Browse": "Chọn tệp",

    "Filter": "Bộ lọc",
    "Filters": "Bộ lọc",
    "Columns": "Cột",
    "Column": "Cột",
    "Sort": "Sắp xếp",
    "Sort By": "Sắp xếp theo",
    "Sort by": "Sắp xếp theo",
    "Last Modified": "Cập nhật gần nhất",
    "Created On": "Ngày tạo",
    "Modified": "Đã cập nhật",
    "Refresh": "Làm mới",
    "Reload": "Tải lại",
    "Export": "Xuất dữ liệu",
    "Export All": "Xuất tất cả",
    "Export Records": "Xuất bản ghi",
    "Actions": "Thao tác",
    "More": "Thêm",

    "Search": "Tìm kiếm",
    "Search...": "Tìm kiếm...",
    "No results found": "Không tìm thấy kết quả",
    "Type something": "Nhập nội dung tìm kiếm",
    "Select an option": "Chọn một tùy chọn",
    "Choose an option": "Chọn một tùy chọn",
    "Empty": "Trống",
    "Empty - Choose a field to filter by": "Chưa có bộ lọc - Chọn trường để lọc",
    "Add Filter": "Thêm bộ lọc",
    "Add filter": "Thêm bộ lọc",
    "Remove filter": "Xóa bộ lọc",
    "Field": "Trường",
    "Condition": "Điều kiện",
    "Value": "Giá trị",
    "Where": "Điều kiện",
    "And": "Và",
    "Or": "Hoặc",
    "is": "là",
    "is not": "không là",
    "equals": "bằng",
    "not equals": "không bằng",
    "contains": "chứa",
    "does not contain": "không chứa",
    "like": "chứa",
    "not like": "không chứa",
    "in": "thuộc",
    "not in": "không thuộc",
    "between": "trong khoảng",
    "greater than": "lớn hơn",
    "less than": "nhỏ hơn",
    "before": "trước",
    "after": "sau",
    "set": "đã có",
    "not set": "chưa có",

    "Ascending": "Tăng dần",
    "Descending": "Giảm dần",
    "Newest First": "Mới nhất trước",
    "Oldest First": "Cũ nhất trước",

    "Load More": "Tải thêm",
    "of": "trên",
    "Select all": "Chọn tất cả",
    "1 row selected": "Đã chọn 1 dòng",
    "rows selected": "dòng đã chọn",

    "ID": "ID",
    "Name": "Tên",
    "Subject": "Tiêu đề",
    "Title": "Tiêu đề",
    "Description": "Mô tả",
    "Status": "Trạng thái",
    "Priority": "Mức ưu tiên",
    "Team": "Nhóm xử lý",
    "Agent": "Nhân viên xử lý",
    "Assigned To": "Người phụ trách",
    "Customer": "Khách hàng",
    "Contact": "Liên hệ",
    "Email": "Email",
    "Phone": "Số điện thoại",
    "Mobile No": "Số điện thoại",
    "First response": "Phản hồi đầu tiên",
    "First Response": "Phản hồi đầu tiên",
    "Resolution": "Giải quyết",
    "Resolution By": "Hạn giải quyết",
    "Response By": "Hạn phản hồi",
    "Creation": "Ngày tạo",
    "Created": "Đã tạo",
    "Owner": "Người tạo",
    "Type": "Loại yêu cầu",
    "Ticket Type": "Loại yêu cầu",
    "Category": "Danh mục",
    "Group": "Nhóm",
    "Nhóm (Group)": "Nhóm",
    "Product Suggestion": "Sản phẩm liên quan",
    "Loại yêu cầu (Type)": "Loại yêu cầu",
    "Sản phẩm liên quan (Suggestion)": "Sản phẩm liên quan",
    "Product Branch": "Nhánh sản phẩm",
    "Nhánh sản phẩm (Product Branch)": "Nhánh sản phẩm",
    "Feature": "Tính năng",
    "Tính năng": "Tính năng",
    "Link Web / MyHaravan": "Link Web / MyHaravan",
    "Shop / MyHaravan domain": "Tên miền Shop / MyHaravan",

    "New": "Mới tạo",
    "Open": "Đang mở",
    "Replied": "Đã phản hồi",
    "Awaiting Response": "Chờ phản hồi",
    "Resolved": "Đã xử lý",
    "Closed": "Đã đóng",
    "Urgent": "Khẩn cấp",
    "High": "Cao",
    "Medium": "Trung bình",
    "Low": "Thấp",
    "Fulfilled": "Đã hoàn thành",
    "Failed": "Thất bại",
    "Overdue": "Quá hạn",
    "Paused": "Tạm dừng",
    "Success": "Thành công",
    "Error": "Lỗi",

    "Today": "Hôm nay",
    "Yesterday": "Hôm qua",
    "Tomorrow": "Ngày mai",
    "Last 7 Days": "7 ngày qua",
    "Last 30 Days": "30 ngày qua",
    "This Week": "Tuần này",
    "This Month": "Tháng này",

    "Attachments": "Tệp đính kèm",
    "Attachment": "Tệp đính kèm",
    "Attach": "Đính kèm",
    "Drop files here or click to upload": "Kéo tệp vào đây hoặc bấm để tải lên",
    "Detailed explanation": "Mô tả chi tiết",
    "Briefly describe your issue": "Mô tả ngắn gọn vấn đề của bạn",
    "Please explain the issue": "Vui lòng mô tả vấn đề",
    "Submit Ticket": "Gửi yêu cầu",
    "Create Ticket": "Tạo yêu cầu",
    "Ticket created": "Đã tạo yêu cầu",
    "Ticket updated": "Đã cập nhật yêu cầu",

    "Suggested Articles": "Bài viết gợi ý",
    "Suggested articles": "Bài viết gợi ý",
    "Related Articles": "Bài viết liên quan",
    "Did this help?": "Nội dung này có hữu ích không?",
    "Read more": "Xem thêm",

    "Loading": "Đang tải",
    "Loading...": "Đang tải...",
    "No Data": "Không có dữ liệu",
    "No records found": "Không có bản ghi",
    "No tickets found": "Không có yêu cầu",
    "Something went wrong": "Đã xảy ra lỗi",
    "Required": "Bắt buộc",
    "Invalid value": "Giá trị không hợp lệ",
  };

  var TRANSLATIONS_LC = {};
  for (var key in TRANSLATIONS) {
    if (Object.prototype.hasOwnProperty.call(TRANSLATIONS, key)) {
      TRANSLATIONS_LC[key.toLowerCase()] = TRANSLATIONS[key];
    }
  }

  var UNIT_TRANSLATIONS = {
    second: "giây",
    minute: "phút",
    hour: "giờ",
    day: "ngày",
    week: "tuần",
    month: "tháng",
    year: "năm",
  };

  var observer = null;
  var routeTimer = null;
  var pendingRun = null;
  var lastActiveRoute = "";

  function normalizePath(path) {
    var normalized = String(path || "").replace(/\/+$/, "");
    return normalized || "/";
  }

  function isTargetRoute() {
    var currentPath = normalizePath(window.location.pathname);
    if (TARGET_ROUTES[currentPath]) return true;
    if (currentPath.indexOf("/helpdesk") === 0) return true;
    if (currentPath.indexOf("/my-tickets") === 0) return true;
    return false;
  }

  function safeLocalStorageGet(key) {
    try {
      return window.localStorage && window.localStorage.getItem(key);
    } catch (e) {
      return "";
    }
  }

  function isDisabled() {
    var params;
    if (window[DISABLE_FLAG] === true) return true;
    if (safeLocalStorageGet(LOCAL_STORAGE_DISABLE_KEY) === "1") return true;
    try {
      params = new URLSearchParams(window.location.search || "");
      return params.get("haravan_vi_override") === "0" || params.get("hrv_vi_override") === "0";
    } catch (e) {
      return false;
    }
  }

  function getBoot() {
    if (typeof window.frappe === "undefined" || !window.frappe.boot) return {};
    return window.frappe.boot || {};
  }

  function appendValue(values, value) {
    if (Array.isArray(value)) {
      value.forEach(function (item) {
        appendValue(values, item);
      });
      return;
    }
    if (value != null && value !== "") values.push(String(value));
  }

  function isVietnameseSignal(value) {
    var normalized = String(value || "").toLowerCase().trim();
    return (
      normalized.indexOf("vi") === 0 ||
      normalized.indexOf("vietnamese") !== -1 ||
      normalized.indexOf("tiếng việt") !== -1 ||
      normalized.indexOf("tieng viet") !== -1
    );
  }

  function hasVietnamesePageSignal() {
    var value = "";
    if (!document.body) return false;

    value = normalizeText(
      [
        document.title,
        document.body.innerText || document.body.textContent || "",
      ].join(" ")
    ).toLowerCase();

    return [
      "danh sách yêu cầu",
      "phiếu hỗ trợ mới",
      "cơ sở kiến thức",
      "chọn loại yêu cầu",
      "số điện thoại",
      "chủ đề",
      "mô tả vấn đề",
      "mới tạo",
      "đã xử lý",
    ].some(function (marker) {
      return value.indexOf(marker) !== -1;
    });
  }

  function isVietnameseLocale() {
    var boot = getBoot();
    var explicitSignals = [];
    var browserSignals = [];

    if (window[NAMESPACE] && window[NAMESPACE].force === true) return true;

    appendValue(explicitSignals, boot.lang);
    appendValue(explicitSignals, boot.user_lang);
    appendValue(explicitSignals, boot.user && boot.user.language);
    appendValue(explicitSignals, boot.sysdefaults && boot.sysdefaults.language);
    appendValue(explicitSignals, document.documentElement && document.documentElement.lang);
    appendValue(explicitSignals, safeLocalStorageGet("preferred_language"));
    appendValue(explicitSignals, safeLocalStorageGet("language"));
    appendValue(explicitSignals, safeLocalStorageGet("lang"));

    if (explicitSignals.some(isVietnameseSignal)) return true;
    if (hasVietnamesePageSignal()) return true;

    appendValue(browserSignals, window.navigator && window.navigator.languages);
    appendValue(browserSignals, window.navigator && window.navigator.language);
    return browserSignals.some(isVietnameseSignal);
  }

  function shouldActivate() {
    return !isDisabled() && isTargetRoute() && isVietnameseLocale();
  }

  function normalizeText(value) {
    return String(value || "").replace(/[\s\u200B-\u200D\uFEFF]+/g, " ").trim();
  }

  function preserveOuterWhitespace(original, translated) {
    var leading = String(original || "").match(/^\s*/)[0];
    var trailing = String(original || "").match(/\s*$/)[0];
    return leading + translated + trailing;
  }

  function translateUnit(unit) {
    var singular = String(unit || "").toLowerCase().replace(/s$/, "");
    return UNIT_TRANSLATIONS[singular] || unit;
  }

  function translateRelativeTime(text) {
    var value = normalizeText(text);
    var match;

    // Test fixture examples: "in 4 days", "4 days ago".
    if (/^just now$/i.test(value)) return "vừa xong";
    if (/^a few seconds ago$/i.test(value)) return "vài giây trước";
    if (/^in a few seconds$/i.test(value)) return "trong vài giây";

    match = value.match(/^a (second|minute|hour|day|week|month|year) ago$/i);
    if (match) return "1 " + translateUnit(match[1]) + " trước";

    match = value.match(/^an (hour) ago$/i);
    if (match) return "1 " + translateUnit(match[1]) + " trước";

    match = value.match(/^in a (second|minute|hour|day|week|month|year)$/i);
    if (match) return "trong 1 " + translateUnit(match[1]);

    match = value.match(/^in an (hour)$/i);
    if (match) return "trong 1 " + translateUnit(match[1]);

    match = value.match(/^(\d+) (second|minute|hour|day|week|month|year)s? ago$/i);
    if (match) return match[1] + " " + translateUnit(match[2]) + " trước";

    match = value.match(/^in (\d+) (second|minute|hour|day|week|month|year)s?$/i);
    if (match) return "trong " + match[1] + " " + translateUnit(match[2]);

    return "";
  }

  function translateValidationText(text) {
    var value = normalizeText(text);
    var match = value.match(/^(.+) is required$/i);
    var field;

    if (!match) return "";
    field = translateTextValue(match[1]) || match[1];
    return field + " là bắt buộc";
  }

  function translateSelectionText(text) {
    var value = normalizeText(text);
    var match = value.match(/^(\d+) rows selected$/i);
    if (match) return "Đã chọn " + match[1] + " dòng";
    return "";
  }

  function translateExportText(text) {
    var value = normalizeText(text);
    var match = value.match(/^Export All (\d+) Records?$/i);
    if (match) return "Xuất toàn bộ " + match[1] + " bản ghi";
    return "";
  }

  function translateTextValue(text) {
    var normalized = normalizeText(text);
    if (!normalized) return "";

    var match = TRANSLATIONS[normalized] ||
                TRANSLATIONS_LC[normalized.toLowerCase()] ||
                translateRelativeTime(normalized) ||
                translateValidationText(normalized) ||
                translateSelectionText(normalized) ||
                translateExportText(normalized);

    if (match) return match;

    if (normalized.slice(-1) === "*") {
      var baseText = normalizeText(normalized.slice(0, -1));
      var baseMatch = TRANSLATIONS[baseText] ||
                      TRANSLATIONS_LC[baseText.toLowerCase()] ||
                      translateRelativeTime(baseText) ||
                      translateValidationText(baseText) ||
                      translateSelectionText(baseText) ||
                      translateExportText(baseText);
      if (baseMatch) return baseMatch + " *";
    }

    return "";
  }

  function shouldSkipForText(node) {
    var parent = node && node.parentElement;
    if (!parent) return true;
    return Boolean(parent.closest(TEXT_SKIP_SELECTOR));
  }

  function shouldSkipForAttributes(element) {
    if (!element || !element.matches) return true;
    return Boolean(element.closest(CONTENT_SKIP_SELECTOR));
  }

  function translateTextNodes(root) {
    var walker;
    var node;
    var translated;

    if (!root) return;

    walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: function (textNode) {
        if (shouldSkipForText(textNode)) return NodeFilter.FILTER_REJECT;
        if (!normalizeText(textNode.nodeValue)) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      },
    });

    while ((node = walker.nextNode())) {
      translated = translateTextValue(node.nodeValue);
      if (translated && normalizeText(node.nodeValue) !== translated) {
        node.nodeValue = preserveOuterWhitespace(node.nodeValue, translated);
      }
    }
  }

  function translateElementAttributes(root) {
    var nodes;
    var attrs = ["placeholder", "title", "aria-label", "label"];

    if (!root || !root.querySelectorAll) return;

    nodes = [root].concat(Array.prototype.slice.call(root.querySelectorAll("*")));
    nodes.forEach(function (element) {
      if (shouldSkipForAttributes(element)) return;
      attrs.forEach(function (attr) {
        var value = element.getAttribute && element.getAttribute(attr);
        var translated = translateTextValue(value);
        if (translated && normalizeText(value) !== translated) {
          element.setAttribute(attr, translated);
        }
      });
    });
  }

  function translateRoot(root) {
    if (!shouldActivate()) return;
    translateTextNodes(root || document.body);
    translateElementAttributes(root || document.body);
  }

  function scheduleRun(root) {
    if (pendingRun) window.clearTimeout(pendingRun);
    pendingRun = window.setTimeout(function () {
      pendingRun = null;
      translateRoot(root || document.body);
    }, OBSERVER_DEBOUNCE_MS);
  }

  function startObserver() {
    if (observer || !document.body || !window.MutationObserver) return;
    observer = new MutationObserver(function (mutations) {
      var shouldRun = false;
      mutations.forEach(function (mutation) {
        if (mutation.type === "childList" && mutation.addedNodes && mutation.addedNodes.length) {
          shouldRun = true;
        }
        if (mutation.type === "characterData" || mutation.type === "attributes") {
          shouldRun = true;
        }
      });
      if (shouldRun) scheduleRun(document.body);
    });
    observer.observe(document.body, {
      childList: true,
      subtree: true,
      characterData: true,
      attributes: true,
      attributeFilter: ["placeholder", "title", "aria-label", "label"],
    });
  }

  function stopObserver() {
    if (observer) {
      observer.disconnect();
      observer = null;
    }
  }

  function run() {
    if (!shouldActivate()) {
      stopObserver();
      return;
    }
    lastActiveRoute = normalizePath(window.location.pathname);
    translateRoot(document.body);
    startObserver();
  }

  function handleRouteChange() {
    var currentRoute = normalizePath(window.location.pathname);
    if (currentRoute !== lastActiveRoute || shouldActivate()) {
      run();
    }
  }

  function installHistoryWatcher() {
    if (window.__haravanHelpdeskViHistoryWatcher) return;
    window.__haravanHelpdeskViHistoryWatcher = true;

    ["pushState", "replaceState"].forEach(function (method) {
      var original = window.history && window.history[method];
      if (!original) return;
      window.history[method] = function () {
        var result = original.apply(this, arguments);
        window.setTimeout(handleRouteChange, 0);
        return result;
      };
    });

    window.addEventListener("popstate", handleRouteChange);
    routeTimer = window.setInterval(handleRouteChange, ROUTE_POLL_MS);
    window[NAMESPACE].routeTimer = routeTimer;
  }

  function init() {
    installHistoryWatcher();
    run();
  }

  window[NAMESPACE] = window[NAMESPACE] || {};
  window[NAMESPACE].run = run;
  window[NAMESPACE].disconnect = stopObserver;
  window[NAMESPACE].shouldActivate = shouldActivate;
  window[NAMESPACE].isVietnameseLocale = isVietnameseLocale;
  window[NAMESPACE].isTargetRoute = isTargetRoute;
  window[NAMESPACE].translateTextValue = translateTextValue;
  window[NAMESPACE].translations = TRANSLATIONS;
  window[NAMESPACE].targetRoutes = TARGET_ROUTES;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
