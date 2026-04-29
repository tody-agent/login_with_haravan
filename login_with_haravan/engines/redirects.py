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

    if not path.startswith("/helpdesk"):
        return DEFAULT_HELPDESK_REDIRECT

    return urlunparse((parsed.scheme, parsed.netloc, path, "", parsed.query, parsed.fragment))
