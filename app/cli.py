"""Kommandozeile für die Benutzerverwaltung, z. B. im Container:

    docker exec -it event-tracker python -m app.cli create-user christian --role admin
    docker exec -it event-tracker python -m app.cli reset-2fa christian
    docker exec -it event-tracker python -m app.cli set-password christian
    docker exec -it event-tracker python -m app.cli list-users
"""
from __future__ import annotations

import argparse
import getpass
import sys

from sqlalchemy import func, select

from . import auth
from . import db as dbmod
from .models import User


def _password(args) -> str:
    if getattr(args, "password", None):
        return args.password
    pw = getpass.getpass("Passwort: ")
    if pw != getpass.getpass("Passwort wiederholen: "):
        sys.exit("Passwörter stimmen nicht überein.")
    return pw


def _user(db, name: str) -> User:
    u = db.scalar(select(User).where(func.lower(User.username) == name.lower()))
    if not u:
        sys.exit(f"Benutzer {name} nicht gefunden.")
    return u


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="python -m app.cli")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("create-user")
    c.add_argument("username")
    c.add_argument("--role", choices=list(auth.ROLES), default="viewer")
    c.add_argument("--password", help="nur für Skripte; sonst interaktiv")
    s = sub.add_parser("set-password")
    s.add_argument("username")
    s.add_argument("--password")
    r = sub.add_parser("reset-2fa")
    r.add_argument("username")
    u = sub.add_parser("unlock")
    u.add_argument("username")
    sub.add_parser("list-users")
    args = p.parse_args(argv)

    dbmod.init_engine()
    with dbmod.SessionLocal() as db:
        if args.cmd == "create-user":
            try:
                user = auth.create_user(db, args.username, _password(args), args.role)
            except ValueError as e:
                sys.exit(str(e))
            print(f"Benutzer {user.username} ({auth.ROLES[user.role]}) angelegt.")
        elif args.cmd == "set-password":
            user = _user(db, args.username)
            pw = _password(args)
            if problem := auth.password_problem(pw, user.username):
                sys.exit(problem)
            user.password_hash = auth.hash_password(pw)
            user.session_epoch += 1
            print("Passwort gesetzt, bestehende Sitzungen beendet.")
        elif args.cmd == "reset-2fa":
            user = _user(db, args.username)
            user.totp_enabled, user.totp_secret, user.recovery_codes = False, None, []
            user.session_epoch += 1
            print("2FA zurückgesetzt. Beim nächsten Login muss sie neu eingerichtet werden.")
        elif args.cmd == "unlock":
            user = _user(db, args.username)
            user.failed_logins, user.locked_until = 0, None
            print("Konto entsperrt.")
        elif args.cmd == "list-users":
            for user in db.scalars(select(User).order_by(User.username)):
                print(f"{user.username:20} {user.role:7} 2FA={'ja' if user.totp_enabled else 'nein'}"
                      f" {'aktiv' if user.active else 'deaktiviert'}")
        db.commit()


if __name__ == "__main__":
    main()
