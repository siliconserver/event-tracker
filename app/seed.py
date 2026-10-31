from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Sport

DEFAULT_SPORTS = [
    ("Fußball", "match"),
    ("MMA", "fight"),
    ("American Football", "match"),
    ("Boxen", "fight"),
]


def seed(db: Session) -> None:
    existing = set(db.scalars(select(Sport.name)))
    for name, kind in DEFAULT_SPORTS:
        if name not in existing:
            db.add(Sport(name=name, kind=kind))
    db.commit()
