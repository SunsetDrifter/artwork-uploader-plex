"""
Homelab fork: a page on another origin cannot open the app's socket with the user's session.

SocketIO used to be built with cors_allowed_origins="*", and the session cookie had no
SameSite attribute, so the session cookie was the only thing between another page and every
socket handler (load_config returns the Plex token). The socket now accepts only its own
origin, or external_url when one is configured, and the cookie is SameSite=Lax.
"""

import pytest
from flask import Flask
from flask_socketio import SocketIO

from core.web_security import configure_session_cookie, socketio_cors_origins


class _Config:
    def __init__(self, external_url=""):
        self.external_url = external_url


@pytest.mark.unit
def test_no_external_url_means_same_origin_only():
    assert socketio_cors_origins(_Config()) is None


@pytest.mark.unit
def test_an_external_url_is_the_only_extra_origin():
    assert socketio_cors_origins(_Config("https://posters.example.org/")) == ["https://posters.example.org"]


@pytest.mark.unit
def test_the_session_cookie_is_same_site_lax_and_http_only():
    app = Flask("cookie_test")
    configure_session_cookie(app)

    assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"
    assert app.config["SESSION_COOKIE_HTTPONLY"] is True


def _handshake(origin):
    app = Flask("origin_test")
    app.config["SECRET_KEY"] = "test"
    SocketIO(app, async_mode="threading", cors_allowed_origins=socketio_cors_origins(_Config()))
    return app.test_client().get(
        "/socket.io/?EIO=4&transport=polling",
        headers={"Origin": origin, "Host": "100.109.122.35:4567"},
    )


@pytest.mark.unit
def test_a_foreign_origin_handshake_is_refused():
    assert _handshake("https://evil.example").status_code == 400


@pytest.mark.unit
def test_a_same_origin_handshake_is_accepted():
    assert _handshake("http://100.109.122.35:4567").status_code == 200
