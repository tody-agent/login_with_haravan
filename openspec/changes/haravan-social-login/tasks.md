# Implementation Checklist

- [x] Package Frappe app as standalone repo/folder.
- [x] Add `hooks.py`, `modules.txt`, and `patches.txt` for Frappe Cloud validation.
- [x] Keep Python metadata name as `login_with_haravan`.
- [x] Implement Haravan OAuth callback.
- [x] Implement Haravan identity normalization engine.
- [x] Implement `Haravan Account Link` DocType.
- [x] Implement Social Login Key setup helper.
- [x] Add local tests for identity normalization.
- [x] Add Frappe Cloud deployment guide.
- [x] Add troubleshooting for Frappe Cloud package validation.
- [x] Add troubleshooting for Haravan `invalid redirect_uri`.
- [ ] Confirm Haravan Partner Dashboard redirect URL in production.
- [ ] Confirm Frappe Social Login Key values in production.
- [ ] Complete end-to-end login test.
- [ ] Verify `Haravan Account Link` records after login.
