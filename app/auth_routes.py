"""Seiten für Anmeldung, 2FA, eigenes Konto und Benutzerverwaltung."""
from __future__ import annotations

import time

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from . import auth
from .config import settings
from .db import get_db
from .models import User

PENDING_SECONDS = 300  # Zeit für die Eingabe des 2FA-Codes nach dem Passwort


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "?"


def _start_session(request: Request, user: User) -> None:
    request.session.clear()
    request.session["uid"] = user.id
    request.session["epoch"] = user.session_epoch


def register_auth_routes(app: FastAPI, render, redirect) -> None:  # noqa: C901

    def me(db: Session, request: Request) -> User:
        u = request.state.user
        if u is None or u.id is None:
            raise HTTPException(404)
        return db.get(User, u.id)

    # ---------- Anmeldung ----------
    @app.get("/login", response_class=HTMLResponse)
    def login_form(request: Request, db: Session = Depends(get_db)):
        no_users = not db.scalar(select(func.count(User.id)))
        return render(request, "login.html", error=None, no_users=no_users)

    @app.post("/login")
    async def login(request: Request, db: Session = Depends(get_db)):
        form = await request.form()
        ip = _client_ip(request)
        if auth.ip_limiter.blocked(ip):
            return render(request, "login.html", no_users=False,
                          error="Zu viele Fehlversuche. Bitte in einigen Minuten erneut versuchen.")
        user, error = auth.check_credentials(db, str(form.get("username", "")),
                                             str(form.get("password", "")))
        if user is None:
            auth.ip_limiter.hit(ip)
            db.commit()
            return render(request, "login.html", error=error, no_users=False)
        if user.totp_enabled:
            request.session.clear()
            request.session["pending_uid"] = user.id
            request.session["pending_at"] = int(time.time())
            db.commit()
            return redirect("/login/2fa")
        auth.register_success(user)
        db.commit()
        _start_session(request, user)
        return redirect("/")

    def _pending(request: Request, db: Session) -> User | None:
        uid, at = request.session.get("pending_uid"), request.session.get("pending_at", 0)
        if not uid or time.time() - at > PENDING_SECONDS:
            return None
        u = db.get(User, uid)
        return u if u and u.active and u.totp_enabled else None

    @app.get("/login/2fa", response_class=HTMLResponse)
    def login_2fa_form(request: Request, db: Session = Depends(get_db)):
        if not _pending(request, db):
            return redirect("/login")
        return render(request, "login_2fa.html", error=None)

    @app.post("/login/2fa")
    async def login_2fa(request: Request, db: Session = Depends(get_db)):
        user = _pending(request, db)
        if user is None:
            request.session.clear()
            return redirect("/login")
        ip = _client_ip(request)
        if auth.ip_limiter.blocked(ip):
            return render(request, "login_2fa.html",
                          error="Zu viele Fehlversuche. Bitte in einigen Minuten erneut versuchen.")
        form = await request.form()
        code = str(form.get("code", "")).strip()
        step = auth.verify_totp(user.totp_secret, code, user.totp_last_step)
        ok = step is not None
        if ok:
            user.totp_last_step = step
        elif len(code.replace("-", "")) == 12:
            ok = auth.use_recovery_code(user, code)
        if not ok:
            auth.ip_limiter.hit(ip)
            auth.register_failure(user)
            if user.locked_until:
                request.session.clear()
            db.commit()
            return render(request, "login_2fa.html", error="Code ungültig.")
        auth.register_success(user)
        db.commit()
        _start_session(request, user)
        return redirect("/")

    @app.post("/logout")
    def logout(request: Request):
        request.session.clear()
        return redirect("/login" if settings.auth_enabled else "/")

    # ---------- Eigenes Konto ----------
    @app.get("/account", response_class=HTMLResponse)
    def account(request: Request, db: Session = Depends(get_db)):
        return render(request, "account.html", u=me(db, request), msg=None, error=None, roles=auth.ROLES)

    @app.post("/account/password")
    async def account_password(request: Request, db: Session = Depends(get_db)):
        u = me(db, request)
        form = await request.form()
        new = str(form.get("new", ""))
        error = None
        if not auth.verify_password(str(form.get("current", "")), u.password_hash):
            error = "Aktuelles Passwort falsch."
        elif new != form.get("confirm"):
            error = "Die neuen Passwörter stimmen nicht überein."
        else:
            error = auth.password_problem(new, u.username)
        if error:
            return render(request, "account.html", u=u, msg=None, error=error, roles=auth.ROLES)
        u.password_hash = auth.hash_password(new)
        u.session_epoch += 1  # andere Sitzungen abmelden
        db.commit()
        _start_session(request, u)
        return render(request, "account.html", u=u, msg="Passwort geändert. Andere Sitzungen "
                      "wurden abgemeldet.", error=None, roles=auth.ROLES)

    @app.get("/account/2fa", response_class=HTMLResponse)
    def account_2fa(request: Request, db: Session = Depends(get_db)):
        u = me(db, request)
        if u.totp_enabled:
            return redirect("/account")
        secret = request.session.get("totp_setup") or auth.new_totp_secret()
        request.session["totp_setup"] = secret
        uri = auth.totp_uri(secret, u.username)
        return render(request, "account_2fa.html", u=u, secret=secret, qr=auth.qr_svg(uri),
                      error=None, required=settings.require_2fa)

    @app.post("/account/2fa/confirm", response_class=HTMLResponse)
    async def account_2fa_confirm(request: Request, db: Session = Depends(get_db)):
        u = me(db, request)
        secret = request.session.get("totp_setup")
        if u.totp_enabled or not secret:
            return redirect("/account")
        form = await request.form()
        step = auth.verify_totp(secret, str(form.get("code", "")), None)
        if step is None:
            return render(request, "account_2fa.html", u=u, secret=secret,
                          qr=auth.qr_svg(auth.totp_uri(secret, u.username)),
                          error="Code ungültig. Uhrzeit des Handys prüfen und erneut versuchen.",
                          required=settings.require_2fa)
        codes, hashes = auth.new_recovery_codes()
        u.totp_secret, u.totp_enabled, u.totp_last_step = secret, True, step
        u.recovery_codes = hashes
        u.session_epoch += 1
        db.commit()
        request.session.pop("totp_setup", None)
        _start_session(request, u)
        return render(request, "recovery_codes.html", codes=codes)

    @app.post("/account/2fa/disable")
    async def account_2fa_disable(request: Request, db: Session = Depends(get_db)):
        u = me(db, request)
        form = await request.form()
        if settings.require_2fa:
            return render(request, "account.html", u=u, msg=None, roles=auth.ROLES,
                          error="2FA ist auf diesem Server Pflicht.")
        if not auth.verify_password(str(form.get("current", "")), u.password_hash):
            return render(request, "account.html", u=u, msg=None, roles=auth.ROLES,
                          error="Passwort falsch.")
        u.totp_enabled, u.totp_secret, u.recovery_codes = False, None, []
        db.commit()
        return redirect("/account")

    @app.post("/account/recovery", response_class=HTMLResponse)
    async def account_recovery(request: Request, db: Session = Depends(get_db)):
        u = me(db, request)
        form = await request.form()
        if not u.totp_enabled or not auth.verify_password(str(form.get("current", "")),
                                                          u.password_hash):
            return render(request, "account.html", u=u, msg=None, roles=auth.ROLES,
                          error="Passwort falsch.")
        codes, u.recovery_codes = auth.new_recovery_codes()
        db.commit()
        return render(request, "recovery_codes.html", codes=codes)

    # ---------- Benutzerverwaltung (nur Admin) ----------
    def users_page(request, db, msg=None, error=None):
        users = list(db.scalars(select(User).order_by(User.username)))
        return render(request, "users.html", users=users, roles=auth.ROLES, msg=msg, error=error)

    @app.get("/users", response_class=HTMLResponse)
    def users(request: Request, db: Session = Depends(get_db)):
        return users_page(request, db)

    @app.post("/users", response_class=HTMLResponse)
    async def user_create(request: Request, db: Session = Depends(get_db)):
        form = await request.form()
        try:
            u = auth.create_user(db, str(form.get("username", "")), str(form.get("password", "")),
                                 str(form.get("role", "viewer")))
        except ValueError as e:
            return users_page(request, db, error=str(e))
        db.commit()
        return users_page(request, db, msg=f"Benutzer {u.username} angelegt. Die 2FA wird beim "
                          "ersten Login eingerichtet.")

    @app.post("/users/{uid}", response_class=HTMLResponse)
    async def user_update(uid: int, request: Request, db: Session = Depends(get_db)):
        u = db.get(User, uid)
        if not u:
            raise HTTPException(404)
        form = await request.form()
        action = form.get("action")
        self_ = u.id == request.state.user.id
        last_admin = u.role == "admin" and u.active and auth.admin_count(db) <= 1
        if action == "role":
            role = str(form.get("role"))
            if role not in auth.ROLES:
                return users_page(request, db, error="Ungültige Rolle.")
            if last_admin and role != "admin":
                return users_page(request, db, error="Der letzte Administrator kann nicht "
                                  "herabgestuft werden.")
            u.role = role
            u.session_epoch += 1
            msg = f"Rolle von {u.username}: {auth.ROLES[role]}."
        elif action == "toggle":
            if self_ or (last_admin and u.active):
                return users_page(request, db, error="Dieses Konto kann nicht deaktiviert werden.")
            u.active = not u.active
            u.session_epoch += 1
            msg = f"{u.username} {'aktiviert' if u.active else 'deaktiviert'}."
        elif action == "password":
            pw = str(form.get("password", ""))
            if problem := auth.password_problem(pw, u.username):
                return users_page(request, db, error=problem)
            u.password_hash = auth.hash_password(pw)
            u.session_epoch += 1
            msg = f"Passwort von {u.username} gesetzt."
        elif action == "reset2fa":
            u.totp_enabled, u.totp_secret, u.recovery_codes = False, None, []
            u.session_epoch += 1
            msg = f"2FA von {u.username} zurückgesetzt."
        elif action == "unlock":
            u.failed_logins, u.locked_until = 0, None
            msg = f"{u.username} entsperrt."
        elif action == "delete":
            if self_ or last_admin:
                return users_page(request, db, error="Dieses Konto kann nicht gelöscht werden.")
            db.delete(u)
            msg = "Benutzer gelöscht."
        else:
            raise HTTPException(400)
        db.commit()
        if self_:
            _start_session(request, u)
        return users_page(request, db, msg=msg)
