"""Anmeldung: Passwort-Hashing (scrypt), TOTP nach RFC 6238, Login-Bremse, Kontosperre."""
from __future__ import annotations

import base64
import datetime as dt
import hashlib
import hmac
import io
import secrets
import struct
import threading
import time
import urllib.parse
from collections import defaultdict, deque

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import User

ROLES = {"viewer": "Nur lesen", "editor": "Lesen und schreiben", "admin": "Administrator"}
MIN_PASSWORD_LENGTH = 10
MAX_FAILED = 5  # danach Kontosperre
LOCK_MINUTES = 15
TOTP_ISSUER = "Event-Tracker"

# ---------- Passwörter ----------
_N, _R, _P = 2**14, 8, 1


def hash_password(pw: str) -> str:
    salt = secrets.token_bytes(16)
    h = hashlib.scrypt(pw.encode(), salt=salt, n=_N, r=_R, p=_P, dklen=32)
    return f"scrypt${_N}${_R}${_P}${salt.hex()}${h.hex()}"


def verify_password(pw: str, stored: str) -> bool:
    try:
        algo, n, r, p, salt, h = stored.split("$")
        if algo != "scrypt":
            return False
        calc = hashlib.scrypt(pw.encode(), salt=bytes.fromhex(salt), n=int(n), r=int(r),
                              p=int(p), dklen=len(bytes.fromhex(h)))
        return hmac.compare_digest(calc.hex(), h)
    except (ValueError, TypeError):
        return False


_DUMMY = hash_password(secrets.token_hex(8))


def password_problem(pw: str, username: str = "") -> str | None:
    if len(pw) < MIN_PASSWORD_LENGTH:
        return f"Das Passwort muss mindestens {MIN_PASSWORD_LENGTH} Zeichen lang sein."
    if username and pw.lower() == username.lower():
        return "Das Passwort darf nicht dem Benutzernamen entsprechen."
    return None


# ---------- TOTP (RFC 6238, SHA-1, 30 s, 6 Stellen – kompatibel zu allen Authenticator-Apps) ----


def new_totp_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")


def _hotp(secret: str, counter: int) -> str:
    key = base64.b32decode(secret + "=" * (-len(secret) % 8), casefold=True)
    d = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    o = d[-1] & 0x0F
    code = (struct.unpack(">I", d[o:o + 4])[0] & 0x7FFFFFFF) % 1_000_000
    return f"{code:06d}"


def totp_now(secret: str, at: float | None = None) -> str:
    return _hotp(secret, int((at or time.time()) // 30))


def verify_totp(secret: str, code: str, last_step: int | None, at: float | None = None,
                window: int = 1) -> int | None:
    """Gibt den akzeptierten Zeitschritt zurück (oder None). Bereits benutzte Schritte gelten nicht."""
    code = "".join(c for c in (code or "") if c.isdigit())
    if len(code) != 6:
        return None
    step = int((at or time.time()) // 30)
    for s in range(step - window, step + window + 1):
        if (last_step is None or s > last_step) and hmac.compare_digest(_hotp(secret, s), code):
            return s
    return None


def totp_uri(secret: str, username: str) -> str:
    label = urllib.parse.quote(f"{TOTP_ISSUER}:{username}")
    q = urllib.parse.urlencode({"secret": secret, "issuer": TOTP_ISSUER})
    return f"otpauth://totp/{label}?{q}"


def qr_svg(data: str) -> str:
    import qrcode
    import qrcode.image.svg

    img = qrcode.make(data, image_factory=qrcode.image.svg.SvgPathImage, box_size=8)
    buf = io.BytesIO()
    img.save(buf)
    return buf.getvalue().decode()


# ---------- Wiederherstellungscodes ----------


def _code_hash(code: str) -> str:
    return hashlib.sha256(code.replace("-", "").upper().encode()).hexdigest()


def new_recovery_codes(n: int = 8) -> tuple[list[str], list[str]]:
    codes = [f"{secrets.token_hex(3)}-{secrets.token_hex(3)}".upper() for _ in range(n)]
    return codes, [_code_hash(c) for c in codes]


def use_recovery_code(user: User, code: str) -> bool:
    h = _code_hash(code.strip())
    remaining = list(user.recovery_codes or [])
    for stored in remaining:
        if hmac.compare_digest(stored, h):
            remaining.remove(stored)
            user.recovery_codes = remaining
            return True
    return False


# ---------- Login-Bremse (pro IP) ----------


class RateLimiter:
    """Höchstens `limit` Fehlversuche je IP in `window` Sekunden."""

    def __init__(self, limit: int = 10, window: int = 600):
        self.limit, self.window = limit, window
        self._hits: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def _trim(self, key: str, now: float) -> deque:
        q = self._hits[key]
        while q and q[0] < now - self.window:
            q.popleft()
        return q

    def blocked(self, key: str) -> bool:
        with self._lock:
            return len(self._trim(key, time.monotonic())) >= self.limit

    def hit(self, key: str) -> None:
        with self._lock:
            now = time.monotonic()
            self._trim(key, now).append(now)

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


ip_limiter = RateLimiter()


def check_credentials(db: Session, username: str, password: str) -> tuple[User | None, str | None]:
    """Prüft Benutzer/Passwort inkl. Kontosperre. Gibt (Benutzer, Fehlermeldung) zurück."""
    generic = "Benutzername oder Passwort falsch."
    user = db.scalar(select(User).where(func.lower(User.username) == username.strip().lower()))
    if user is None or not user.active:
        verify_password(password, _DUMMY)  # gleiche Laufzeit wie bei bekannten Benutzern
        return None, generic
    now = dt.datetime.now()
    if user.locked_until and user.locked_until > now:
        return None, "Zu viele Fehlversuche. Das Konto ist vorübergehend gesperrt."
    if not verify_password(password, user.password_hash):
        register_failure(user)
        return None, generic
    return user, None


def register_failure(user: User) -> None:
    user.failed_logins = (user.failed_logins or 0) + 1
    if user.failed_logins >= MAX_FAILED:
        user.locked_until = dt.datetime.now() + dt.timedelta(minutes=LOCK_MINUTES)
        user.failed_logins = 0


def register_success(user: User) -> None:
    user.failed_logins = 0
    user.locked_until = None
    user.last_login = dt.datetime.now()


def create_user(db: Session, username: str, password: str, role: str) -> User:
    username = username.strip()
    if not username or len(username) > 80:
        raise ValueError("Ungültiger Benutzername.")
    if role not in ROLES:
        raise ValueError("Ungültige Rolle.")
    if problem := password_problem(password, username):
        raise ValueError(problem)
    if db.scalar(select(User).where(func.lower(User.username) == username.lower())):
        raise ValueError("Benutzername ist bereits vergeben.")
    u = User(username=username, password_hash=hash_password(password), role=role)
    db.add(u)
    db.flush()
    return u


def admin_count(db: Session) -> int:
    return db.scalar(select(func.count(User.id)).where(User.role == "admin",
                                                       User.active.is_(True))) or 0
