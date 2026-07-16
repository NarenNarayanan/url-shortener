"""
Parses a raw User-Agent string once, at write time — see the Click model's
docstring: doing this here means analytics queries never have to re-parse a
UA string themselves.
"""
from user_agents import parse as _parse_ua


def parse_user_agent(user_agent: str | None) -> tuple[str | None, str | None, str | None]:
    """Returns (browser, os, device_type), any of which may be None for a blank/unparseable UA."""
    if not user_agent:
        return None, None, None

    ua = _parse_ua(user_agent)
    browser = ua.browser.family or None
    os_name = ua.os.family or None

    if ua.is_mobile:
        device_type = "mobile"
    elif ua.is_tablet:
        device_type = "tablet"
    elif ua.is_pc:
        device_type = "desktop"
    else:
        device_type = "other"

    return browser, os_name, device_type
