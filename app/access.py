"""Zugriffskontrolle für jede Anfrage: Anmeldung, 2FA-Pflicht, Rollen, Herkunftsprüfung."""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit

from fastapi import Request
from fastapi.responses import PlainTextResponse, RedirectResponse

from . import db as dbmod
from .config import settings
from .models import User

PUBLIC = ("/static/", "/health")
LOGIN_PATHS = ("/login", "/login/2fa")
# erreichbar für angemeldete Benutzer, die 2FA noch einrichten müssen
SETUP_PATHS = ("/account/2fa", "/account/2fa/confirm", "/logout")
# schreibende Anfragen, die auch Lese-Benutzer stellen dürfen (eigenes Konto)
READONLY_ALLOWED = ("/logout", "/account/password", "/account/2fa", "/account/2fa/confirm",
                    "/account/2fa/disable", "/account/recovery")
SAFE_METHODS = ("GET", "HEAD", "OPTIONS")


@dataclass(frozen=True)
class Anonymous:
    """Benutzer, wenn die Anmeldung abgeschaltet ist (AUTH_ENABLED=false, z. B. NAS hinter VPN)."""

    id: None = None
    username: str = ""
    role: str = "admin"
    can_write: bool = True
    is_admin: bool = True
    totp_enabled: bool = False


ANONYMOUS = Anonymous()


def session_user(request: Request) -> User | None:
    uid = request.session.get("uid")
    if not uid:
        return None
    with dbmod.SessionLocal() as db:
        u = db.get(User, uid)
        if u is None or not u.active or u.session_epoch != request.session.get("epoch"):
            request.session.clear()
            return None
        db.expunge(u)
        return u


def _same_origin(request: Request) -> bool:
    origin = request.headers.get("origin") or request.headers.get("referer")
    if not origin:
        return True  # ältere Clients/Formulare ohne Header; SameSite=Lax schützt zusätzlich
    host = request.headers.get("x-forwarded-host") or request.headers.get("host", "")
    return urlsplit(origin).netloc == host.split(",")[0].strip()


def check_access(request: Request):
    path = request.url.path
    request.state.user = None
    if path.startswith(PUBLIC):
        return None
    if request.method not in SAFE_METHODS and not _same_origin(request):
        return PlainTextResponse("Anfrage von fremder Herkunft abgelehnt.", status_code=403)

    if not settings.auth_enabled:
        request.state.user = ANONYMOUS
        if path.startswith(("/login", "/account", "/users")):
            return RedirectResponse("/", 303)
        return None

    if path in LOGIN_PATHS:
        return None
    user = session_user(request)
    if user is None:
        return RedirectResponse("/login", 303)
    request.state.user = user

    if settings.require_2fa and not user.totp_enabled and path not in SETUP_PATHS:
        return RedirectResponse("/account/2fa", 303)
    if request.method not in SAFE_METHODS and not user.can_write and path not in READONLY_ALLOWED:
        return PlainTextResponse("Nur Lesezugriff.", status_code=403)
    if path.startswith("/users") and not user.is_admin:
        return PlainTextResponse("Nur für Administratoren.", status_code=403)
    if path == "/export.json" and not user.can_write:
        return PlainTextResponse("Export nur mit Schreibrecht.", status_code=403)
    return None
