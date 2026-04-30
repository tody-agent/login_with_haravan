"""HD Ticket extensions for Haravan Helpdesk behavior."""

from __future__ import annotations

import frappe

from login_with_haravan.engines.ticket_cc import (
    InvalidCCEmailError,
    TICKET_CC_FIELD,
    merge_cc_email_text,
)


class HDTicketCCMixin:
    """Merge ticket-level CC recipients into Helpdesk outgoing emails."""

    def _merged_ticket_cc(self, existing_cc=None, recipients=None) -> str:
        try:
            return merge_cc_email_text(
                ticket_cc=getattr(self, TICKET_CC_FIELD, None),
                existing_cc=existing_cc,
                recipients=recipients,
            )
        except InvalidCCEmailError as exc:
            frappe.throw("Invalid CC Emails: " + ", ".join(exc.invalid_emails))
            return ""

    @frappe.whitelist()
    def reply_via_agent(
        self,
        message: str,
        to: str | None = None,
        cc: str | None = None,
        bcc: str | None = None,
        attachments: list[str] | None = None,
    ):
        recipients = to or getattr(self, "raised_by", None)
        merged_cc = self._merged_ticket_cc(existing_cc=cc, recipients=recipients)
        return super().reply_via_agent(
            message=message,
            to=to,
            cc=merged_cc or None,
            bcc=bcc,
            attachments=attachments or [],
        )

    def send_acknowledgement_email(self):
        recipients = [self.raised_by]
        merged_cc = self._merged_ticket_cc(recipients=recipients)
        if not merged_cc:
            return super().send_acknowledgement_email()

        from helpdesk.helpdesk.doctype.hd_settings.helpers import get_default_email_content

        acknowledgement_email_content = frappe.db.get_single_value(
            "HD Settings", "acknowledgement_email_content"
        )
        default_acknowledgement_email_content = get_default_email_content(
            "acknowledgement"
        )

        try:
            frappe.sendmail(
                recipients=recipients,
                cc=merged_cc,
                subject=frappe._("Ticket #{0}: We've received your request").format(
                    self.name
                ),
                message=self._get_rendered_template(
                    acknowledgement_email_content,
                    default_acknowledgement_email_content,
                ),
                reference_doctype="HD Ticket",
                reference_name=self.name,
                now=True,
                expose_recipients="header",
                email_headers={"X-Auto-Generated": "hd-acknowledgement"},
            )
        except Exception as exc:
            frappe.throw(
                frappe._("Could not send an acknowledgement email due to: {0}").format(exc)
            )
