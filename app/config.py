"""Konfiguration über Umgebungsvariablen (siehe docs/BETRIEB.md)."""
import os
from pathlib import Path


def _bool(name: str, default: bool) -> bool:
    v = os.environ.get(name)
    if v is None or v.strip() == "":
        return default
    return v.strip().lower() in ("1", "true", "yes", "ja", "on")


class Settings:
    def __init__(self) -> None:
        self.data_dir = Path(os.environ.get("DATA_DIR", "./data"))
        self.database_url = os.environ.get(
            "DATABASE_URL", f"sqlite:///{self.data_dir / 'event-tracker.db'}"
        )
        # Wurzel der NAS-Fotos, im Container nur lesend eingebunden.
        self.photo_root = Path(os.environ.get("PHOTO_ROOT", "./photos"))
        # Vorschaubilder liegen im Datenverzeichnis, nicht neben den Originalen.
        self.thumb_dir = Path(os.environ.get("THUMB_DIR", str(self.data_dir / "thumbs")))
        # Anmeldung mit Benutzern. Nur im abgeschotteten Netz (NAS hinter VPN) abschalten.
        self.auth_enabled = _bool("AUTH_ENABLED", True)
        # 2FA (TOTP) für alle Benutzer verpflichtend
        self.require_2fa = _bool("REQUIRE_2FA", True)
        # Sitzungs-Cookie nur über HTTPS senden (hinter Traefik/HTTPS: true)
        self.cookie_secure = _bool("COOKIE_SECURE", False)
        self.session_days = int(os.environ.get("SESSION_DAYS", "14"))
        self.secret_key = os.environ.get("SECRET_KEY", "")
        self.home_country = os.environ.get("HOME_COUNTRY", "Deutschland")
        self.tile_url = os.environ.get(
            "TILE_URL", "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        )
        self.tile_attribution = os.environ.get(
            "TILE_ATTRIBUTION",
            '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>-Mitwirkende',
        )


settings = Settings()
