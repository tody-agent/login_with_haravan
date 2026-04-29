from urllib.parse import unquote, urlparse, urlunparse


DEFAULT_HELPDESK_REDIRECT = "/helpdesk/my-tickets"


def normalize_helpdesk_redirect(redirect_to: str | None) -> str:
    if not redirect_to:
        return DEFAULT_HELPDESK_REDIRECT

    value = unquote(str(redirect_to).strip())
    if not value:
        return DEFAULT_HELPDESK_REDIRECT

    parsed = urlparse(value)
    path = parsed.path or ""
    if not path.startswith("/"):
        path = f"/{path}"

    if not _is_clear_ticket_route(path):
        return DEFAULT_HELPDESK_REDIRECT

    return urlunparse(("", "", path, "", parsed.query, parsed.fragment))


def _is_clear_ticket_route(path: str) -> bool:
    return path == DEFAULT_HELPDESK_REDIRECT or path.startswith(f"{DEFAULT_HELPDESK_REDIRECT}/")
