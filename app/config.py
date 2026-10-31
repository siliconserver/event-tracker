"""Konfiguration über Umgebungsvariablen (siehe docs/BETRIEB.md)."""
import os
from pathlib import Path


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
        # Leer = keine Anmeldung (z. B. nur im VPN). Gesetzt = einfacher Passwortschutz.
        self.app_password = os.environ.get("APP_PASSWORD", "")
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
