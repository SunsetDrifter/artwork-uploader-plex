"""
Homelab fork: secrets stay out of the browser where it does not need them, and out of logs.

- save_config copied every key the client sent onto the Config object, so {"path": ...}
  pointed the next config write at any file, and {"save": 1} broke the config until restart.
- load_config/save_config/update_ui sent vars(config), bcrypt hash included, to the page.
- notify_web debug-printed every payload, so debug mode wrote the Plex token, the hash, the
  OIDC client secret, the webhook token and Apprise URLs to the container log.
- Apprise URLs embed bot tokens and were logged on every notification.
"""

import pytest

from core.config import Config
from utils.secret_redaction import (
    browser_config,
    describe_apprise_url,
    filter_client_config,
    redact_for_log,
)


@pytest.mark.unit
def test_client_config_keeps_real_settings_and_the_new_password():
    kept = filter_client_config({"base_url": "http://plex:32400", "token": "abc", "auth_password": "pw"})

    assert kept == {"base_url": "http://plex:32400", "token": "abc", "auth_password": "pw"}


@pytest.mark.unit
@pytest.mark.parametrize("key", ["path", "auth_password_hash", "save", "load", "__class__", "made_up_key"])
def test_client_config_drops_keys_that_are_not_settings(key):
    assert key not in filter_client_config({key: "/etc/passwd", "base_url": "x"})


@pytest.mark.unit
def test_the_browser_never_gets_the_password_hash():
    config = Config()
    config.auth_password_hash = "$2b$12$abcdefghijklmnopqrstuv"
    config.token = "plex-token-value-12345"

    sent = browser_config(config)

    assert "auth_password_hash" not in sent
    assert sent["token"] == "plex-token-value-12345"  # the settings form edits it
    assert config.auth_password_hash  # the live config is untouched


@pytest.mark.unit
def test_logged_payloads_mask_every_secret():
    payload = {"config": {
        "token": "plex-token", "auth_password_hash": "$2b$hash", "oidc_client_secret": "oidc-secret-value",
        "webhook_token": "hook-secret-value", "apprise_urls": [{"url": "tgram://bot/chat"}], "base_url": "http://plex",
    }, "instance_id": "abc"}

    logged = redact_for_log(payload)

    text = repr(logged)
    for secret in ("plex-token", "$2b$hash", "oidc-secret-value", "hook-secret-value", "tgram://bot/chat"):
        assert secret not in text
    assert logged["config"]["base_url"] == "http://plex"
    assert payload["config"]["token"] == "plex-token"  # the emitted payload is untouched


@pytest.mark.unit
@pytest.mark.parametrize("url,expected", [
    ("tgram://123456:SECRETTOKEN/987", "tgram://…"),
    ("discord://webhook_id/webhook_token", "discord://…"),
    ("not a url", "[notification channel]"),
    ("", "[notification channel]"),
])
def test_apprise_urls_are_logged_by_scheme_only(url, expected):
    assert describe_apprise_url(url) == expected
