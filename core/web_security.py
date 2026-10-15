"""
Browser-facing security settings for the web app (homelab fork hardening).

The socket handlers do the app's real work, so the socket must not be reachable from another
origin riding the user's session cookie. These are kept here, rather than inline in the
startup code, so they can be tested.
"""

from typing import List, Optional


def socketio_cors_origins(config) -> Optional[List[str]]:
    """Origins allowed to open the Socket.IO connection.

    None makes python-engineio accept only the server's own origin. A configured external_url
    (the app behind a reverse proxy) is allowed as well.
    """
    external_url = (getattr(config, "external_url", "") or "").strip().rstrip("/")
    return [external_url] if external_url else None


def configure_session_cookie(web_app) -> None:
    """SameSite=Lax keeps the session cookie off cross-site requests, socket handshakes included."""
    web_app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    web_app.config["SESSION_COOKIE_HTTPONLY"] = True
