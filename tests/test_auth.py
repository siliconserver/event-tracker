import datetime as dt

import pytest
from sqlalchemy import select

from app import auth
from app import db as dbmod
from app.models import User

PW = "sehr-geheim-123"


@pytest.fixture()
def secured(client, monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "auth_enabled", True)
    with dbmod.SessionLocal() as db:
        for name, role in (("admin", "admin"), ("schreiber", "editor"), ("leser", "viewer")):
            auth.create_user(db, name, PW, role)
        db.commit()
    return client


def login(client, name, pw=PW):
    return client.post("/login", data={"username": name, "password": pw}, follow_redirects=False)


def setup_2fa(client):
    r = client.get("/account/2fa")
    assert r.status_code == 200 and "<svg" in r.text
    import re
    secret = re.search(r"<code[^>]*>([A-Z2-7]+)</code>", r.text).group(1)
    r = client.post("/account/2fa/confirm", data={"code": auth.totp_now(secret)})
    assert "Wiederherstellungscodes" in r.text
    codes = re.findall(r"<li>([0-9A-F]{6}-[0-9A-F]{6})</li>", r.text)
    assert len(codes) == 8
    return secret, codes


def test_totp_matches_rfc6238_vector():
    # RFC 6238, SHA-1, Schlüssel "12345678901234567890", T=59 -> 94287082 (8 Stellen) -> 287082
    import base64
    secret = base64.b32encode(b"12345678901234567890").decode()
    assert auth.totp_now(secret, at=59) == "287082"
    assert auth.verify_totp(secret, "287082", None, at=59) == 1
    assert auth.verify_totp(secret, "287082", 1, at=59) is None  # Wiederverwendung blockiert


def test_password_hashing():
    h = auth.hash_password("abcdefghijk")
    assert h.startswith("scrypt$") and auth.verify_password("abcdefghijk", h)
    assert not auth.verify_password("falsch", h)
    assert auth.password_problem("kurz") is not None


def test_requires_login_and_2fa_setup(secured):
    assert secured.get("/events", follow_redirects=False).headers["location"] == "/login"
    assert secured.get("/health").status_code == 200
    assert secured.get("/static/style.css").status_code == 200
    assert login(secured, "admin", "falsch").status_code == 200
    r = login(secured, "admin")
    assert r.status_code == 303
    # 2FA ist Pflicht -> erst einrichten
    assert secured.get("/events", follow_redirects=False).headers["location"] == "/account/2fa"
    secret, codes = setup_2fa(secured)
    assert secured.get("/events").status_code == 200
    # Neu anmelden: Passwort + Code
    secured.post("/logout")
    r = login(secured, "admin")
    assert r.headers["location"] == "/login/2fa"
    assert secured.get("/events", follow_redirects=False).headers["location"] == "/login"
    assert "Code ungültig" in secured.post("/login/2fa", data={"code": "000000"}).text
    with dbmod.SessionLocal() as db:
        last = db.scalar(select(User).where(User.username == "admin")).totp_last_step
    # derselbe Code wie bei der Einrichtung ist verbraucht, daher Wiederherstellungscode nutzen
    r = secured.post("/login/2fa", data={"code": codes[0]}, follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/"
    assert secured.get("/events").status_code == 200
    # Wiederherstellungscode ist nur einmal gültig
    secured.post("/logout")
    login(secured, "admin")
    assert "Code ungültig" in secured.post("/login/2fa", data={"code": codes[0]}).text
    assert last is not None


def test_roles(secured, monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "require_2fa", False)
    login(secured, "leser")
    assert secured.get("/events").status_code == 200
    assert secured.post("/venues/new", data={"name": "X"}).status_code == 403
    assert secured.get("/users").status_code == 403
    assert secured.get("/export.json").status_code == 403
    assert "readonly.js" in secured.get("/").text
    # eigenes Passwort darf ein Leser ändern
    r = secured.post("/account/password", data={"current": PW, "new": "neues-passwort-1",
                                                 "confirm": "neues-passwort-1"})
    assert "Passwort geändert" in r.text
    secured.post("/logout")
    login(secured, "schreiber")
    assert secured.post("/venues/new", data={"name": "Waldstadion"},
                        follow_redirects=False).status_code == 303
    assert secured.get("/users").status_code == 403
    export = secured.get("/export.json").json()
    assert "app_user" not in export["tables"]
    secured.post("/logout")
    login(secured, "admin")
    r = secured.post("/users", data={"username": "neu", "password": "passwort-neu-1",
                                     "role": "viewer"})
    assert "angelegt" in r.text
    with dbmod.SessionLocal() as db:
        uid = db.scalar(select(User.id).where(User.username == "neu"))
        aid = db.scalar(select(User.id).where(User.username == "admin"))
    secured.post(f"/users/{uid}", data={"action": "role", "role": "editor"})
    with dbmod.SessionLocal() as db:
        assert db.get(User, uid).role == "editor"
    r = secured.post(f"/users/{aid}", data={"action": "role", "role": "viewer"})
    assert "letzte Administrator" in r.text
    assert "nicht gelöscht" in secured.post(f"/users/{aid}", data={"action": "delete"}).text


def test_session_invalidated_on_deactivate(secured, monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "require_2fa", False)
    login(secured, "schreiber")
    assert secured.get("/events").status_code == 200
    with dbmod.SessionLocal() as db:
        u = db.scalar(select(User).where(User.username == "schreiber"))
        u.active = False
        u.session_epoch += 1
        db.commit()
    assert secured.get("/events", follow_redirects=False).status_code == 303


def test_lockout_and_ip_limit(secured):
    for _ in range(auth.MAX_FAILED):
        login(secured, "leser", "falsch")
    r = login(secured, "leser")  # richtiges Passwort, aber gesperrt
    assert "gesperrt" in r.text
    with dbmod.SessionLocal() as db:
        u = db.scalar(select(User).where(User.username == "leser"))
        assert u.locked_until > dt.datetime.now()
    for _ in range(10):
        login(secured, "gibtsnicht", "x")
    assert "Zu viele Fehlversuche" in login(secured, "admin").text


def test_cross_origin_post_rejected(secured, monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "require_2fa", False)
    login(secured, "schreiber")
    r = secured.post("/venues/new", data={"name": "Y"}, headers={"Origin": "https://evil.example"})
    assert r.status_code == 403
    r = secured.post("/venues/new", data={"name": "Y"}, headers={"Origin": "http://testserver"},
                     follow_redirects=False)
    assert r.status_code == 303


def test_security_headers_and_auth_off(client):
    r = client.get("/")
    assert r.headers["x-frame-options"] == "DENY"
    # Anmeldung aus (NAS): alles erreichbar, keine Login-Seite
    assert client.get("/login", follow_redirects=False).status_code == 303
    assert client.post("/venues/new", data={"name": "Z"}, follow_redirects=False).status_code == 303


def test_cli_create_user(tmp_path, monkeypatch, client):
    from app import cli
    cli.main(["create-user", "christian", "--role", "admin", "--password", "langes-passwort"])
    with dbmod.SessionLocal() as db:
        assert db.scalar(select(User).where(User.username == "christian")).role == "admin"
