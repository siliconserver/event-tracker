"""Vollständiger JSON-Export aller Tabellen (Backup). Die SQLite-Datei selbst liegt in DATA_DIR
und kann zusätzlich per Hyper Backup gesichert werden (siehe docs/BETRIEB.md)."""
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from .db import Base


EXCLUDED = {"app_user"}  # Zugangsdaten gehören nicht in den Export


def export_all(db: Session) -> dict:
    out = {"format": "event-tracker-export", "version": 1, "tables": {}}
    for mapper in Base.registry.mappers:
        cls = mapper.class_
        if cls.__tablename__ in EXCLUDED:
            continue
        cols = [c.key for c in inspect(cls).column_attrs]
        out["tables"][cls.__tablename__] = [
            {c: getattr(row, c) for c in cols} for row in db.query(cls).order_by(cls.id)
        ]
    return out
