"""
Keep secrets out of places that do not need them (homelab fork hardening).

The config holds the Plex admin token, the bcrypt hash of the web password, the OIDC client
secret, the webhook token and Apprise URLs (which embed bot tokens). See
tests/test_secret_redaction.py for what each helper closes.
"""

import copy
from typing import Any, Dict
from urllib.parse import urlsplit

SECRET_CONFIG_KEYS = frozenset({
    "token", "auth_password_hash", "oidc_client_secret", "webhook_token", "apprise_urls",
})
_MASK = "***"
# Never settable from the browser: where the config is written, and the stored hash
# (a new password arrives as auth_password and is hashed server side).
_NOT_CLIENT_SETTABLE = frozenset({"path", "auth_password_hash"})


def filter_client_config(client_config: Dict[str, Any]) -> Dict[str, Any]:
    """Return only the keys of a browser-sent config that are real, client-settable settings."""
    from core.config import Config  # imported here: core.config sits below utils in the import graph

    allowed = (set(vars(Config())) - _NOT_CLIENT_SETTABLE) | {"auth_password"}
    return {key: value for key, value in client_config.items() if key in allowed}


def browser_config(config) -> Dict[str, Any]:
    """The config as sent to the page: everything the settings form edits, minus the hash."""
    sent = dict(vars(config))
    sent.pop("auth_password_hash", None)
    return sent


def redact_for_log(payload: Any) -> Any:
    """A copy of a socket payload with every secret config value masked, for debug logging."""
    if not isinstance(payload, dict):
        return payload
    redacted = copy.deepcopy(payload)
    stack = [redacted]
    while stack:
        current = stack.pop()
        for key, value in current.items():
            if key in SECRET_CONFIG_KEYS and value:
                current[key] = _MASK
            elif isinstance(value, dict):
                stack.append(value)
    return redacted


def describe_apprise_url(url: str) -> str:
    """Name a notification channel in a log line without its credentials."""
    scheme = urlsplit(url or "").scheme if "://" in (url or "") else ""
    return f"{scheme}://…" if scheme else "[notification channel]"
