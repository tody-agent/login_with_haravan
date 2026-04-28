import frappe
from frappe.model.document import Document

from login_with_haravan.engines.haravan_identity import make_link_name


class HaravanAccountLink(Document):
    def autoname(self):
        self.name = make_link_name(self.haravan_orgid, self.haravan_userid)

    def validate(self):
        if self.email:
            self.email = self.email.lower()
        if not self.user and self.email and frappe.db.exists("User", self.email):
            self.user = self.email
