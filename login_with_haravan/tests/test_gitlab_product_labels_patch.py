import unittest

from scripts.patch_gitlab_product_suggestion_labels import patch_form_script, patch_server_script


class TestGitLabProductLabelsPatch(unittest.TestCase):
    def test_form_script_uses_default_labels_from_init(self):
        source = """async function setupForm() {
        const defDesc = plainText(ticket.description || doc.description || doc.content || '');
        await api('create', {
                        labels: document.getElementById(`${id}-labels`)?.value || 'helpdesk,customer-report'
        });
        const html = `
                            <input id="${id}-labels" class="gl-input" type="text"
                                value="helpdesk,customer-report"
                                placeholder="Labels phân cách bởi dấu phẩy">
        `;
}"""

        patched = patch_form_script(source)

        self.assertIn("const defLabels = init.default_labels || 'helpdesk,customer-report';", patched)
        self.assertIn("labels: document.getElementById(`${id}-labels`)?.value || defLabels", patched)
        self.assertIn('value="${esc(defLabels)}"', patched)
        self.assertNotIn('value="helpdesk,customer-report"', patched)

    def test_server_script_reads_product_suggestion_gitlab_labels(self):
        source = '''TRACKER_DTYPE = "HD GitLab Tracker"
TICKET_DTYPE = "HD Ticket"

def as_text(value):
    return "" if value is None else str(value).strip()

def ticket_payload(ticket_name):
    ticket = frappe.get_doc(TICKET_DTYPE, ticket_name)
    return {
        "name": ticket.name,
        "subject": ticket.get("subject") or "",
        "description": ticket.get("description") or "",
        "status": ticket.get("status") or "",
    }

def get_tracker_by_ticket(ticket_name):
    return None

if action == "init":
    frappe.response["message"] = {"ok": True, "linked": linked, "ticket": ticket_payload(ticket_name), "tracker": tracker.name if tracker else None, "issue": issue, "comments": comments, "project_id": project_id, "project_path": gitlab_project_path()}

elif action == "create":
    labels = as_text(frappe.form_dict.get("labels") or "helpdesk,customer-report")
'''

        patched = patch_server_script(source)

        self.assertIn('PRODUCT_SUGGESTION_DOCTYPE = "HD Ticket Product Suggestion"', patched)
        self.assertIn('PRODUCT_SUGGESTION_FIELD = "custom_product_suggestion"', patched)
        self.assertIn('PRODUCT_SUGGESTION_LABEL_FIELD = "gitlab_labels"', patched)
        self.assertIn('frappe.db.get_value(TICKET_DTYPE, ticket_name, PRODUCT_SUGGESTION_FIELD)', patched)
        self.assertIn('frappe.db.get_value(PRODUCT_SUGGESTION_DOCTYPE, suggestion, PRODUCT_SUGGESTION_LABEL_FIELD)', patched)
        self.assertIn('"default_labels": gitlab_default_labels(ticket_name)', patched)
        self.assertIn('labels = as_text(frappe.form_dict.get("labels") or gitlab_default_labels(ticket_name) or BASE_GITLAB_LABELS)', patched)


if __name__ == "__main__":
    unittest.main()
