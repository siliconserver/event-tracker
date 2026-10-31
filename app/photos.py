"""Fotos aus dem NAS-Bestand als Verweise (KONZEPT 2.10).

- Originale werden nur gelesen, nie verändert, verschoben oder gelöscht.
- Der Bestand wird über „Fotobestand einlesen“ indiziert (inkrementell über Größe/mtime).
- Wiedererkennung nach Verschieben/Umbenennen über Pfad + Dateifingerabdruck.
- HEIC wird für die Browseranzeige in JPEG umgewandelt (Vorschau im Datenverzeichnis).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import logging
import threading
from pathlib import Path

from PIL import Image, ImageOps
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .models import Photo

log = logging.getLogger(__name__)

try:  # HEIC/HEIF-Unterstützung
    import pillow_heif

    pillow_heif.register_heif_opener()
except Exception:  # pragma: no cover
    log.warning("pillow-heif nicht verfügbar – HEIC-Dateien werden nicht angezeigt")

EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp", ".tif", ".tiff"}
SKIP_DIRS = {"@eaDir", "#recycle", "#snapshot", ".DS_Store"}  # Synology-Systemordner

scan_state = {"running": False, "scanned": 0, "added": 0, "moved": 0, "missing": 0,
              "error": None, "finished": None}
_lock = threading.Lock()


def fingerprint(path: Path) -> str:
    """Schneller Fingerabdruck: Größe + SHA-256 der ersten und letzten 64 KiB."""
    size = path.stat().st_size
    h = hashlib.sha256(str(size).encode())
    with path.open("rb") as f:
        h.update(f.read(65536))
        if size > 131072:
            f.seek(-65536, 2)
            h.update(f.read(65536))
    return h.hexdigest()


def taken_at(path: Path) -> dt.datetime | None:
    try:
        with Image.open(path) as im:
            exif = im.getexif()
            raw = exif.get_ifd(0x8769).get(36867) or exif.get(306)
            if raw:
                return dt.datetime.strptime(str(raw).strip()[:19], "%Y:%m:%d %H:%M:%S")
    except Exception:
        pass
    try:
        return dt.datetime.fromtimestamp(path.stat().st_mtime)
    except OSError:
        return None


def safe_path(rel: str) -> Path:
    root = settings.photo_root.resolve()
    p = (root / rel).resolve()
    if root != p and root not in p.parents:
        raise ValueError("Pfad liegt außerhalb des Fotoverzeichnisses")
    return p


def iter_files(root: Path):
    for p in root.rglob("*"):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.is_file() and p.suffix.lower() in EXTENSIONS:
            yield p


def scan(db: Session) -> dict:
    root = settings.photo_root
    stats = {"scanned": 0, "added": 0, "moved": 0, "missing": 0}
    if not root.exists():
        raise FileNotFoundError(f"Fotoverzeichnis {root} nicht gefunden")
    known = {p.path: p for p in db.scalars(select(Photo))}
    seen: set[str] = set()
    new_files: list[tuple[str, Path, str]] = []
    for f in iter_files(root):
        rel = f.relative_to(root).as_posix()
        seen.add(rel)
        stats["scanned"] += 1
        scan_state["scanned"] = stats["scanned"]
        st = f.stat()
        ph = known.get(rel)
        if ph and ph.size == st.st_size and ph.mtime == st.st_mtime and not ph.missing:
            continue
        fp = fingerprint(f)
        if ph:
            ph.size, ph.mtime, ph.fingerprint, ph.missing = st.st_size, st.st_mtime, fp, False
            ph.taken_at = taken_at(f)
        else:
            new_files.append((rel, f, fp))
    # verschwundene Pfade -> evtl. verschoben
    gone = {fp_: ph for ph in known.values() if ph.path not in seen
            for fp_ in [ph.fingerprint] if fp_}
    for rel, f, fp in new_files:
        st = f.stat()
        if fp in gone:
            ph = gone.pop(fp)
            ph.path, ph.missing = rel, False
            ph.size, ph.mtime = st.st_size, st.st_mtime
            stats["moved"] += 1
        else:
            db.add(Photo(path=rel, fingerprint=fp, size=st.st_size, mtime=st.st_mtime,
                         taken_at=taken_at(f)))
            stats["added"] += 1
    for ph in known.values():
        if ph.path not in seen and not ph.missing:  # verschobene haben jetzt neuen Pfad
            ph.missing = True
            stats["missing"] += 1
    db.commit()
    return stats


def scan_in_background(session_factory) -> bool:
    if not _lock.acquire(blocking=False):
        return False

    def run():
        scan_state.update(running=True, scanned=0, error=None)
        try:
            with session_factory() as db:
                scan_state.update(scan(db))
        except Exception as e:  # pragma: no cover
            log.exception("Fotoscan fehlgeschlagen")
            scan_state["error"] = str(e)
        finally:
            scan_state.update(running=False, finished=dt.datetime.now())
            _lock.release()

    threading.Thread(target=run, daemon=True).start()
    return True


def candidates(db: Session, day: dt.date, days: int = 1) -> list[Photo]:
    start = dt.datetime.combine(day - dt.timedelta(days=days), dt.time.min)
    end = dt.datetime.combine(day + dt.timedelta(days=days), dt.time.max)
    q = select(Photo).where(Photo.taken_at.between(start, end), Photo.missing.is_(False))
    return list(db.scalars(q.order_by(Photo.taken_at)))


def render(photo: Photo, size: int) -> Path:
    """Erzeugt (einmalig) eine JPEG-Version mit max. `size` px Kantenlänge."""
    out = settings.thumb_dir / f"{photo.fingerprint or photo.id}_{size}.jpg"
    if out.exists():
        return out
    out.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(safe_path(photo.path)) as im:
        im = ImageOps.exif_transpose(im)
        im.thumbnail((size, size))
        im.convert("RGB").save(out, "JPEG", quality=85)
    return out
