#!/usr/bin/env python3
"""Patch Haravan Helpdesk AI assist scripts on a live Frappe site.

Fixes:
- AI summary/reply button response unwrapping and duplicate-click handling.
- Summary/reply APIs return both legacy top-level fields and canonical data.
- AI analyze writes an internal Comment linked to the HD Ticket.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests


ASSIST_MENU_SCRIPT = r'''function setupForm({ doc, call, $dialog, createToast }) {
  const actions = [];
  const CLOSED_STATUSES = ["Resolved", "Closed", "Rejected"];

  if (!doc.name || CLOSED_STATUSES.includes(doc.status)) {
    return { actions };
  }

  const state = window.__haravanAiAssistState || (window.__haravanAiAssistState = {});
  const toast = (title, message, variant = "info") => {
    createToast?.({ title, message, variant, appearance: variant });
  };

  const unwrap = (response) => {
    const first = response?.message ?? response?.data ?? response;
    return first?.message && typeof first.message === "object" ? first.message : first || {};
  };

  const isSuccess = (payload) => {
    if (payload.success === false) return false;
    if (payload.exc || payload.exception || payload._server_messages) return false;
    return true;
  };

  const errorMessage = (payload, fallback) => {
    if (typeof payload.message === "string") return payload.message;
    if (payload.error) return payload.error;
    if (payload.exception) return payload.exception;
    return fallback;
  };

  const escapeHtml = (value) => String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");

  const request = async (method, args = {}) => unwrap(await call(method, args));

  const openSummary = (payload) => {
    const data = payload.data || payload;
    const bullets = Array.isArray(data.bullets) ? data.bullets : [];
    const risks = Array.isArray(data.risks) ? data.risks : [];
    const nextSteps = Array.isArray(data.next_steps) ? data.next_steps : [];
    const list = (items) => items.length ? `<ul>${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>` : "";

    $dialog({
      title: "AI Tóm tắt",
      html: `
        <div class="p-4 text-sm leading-6">
          <h4 class="font-medium mb-2">Tóm tắt</h4>
          <p>${escapeHtml(data.summary || "Không có tóm tắt.")}</p>
          ${bullets.length ? `<h4 class="font-medium mt-4 mb-2">Điểm chính</h4>${list(bullets)}` : ""}
          ${risks.length ? `<h4 class="font-medium mt-4 mb-2">Rủi ro / thiếu thông tin</h4>${list(risks)}` : ""}
          ${nextSteps.length ? `<h4 class="font-medium mt-4 mb-2">Bước tiếp theo</h4>${list(nextSteps)}` : ""}
        </div>`,
      actions: [{ label: "Đóng", theme: "gray", onClick: (close) => close() }]
    });
  };

  const openReply = (payload) => {
    const data = payload.data || payload;
    const dialogId = "ai-reply-" + Date.now();
    const options = (Array.isArray(data.options) ? data.options : [])
      .filter((option) => option && option.content)
      .slice(0, 3);
    const selectedFromApi = Number.isInteger(data.selected_index) ? data.selected_index : -1;
    const bestIndex = selectedFromApi >= 0 && selectedFromApi < options.length
      ? selectedFromApi
      : options.reduce((best, option, index) => {
          const current = Number(option.confidence || 0);
          const previous = Number(options[best]?.confidence || 0);
          return current > previous ? index : best;
        }, 0);
    const first = options[bestIndex] || options[0] || {};
    const optionList = options.map((option, index) => {
      const confidence = Math.round(Number(option.confidence || 0) * 100);
      const label = option.label || option.scenario || `Phương án ${index + 1}`;
      const reason = option.reason || option.when_to_use || "";
      const missing = Array.isArray(option.missing_context) ? option.missing_context.filter(Boolean) : [];
      return `
        <label class="block border rounded p-3 cursor-pointer ${index === bestIndex ? "border-blue-500 bg-blue-50" : "border-gray-200"}">
          <div class="flex items-start gap-2">
            <input type="radio" name="${dialogId}-choice" value="${index}" ${index === bestIndex ? "checked" : ""} class="mt-1">
            <div>
              <div class="font-medium">${escapeHtml(label)}${confidence ? ` · ${confidence}%` : ""}</div>
              ${reason ? `<div class="text-xs text-gray-600 mt-1">${escapeHtml(reason)}</div>` : ""}
              ${missing.length ? `<div class="text-xs text-amber-700 mt-1">Thiếu bối cảnh: ${escapeHtml(missing.join(", "))}</div>` : ""}
            </div>
          </div>
        </label>`;
    }).join("");

    $dialog({
      title: "AI gợi ý trả lời",
      html: `
        <div id="${dialogId}" class="p-4 space-y-4">
          <div class="text-xs text-gray-600">
            AI đã đọc nội dung ticket và các trao đổi gần nhất. Phương án có độ tự tin cao nhất được chọn sẵn để agent chỉnh sửa trước khi gửi.
          </div>
          ${optionList || `<div class="text-sm text-gray-600">AI chưa trả về phương án phù hợp.</div>`}
          <textarea id="${dialogId}-content" rows="12" class="w-full border rounded p-3 text-sm">${escapeHtml(first.content || "")}</textarea>
        </div>`,
      actions: [
        {
          label: "Thêm comment nội bộ",
          theme: "blue",
          variant: "solid",
          onClick: async (close) => {
            const content = document.getElementById(`${dialogId}-content`)?.value?.trim();
            if (!content) {
              toast("Thiếu nội dung", "Vui lòng nhập nội dung reply.", "error");
              return;
            }
            const result = await request("send-ai-reply", { ticket_id: doc.name, content });
            if (!isSuccess(result)) {
              toast("Không thêm được comment", errorMessage(result, "API trả về lỗi."), "error");
              return;
            }
            close();
            toast("Đã thêm comment", "Comment nội bộ đã được thêm vào ticket.", "success");
          }
        },
        { label: "Bỏ qua", theme: "gray", onClick: (close) => close() }
      ]
    });
    setTimeout(() => {
      const root = document.getElementById(dialogId);
      if (!root) return;
      root.querySelectorAll(`input[name="${dialogId}-choice"]`).forEach((input) => {
        input.addEventListener("change", () => {
          const selected = options[Number(input.value)] || {};
          const textarea = document.getElementById(`${dialogId}-content`);
          if (textarea) textarea.value = selected.content || "";
        });
      });
    }, 50);
  };

  const runOnce = async (key, fn) => {
    if (state[key]) {
      toast("AI đang xử lý", "Tác vụ AI này đang chạy, vui lòng chờ thêm một chút.", "info");
      return;
    }
    state[key] = true;
    try {
      await fn();
    } finally {
      delete state[key];
    }
  };

  actions.push({
    group: "AI",
    hideLabel: true,
    items: [
      {
        label: "AI Tóm tắt",
        onClick: () => runOnce("summary:" + doc.name, async () => {
          toast("Đang tóm tắt", "AI đang phân tích ticket.");
          const result = await request("generate-ai-summary", { ticket_id: doc.name });
          if (!isSuccess(result)) throw new Error(errorMessage(result, "Không tạo được tóm tắt."));
          openSummary(result);
        }).catch((error) => {
          toast("Lỗi AI", error.message || "Không thể tạo tóm tắt.", "error");
        })
      },
      {
        label: "AI Gợi ý trả lời",
        onClick: () => runOnce("reply:" + doc.name, async () => {
          toast("Đang tạo gợi ý", "AI đang soạn các phương án trả lời.");
          const result = await request("generate-ai-reply", { ticket_id: doc.name });
          if (!isSuccess(result)) throw new Error(errorMessage(result, "Không tạo được gợi ý trả lời."));
          openReply(result);
        }).catch((error) => {
          toast("Lỗi AI", error.message || "Không thể tạo gợi ý trả lời.", "error");
        })
      }
    ]
  });

  return { actions };
}
'''


SUMMARY_SCRIPT = r'''# API Method: generate-ai-summary - Helpdesk Integrations Settings

SETTINGS_DOCTYPE = "Helpdesk Integrations Settings"
DEFAULT_MODEL = "gemini-2.5-flash"
PASSWORD_FIELDS = ["gemini_api_key", "openrouter_api_key", "gitlab_token", "inside_api_key", "inside_api_secret", "bitrix_webhook_url"]


def as_text(value):
    return "" if value is None else str(value).strip()


def setting_value(fieldname, default=None):
    if fieldname in PASSWORD_FIELDS:
        try:
            settings = frappe.get_doc(SETTINGS_DOCTYPE)
            value = settings.get_password(fieldname)
            if value not in (None, ""):
                return value
        except Exception:
            pass
    try:
        value = frappe.db.get_single_value(SETTINGS_DOCTYPE, fieldname)
        if value not in (None, ""):
            return value
    except Exception:
        pass
    try:
        settings = frappe.get_doc(SETTINGS_DOCTYPE)
        value = settings.get(fieldname)
        if value not in (None, ""):
            return value
    except Exception:
        pass
    return default


def strip_html(raw):
    try:
        return frappe.utils.strip_html(as_text(raw))
    except Exception:
        text = as_text(raw)
        out = []
        in_tag = False
        for ch in text:
            if ch == "<":
                in_tag = True
            elif ch == ">":
                in_tag = False
                out.append(" ")
            elif not in_tag:
                out.append(ch)
        return " ".join("".join(out).split())


def parse_confidence(value):
    if value in (None, ""):
        return 0
    try:
        score = float(value)
        if score > 1:
            score = score / 100
        if score < 0:
            return 0
        if score > 1:
            return 1
        return score
    except Exception:
        label = as_text(value).lower()
        if label in ["cao", "high", "tot", "tốt"]:
            return 0.85
        if label in ["trung binh", "trung bình", "medium", "vua", "vừa"]:
            return 0.6
        if label in ["thap", "thấp", "low"]:
            return 0.35
        return 0


def response(success, data=None, message="", error=""):
    data = data or {}
    payload = {"success": success, "data": data, "message": message}
    if error:
        payload["error"] = error
    for key in data:
        payload[key] = data.get(key)
    frappe.response["message"] = payload


ticket_id = frappe.form_dict.get("ticket_id") or frappe.form_dict.get("name")
if not ticket_id:
    response(False, {}, error="ticket_id is required")
else:
    try:
        api_key = as_text(setting_value("gemini_api_key"))
        model = as_text(setting_value("gemini_model", DEFAULT_MODEL)) or DEFAULT_MODEL
        if not api_key:
            response(False, {}, error="Chưa cấu hình gemini_api_key trong Helpdesk Integrations Settings")
        else:
            ticket = frappe.get_doc("HD Ticket", ticket_id)
            recent = frappe.get_all("Communication", filters={"reference_doctype": "HD Ticket", "reference_name": ticket_id}, fields=["content", "sent_or_received", "creation"], order_by="creation desc", limit=8)
            prompt_data = {
                "subject": as_text(ticket.get("subject")),
                "description": strip_html(ticket.get("description"))[:1200],
                "customer": as_text(ticket.get("customer")),
                "status": as_text(ticket.get("status")),
                "recent_messages": [{"direction": as_text(c.get("sent_or_received")), "content": strip_html(c.get("content"))[:500]} for c in recent],
            }
            instruction = "Bạn là AI hỗ trợ agent Haravan Helpdesk. Tóm tắt ticket nội bộ bằng tiếng Việt có dấu. Chỉ trả JSON: {summary, bullets, risks, next_steps, confidence}. Confidence phải là số từ 0 đến 1."
            endpoint = "https://generativelanguage.googleapis.com/v1beta/models/" + model + ":generateContent"
            payload = {"contents": [{"role": "user", "parts": [{"text": instruction + "\n\nDU LIEU TICKET:\n" + json.dumps(prompt_data, ensure_ascii=False)}]}], "generationConfig": {"temperature": 0.3, "responseMimeType": "application/json"}}
            gemini = frappe.make_post_request(endpoint, data=json.dumps(payload), headers={"x-goog-api-key": api_key, "Content-Type": "application/json"})
            text = ""
            candidates = (gemini or {}).get("candidates") or []
            if candidates:
                parts = (((candidates[0] or {}).get("content") or {}).get("parts") or [])
                if parts:
                    text = parts[0].get("text") or ""
            if not text:
                response(False, {}, error="Gemini trả về kết quả rỗng")
            else:
                parsed = json.loads(as_text(text).replace("```json", "").replace("```", "").strip())
                data = {
                    "summary": as_text(parsed.get("summary")),
                    "bullets": parsed.get("bullets") or [],
                    "risks": parsed.get("risks") or [],
                    "next_steps": parsed.get("next_steps") or [],
                    "confidence": parse_confidence(parsed.get("confidence")),
                }
                response(True, data, "AI đã tạo tóm tắt ticket")
    except Exception as exc:
        frappe.log_error(as_text(exc)[:1000], "generate-ai-summary Error")
        response(False, {}, error=as_text(exc))
'''


REPLY_SCRIPT = r'''# API Method: generate-ai-reply - Helpdesk Integrations Settings

SETTINGS_DOCTYPE = "Helpdesk Integrations Settings"
DEFAULT_MODEL = "gemini-2.5-flash"
PASSWORD_FIELDS = ["gemini_api_key", "openrouter_api_key", "gitlab_token", "inside_api_key", "inside_api_secret", "bitrix_webhook_url"]


def as_text(value):
    return "" if value is None else str(value).strip()


def setting_value(fieldname, default=None):
    if fieldname in PASSWORD_FIELDS:
        try:
            settings = frappe.get_doc(SETTINGS_DOCTYPE)
            value = settings.get_password(fieldname)
            if value not in (None, ""):
                return value
        except Exception:
            pass
    try:
        value = frappe.db.get_single_value(SETTINGS_DOCTYPE, fieldname)
        if value not in (None, ""):
            return value
    except Exception:
        pass
    try:
        settings = frappe.get_doc(SETTINGS_DOCTYPE)
        value = settings.get(fieldname)
        if value not in (None, ""):
            return value
    except Exception:
        pass
    return default


def strip_html(raw):
    try:
        return frappe.utils.strip_html(as_text(raw))
    except Exception:
        text = as_text(raw)
        out = []
        in_tag = False
        for ch in text:
            if ch == "<":
                in_tag = True
            elif ch == ">":
                in_tag = False
                out.append(" ")
            elif not in_tag:
                out.append(ch)
        return " ".join("".join(out).split())


def response(success, data=None, message="", error=""):
    data = data or {}
    payload = {"success": success, "data": data, "message": message}
    if error:
        payload["error"] = error
    for key in data:
        payload[key] = data.get(key)
    frappe.response["message"] = payload


def parse_confidence(value):
    if value in (None, ""):
        return 0
    try:
        score = float(value)
        if score > 1:
            score = score / 100
        if score < 0:
            return 0
        if score > 1:
            return 1
        return score
    except Exception:
        label = as_text(value).lower()
        if label in ["cao", "high", "tốt", "tot"]:
            return 0.85
        if label in ["trung bình", "trung binh", "medium", "vừa", "vua"]:
            return 0.6
        if label in ["thấp", "thap", "low"]:
            return 0.35
        return 0


def listify(value):
    if isinstance(value, list):
        return [as_text(item) for item in value if as_text(item)]
    text = as_text(value)
    return [text] if text else []


def normalize_options(parsed):
    raw_options = parsed.get("options") if isinstance(parsed, dict) else []
    if not isinstance(raw_options, list):
        raw_options = []
    if not raw_options and isinstance(parsed, dict) and as_text(parsed.get("content")):
        raw_options = [parsed]

    options = []
    for index, option in enumerate(raw_options[:3]):
        if not isinstance(option, dict):
            continue
        content = as_text(option.get("content") or option.get("reply") or option.get("message"))
        if not content:
            continue
        confidence = parse_confidence(option.get("confidence"))
        label = as_text(option.get("label") or option.get("scenario") or ("Phương án " + str(index + 1)))
        options.append(
            {
                "label": label,
                "scenario": as_text(option.get("scenario") or label),
                "confidence": confidence,
                "reason": as_text(option.get("reason") or option.get("when_to_use")),
                "missing_context": listify(option.get("missing_context") or option.get("needs")),
                "content": content,
            }
        )
    selected_index = 0
    for index, option in enumerate(options):
        if option.get("confidence", 0) > options[selected_index].get("confidence", 0):
            selected_index = index
    return options, selected_index


def post_gemini(model, api_key, prompt_data):
    instruction = (
        "Bạn là AI hỗ trợ agent chăm sóc khách hàng tại Haravan Helpdesk. "
        "Hãy đọc kỹ nội dung ticket, mô tả ban đầu, trường phân loại và các trao đổi gần nhất để hiểu nhu cầu thật của khách. "
        "Luôn viết tiếng Việt có dấu, lịch sự, rõ ràng, không dùng tiếng Việt không dấu. "
        "Không bịa chính sách, không hứa đã xử lý nếu dữ liệu ticket chưa chứng minh điều đó. "
        "Nếu thiếu bối cảnh, hãy đặt câu hỏi ngắn gọn trong nội dung trả lời. "
        "Trong một lần gọi, trả đúng tối đa 3 phương án cho các tình huống hợp lý nhất; tự xếp phương án chắc nhất với confidence cao nhất. "
        "Chỉ trả JSON thuần theo schema: "
        "{\"confidence\":0.85,\"options\":[{\"label\":\"Tình huống ngắn\",\"scenario\":\"Khách đang cần gì\",\"confidence\":0.85,\"reason\":\"Vì sao chọn\",\"missing_context\":[\"thông tin còn thiếu\"],\"content\":\"Mẫu trả lời cho khách\"}]}"
    )
    endpoint = "https://generativelanguage.googleapis.com/v1beta/models/" + model + ":generateContent"
    payload = {
        "contents": [{"role": "user", "parts": [{"text": instruction + "\n\nDU LIEU TICKET:\n" + json.dumps(prompt_data, ensure_ascii=False)}]}],
        "generationConfig": {"temperature": 0.4, "responseMimeType": "application/json"},
    }
    return frappe.make_post_request(endpoint, data=json.dumps(payload), headers={"x-goog-api-key": api_key, "Content-Type": "application/json"})


ticket_id = frappe.form_dict.get("ticket_id") or frappe.form_dict.get("name")
if not ticket_id:
    response(False, {}, error="ticket_id is required")
else:
    try:
        api_key = as_text(setting_value("gemini_api_key"))
        model = as_text(setting_value("gemini_model", DEFAULT_MODEL)) or DEFAULT_MODEL
        if not api_key:
            response(False, {}, error="Chưa cấu hình gemini_api_key trong Helpdesk Integrations Settings")
        else:
            ticket = frappe.get_doc("HD Ticket", ticket_id)
            try:
                recent = frappe.get_all("Communication", filters={"reference_doctype": "HD Ticket", "reference_name": ticket_id}, fields=["content", "sent_or_received", "creation", "sender", "recipients", "subject"], order_by="creation desc", limit=10)
                recent.reverse()
            except Exception as context_exc:
                frappe.log_error(as_text(context_exc)[:500], "generate-ai-reply Communication Context")
                recent = []
            try:
                internal_notes = frappe.get_all("Comment", filters={"reference_doctype": "HD Ticket", "reference_name": ticket_id}, fields=["content", "comment_type", "creation", "owner"], order_by="creation desc", limit=5)
                internal_notes.reverse()
            except Exception as context_exc:
                frappe.log_error(as_text(context_exc)[:500], "generate-ai-reply Comment Context")
                internal_notes = []
            ticket_fields = {}
            for fieldname in [
                "subject",
                "description",
                "customer",
                "status",
                "priority",
                "ticket_type",
                "custom_type",
                "custom_internal_type",
                "custom_service_line",
                "custom_service_name",
                "custom_service_vendor",
                "custom_product_suggestion",
                "custom_myharavan",
                "custom_org_id",
                "custom_email",
                "custom_phone",
            ]:
                value = ticket.get(fieldname)
                if value not in (None, ""):
                    ticket_fields[fieldname] = strip_html(value)[:1200] if fieldname == "description" else as_text(value)
            prompt_data = {
                "ticket": ticket_fields,
                "reply_goal": "Soạn gợi ý trả lời cho agent. Agent sẽ kiểm tra và chỉnh sửa trước khi gửi cho khách.",
                "recent_messages_oldest_to_newest": [
                    {
                        "direction": as_text(c.get("sent_or_received")),
                        "creation": as_text(c.get("creation")),
                        "sender": as_text(c.get("sender")),
                        "subject": as_text(c.get("subject")),
                        "content": strip_html(c.get("content"))[:700],
                    }
                    for c in recent
                ],
                "internal_notes_oldest_to_newest": [
                    {
                        "creation": as_text(c.get("creation")),
                        "owner": as_text(c.get("owner")),
                        "type": as_text(c.get("comment_type")),
                        "content": strip_html(c.get("content"))[:500],
                    }
                    for c in internal_notes
                ],
            }
            gemini = post_gemini(model, api_key, prompt_data)
            text = ""
            candidates = (gemini or {}).get("candidates") or []
            if candidates:
                parts = (((candidates[0] or {}).get("content") or {}).get("parts") or [])
                if parts:
                    text = parts[0].get("text") or ""
            if not text:
                response(False, {}, error="Gemini trả về kết quả rỗng")
            else:
                parsed = json.loads(as_text(text).replace("```json", "").replace("```", "").strip())
                options, selected_index = normalize_options(parsed)
                if not options:
                    response(False, {}, error="Gemini không trả về phương án reply")
                else:
                    data = {"options": options, "selected_index": selected_index, "confidence": parse_confidence(parsed.get("confidence") or options[selected_index].get("confidence"))}
                    response(True, data, "AI đã tạo gợi ý trả lời")
    except Exception as exc:
        frappe.log_error(as_text(exc)[:1000], "generate-ai-reply Error")
        response(False, {}, error=as_text(exc))
'''


SEND_REPLY_SCRIPT = r'''# Server Script — API Method: send-ai-reply
# Adds the AI-drafted reply as an internal Helpdesk comment. It must not email customers.


def as_text(value):
    return "" if value is None else str(value).strip()


def response(success, data=None, message="", error=""):
    data = data or {}
    payload = {"success": success, "data": data, "message": message}
    if error:
        payload["error"] = error
    for key in data:
        payload[key] = data.get(key)
    frappe.response["message"] = payload


def clear_server_messages():
    try:
        frappe.message_log = []
    except Exception:
        pass
    try:
        frappe.local.message_log = []
    except Exception:
        pass
    try:
        frappe.local.response.pop("_server_messages", None)
    except Exception:
        pass


def add_internal_comment(ticket, content):
    safe = frappe.utils.escape_html(as_text(content)).replace("\n", "<br>")
    comment = frappe.get_doc(
        {
            "doctype": "Comment",
            "comment_type": "Comment",
            "reference_doctype": "HD Ticket",
            "reference_name": ticket.name,
            "reference_owner": ticket.owner,
            "content": safe,
            "published": 0,
        }
    )
    comment.insert(ignore_permissions=True)
    clear_server_messages()
    return comment.name


ticket_id = frappe.form_dict.get("ticket_id") or frappe.form_dict.get("name")
content = frappe.form_dict.get("content")

if not ticket_id:
    response(False, {}, error="ticket_id is required")
elif not as_text(content):
    response(False, {}, error="Nội dung không được để trống")
else:
    try:
        ticket = frappe.get_doc("HD Ticket", ticket_id)
        comment_id = add_internal_comment(ticket, content)
        response(True, {"comment_id": comment_id}, "Đã thêm comment nội bộ vào ticket")

    except Exception as exc:
        try:
            frappe.log_error(as_text(exc)[:1000], "send-ai-reply Comment Error")
        except Exception:
            pass
        response(False, {}, error=as_text(exc))
'''


ANALYZE_OLD_ADD_NOTE = '''def add_note(ticket, result, updated_fields, gemini_status):
    body = "AI Ghi chú nội bộ\\n\\nNguồn: " + as_text(result.get("source")) + "\\nĐã cập nhật: " + (", ".join(updated_fields) if updated_fields else "Không có") + "\\nLog AI: " + as_text(gemini_status or "configured") + "\\nReasoning: " + as_text(result.get("reasoning"))
    try:
        ticket.add_comment("Comment", frappe.utils.escape_html(body).replace("\\n", "<br>"))
    except Exception as exc:
        frappe.log_error(as_text(exc)[:500], SCRIPT_TITLE + " comment")
'''


ANALYZE_NEW_ADD_NOTE = '''def clear_server_messages():
    try:
        frappe.message_log = []
    except Exception:
        pass
    try:
        frappe.local.message_log = []
    except Exception:
        pass
    try:
        frappe.local.response.pop("_server_messages", None)
    except Exception:
        pass


def add_note(ticket, result, updated_fields, gemini_status, skipped_updates=None):
    skipped_updates = skipped_updates or {}
    body = (
        "AI Ghi chú nội bộ\\n\\n"
        + "Nguồn: " + as_text(result.get("source")) + "\\n"
        + "Đã cập nhật: " + (", ".join(updated_fields) if updated_fields else "Không có") + "\\n"
        + "Bỏ qua: " + (", ".join(skipped_updates.keys()) if skipped_updates else "Không có") + "\\n"
        + "Log AI: " + as_text(gemini_status or "configured") + "\\n"
        + "Reasoning: " + as_text(result.get("reasoning"))
    )
    html = frappe.utils.escape_html(body).replace("\\n", "<br>")
    try:
        comment = frappe.get_doc(
            {
                "doctype": "Comment",
                "comment_type": "Comment",
                "reference_doctype": "HD Ticket",
                "reference_name": ticket.name,
                "reference_owner": ticket.owner,
                "content": html,
                "published": 0,
            }
        )
        comment.insert(ignore_permissions=True)
        clear_server_messages()
        return comment.name
    except Exception as exc:
        frappe.log_error(as_text(exc)[:500], SCRIPT_TITLE + " internal comment")
    clear_server_messages()
    return None
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


def doc_url(site: str, doctype: str, name: str) -> str:
    return (
        site.rstrip("/")
        + "/api/resource/"
        + requests.utils.quote(doctype, safe="")
        + "/"
        + requests.utils.quote(name, safe="")
    )


def main() -> int:
    site = env("HARAVAN_SITE").rstrip("/")
    api_key = env("HARAVAN_API_KEY")
    api_secret = env("HARAVAN_API_SECRET")

    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"token {api_key}:{api_secret}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
    )

    backup_dir = Path("backups") / f"ai_assist_fix_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    replacements = [
        ("HD Form Script", "AI - Ticket Assist Menu", ASSIST_MENU_SCRIPT),
        ("Server Script", "AI - Summary API", SUMMARY_SCRIPT),
        ("Server Script", "AI - Reply Suggest API", REPLY_SCRIPT),
        ("Server Script", "AI - Send Reply API", SEND_REPLY_SCRIPT),
    ]

    for doctype, name, script in replacements:
        url = doc_url(site, doctype, name)
        current = request(session, "GET", url)["data"]
        safe_name = f"{doctype}__{name}".replace(" ", "_").replace("/", "_")
        (backup_dir / f"{safe_name}_before.json").write_text(
            json.dumps(current, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        payload = {"script": script}
        if doctype == "HD Form Script":
            payload["enabled"] = 1
        else:
            payload["disabled"] = 0
        updated = request(session, "PUT", url, data=json.dumps(payload))["data"]
        (backup_dir / f"{safe_name}_after.json").write_text(
            json.dumps(updated, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    analyze_url = doc_url(site, "Server Script", "AI - Ticket Analyze API")
    current = request(session, "GET", analyze_url)["data"]
    analyze_script = current.get("script") or ""
    if ANALYZE_OLD_ADD_NOTE in analyze_script:
        analyze_script = analyze_script.replace(ANALYZE_OLD_ADD_NOTE, ANALYZE_NEW_ADD_NOTE)
    elif "def add_note(ticket, result, updated_fields, gemini_status, skipped_updates=None):" not in analyze_script:
        raise SystemExit("Could not locate analyze add_note block")

    analyze_script = analyze_script.replace(
        "        add_note(ticket, result, updated_fields, err)\n",
        "        internal_comment_id = add_note(ticket, result, updated_fields, err, skipped_updates)\n",
    )
    analyze_script = analyze_script.replace(
        "    else:\n        skipped_updates = {}\n    return {\"ticket\": ticket_name, \"dry_run\": dry_run, \"updated_fields\": updated_fields, \"proposed_updates\": proposed_updates, \"skipped_updates\": skipped_updates, \"reasoning\": result.get(\"reasoning\"), \"source\": result.get(\"source\"), \"gemini_status\": \"configured\" if not err else err}\n",
        "    else:\n        skipped_updates = {}\n        internal_comment_id = None\n    return {\"ticket\": ticket_name, \"dry_run\": dry_run, \"updated_fields\": updated_fields, \"proposed_updates\": proposed_updates, \"skipped_updates\": skipped_updates, \"internal_comment_id\": internal_comment_id, \"reasoning\": result.get(\"reasoning\"), \"source\": result.get(\"source\"), \"gemini_status\": \"configured\" if not err else err}\n",
    )
    analyze_script = analyze_script.replace("internal_communication_id", "internal_comment_id")
    analyze_script = analyze_script.replace(
        "try:\n    data = analyze_ticket(name, dry_run)\n    frappe.response[\"message\"] = {\"success\": True, \"data\": data, \"message\": \"AI đã làm giàu dữ liệu ticket thành công\"}\nexcept Exception as exc:\n",
        "try:\n    data = analyze_ticket(name, dry_run)\n    clear_server_messages()\n    frappe.response[\"message\"] = {\"success\": True, \"data\": data, \"message\": \"AI đã làm giàu dữ liệu ticket thành công\"}\nexcept Exception as exc:\n",
    )
    safe_name = "Server_Script__AI___Ticket_Analyze_API"
    (backup_dir / f"{safe_name}_before.json").write_text(
        json.dumps(current, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    updated = request(session, "PUT", analyze_url, data=json.dumps({"script": analyze_script, "disabled": 0}))["data"]
    (backup_dir / f"{safe_name}_after.json").write_text(
        json.dumps(updated, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Patched AI assist and analyze internal Comment. Backup: {backup_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
