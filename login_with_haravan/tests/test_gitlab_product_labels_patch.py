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

        self.assertIn("const defLabels = init.default_labels || '';", patched)
        self.assertIn("const defAssigneeIds = init.default_assignee_ids || '';", patched)
        self.assertIn("const defProjectId = init.default_project_id || '';", patched)
        self.assertIn("labels: document.getElementById(`${id}-labels`)?.value || defLabels", patched)
        self.assertIn("assignee_ids: document.getElementById(`${id}-assignee-ids`)?.value || defAssigneeIds", patched)
        self.assertIn("project_id: document.getElementById(`${id}-project-id`)?.value || defProjectId", patched)
        self.assertIn('value="${esc(defLabels)}"', patched)
        self.assertIn('value="${esc(defAssigneeIds)}"', patched)
        self.assertIn('value="${esc(defProjectId)}"', patched)
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
    issue = api_post("/projects/" + project_id + "/issues", {"title": title, "description": full_description, "labels": labels})
'''

        patched = patch_server_script(source)

        self.assertIn('PRODUCT_SUGGESTION_DOCTYPE = "HD Ticket Product Suggestion"', patched)
        self.assertIn('PRODUCT_SUGGESTION_FIELD = "custom_product_suggestion"', patched)
        self.assertIn('PRODUCT_SUGGESTION_LABEL_FIELD = "gitlab_labels"', patched)
        self.assertIn('PRODUCT_SUGGESTION_ASSIGN_FIELD = "assign_to"', patched)
        self.assertIn('PRODUCT_SUGGESTION_PROJECT_ID_FIELD = "default_gitlab_projectid"', patched)
        self.assertIn('TICKET_INTERNAL_TYPE_FIELDS = ["custom_internal_type", "ticket_type"]', patched)
        self.assertIn('"urgent": "P1_Urgent"', patched)
        self.assertIn('"high": "P2_High"', patched)
        self.assertIn('"medium": "P3_Medium"', patched)
        self.assertIn('"low": "P4_Low"', patched)
        self.assertIn('frappe.db.get_value(TICKET_DTYPE, ticket_name, PRODUCT_SUGGESTION_FIELD)', patched)
        self.assertIn('frappe.db.get_value(PRODUCT_SUGGESTION_DOCTYPE, suggestion, PRODUCT_SUGGESTION_LABEL_FIELD)', patched)
        self.assertIn('def internal_type_labels(ticket_name):', patched)
        self.assertIn('def ticket_priority_label(ticket_name):', patched)
        self.assertIn('frappe.db.get_value(TICKET_DTYPE, ticket_name, "priority")', patched)
        self.assertIn('return ["Bug"]', patched)
        self.assertIn('return ["Support"]', patched)
        self.assertIn('return ["API_Support"]', patched)
        self.assertIn('product_suggestion_labels(ticket_name) + internal_type_labels(ticket_name) + ([priority_label] if priority_label else [])', patched)
        self.assertIn('"default_labels": gitlab_default_labels(ticket_name)', patched)
        self.assertIn('"default_assignee_ids": gitlab_default_assignee_ids(ticket_name)', patched)
        self.assertIn('"default_project_id": gitlab_default_project_id(ticket_name)', patched)
        self.assertIn('labels = as_text(frappe.form_dict.get("labels") or gitlab_default_labels(ticket_name))', patched)
        self.assertIn('create_project_id = as_text(frappe.form_dict.get("project_id") or gitlab_default_project_id(ticket_name) or project_id)', patched)
        self.assertIn('create_payload["assignee_ids"] = [int(value) for value in assignee_ids]', patched)
        self.assertIn('api_post("/projects/" + create_project_id + "/issues", create_payload)', patched)
        self.assertNotIn("split_labels(BASE_GITLAB_LABELS)", patched)

    def test_server_script_adds_priority_label_without_duplicate_function(self):
        source = '''TRACKER_DTYPE = "HD GitLab Tracker"
TICKET_DTYPE = "HD Ticket"
PRODUCT_SUGGESTION_DOCTYPE = "HD Ticket Product Suggestion"
PRODUCT_SUGGESTION_FIELD = "custom_product_suggestion"
PRODUCT_SUGGESTION_LABEL_FIELD = "gitlab_labels"
PRODUCT_SUGGESTION_ASSIGN_FIELD = "assign_to"
PRODUCT_SUGGESTION_PROJECT_ID_FIELD = "default_gitlab_projectid"
TICKET_INTERNAL_TYPE_FIELDS = ["custom_internal_type", "ticket_type"]

def as_text(value):
    return "" if value is None else str(value).strip()

def split_labels(value):
    return []

def product_suggestion_labels(ticket_name):
    return []

def internal_type_labels(ticket_name):
    value = ticket_internal_type(ticket_name).lower()
    if value == "system bug / incident":
        return ["Bug"]
    if value == "technical support":
        return ["Support"]
    if value == "api support":
        return ["API_Support"]
    return []

def ticket_internal_type(ticket_name):
    return ""

def gitlab_default_labels(ticket_name):
    labels = []
    for label in product_suggestion_labels(ticket_name) + internal_type_labels(ticket_name):
        if label not in labels:
            labels.append(label)
    return ",".join(labels)

def product_suggestion_value(ticket_name, fieldname):
    return ""

def gitlab_default_assignee_ids(ticket_name):
    return ""

def gitlab_default_project_id(ticket_name):
    return ""

def ticket_payload(ticket_name):
    return {"status": ""}

if action == "init":
    frappe.response["message"] = {"ok": True, "linked": linked, "ticket": ticket_payload(ticket_name), "tracker": tracker.name if tracker else None, "issue": issue, "comments": comments, "project_id": project_id, "project_path": gitlab_project_path()}

elif action == "create":
    labels = as_text(frappe.form_dict.get("labels") or "helpdesk,customer-report")
    issue = api_post("/projects/" + project_id + "/issues", {"title": title, "description": full_description, "labels": labels})
'''

        patched = patch_server_script(source)

        self.assertEqual(patched.count("def ticket_priority_label(ticket_name):"), 1)
        self.assertIn("PRIORITY_LABELS", patched)
        self.assertIn('frappe.db.get_value(TICKET_DTYPE, ticket_name, "priority")', patched)
        self.assertIn("([priority_label] if priority_label else [])", patched)


if __name__ == "__main__":
    unittest.main()
