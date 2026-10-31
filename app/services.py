"""Gemeinsame Logik: Namensauflösung (Aliase, Dubletten), Abfragen und Filter."""
from __future__ import annotations

import datetime as dt
import unicodedata

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from .config import settings
from .models import Bout, Competition, Event, Participant, Sport, Venue, VenueAlias, Visit


def norm(s: str | None) -> str:
    """Vergleichsschlüssel: klein, ohne Akzente/Satzzeichen, Leerzeichen zusammengefasst."""
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s.replace("ß", "ss"))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = "".join(c if c.isalnum() else " " for c in s.lower())
    return " ".join(s.split())


def split_aliases(text: str | None) -> list[str]:
    return [a.strip() for a in (text or "").split(",") if a.strip()]


def find_venue(db: Session, name: str) -> Venue | None:
    """Findet eine Spielstätte über Allzeitnamen oder einen ihrer historischen Namen."""
    key = norm(name)
    if not key:
        return None
    for v in db.scalars(select(Venue).options(selectinload(Venue.aliases))):
        if norm(v.name) == key or any(norm(a.name) == key for a in v.aliases):
            return v
    return None


def find_participant(db: Session, name: str, kind: str) -> Participant | None:
    key = norm(name)
    if not key:
        return None
    for p in db.scalars(select(Participant).where(Participant.kind == kind)):
        if norm(p.name) == key or key in {norm(a) for a in split_aliases(p.aliases)}:
            return p
    return None


def get_or_create_participant(db: Session, name: str | None, kind: str) -> Participant | None:
    if not name or not name.strip():
        return None
    p = find_participant(db, name, kind)
    if p is None:
        p = Participant(name=name.strip(), kind=kind)
        db.add(p)
        db.flush()
    return p


def find_competition(db: Session, name: str) -> Competition | None:
    key = norm(name)
    if not key:
        return None
    for c in db.scalars(select(Competition)):
        if norm(c.name) == key or key in {norm(a) for a in split_aliases(c.aliases)}:
            return c
    return None


def get_or_create_competition(db: Session, name: str | None) -> Competition | None:
    if not name or not name.strip():
        return None
    c = find_competition(db, name)
    if c is None:
        c = Competition(name=name.strip())
        db.add(c)
        db.flush()
    return c


def find_sport(db: Session, name: str | None) -> Sport | None:
    key = norm(name)
    if not key:
        return None
    for s in db.scalars(select(Sport)):
        if norm(s.name) == key:
            return s
    synonyms = {"fussball": "Fußball", "soccer": "Fußball", "football": "Fußball",
                "american football": "American Football", "nfl": "American Football",
                "mixed martial arts": "MMA", "boxing": "Boxen"}
    if key in synonyms:
        return db.scalar(select(Sport).where(Sport.name == synonyms[key]))
    return None


def venue_name_on(venue: Venue, date: dt.date) -> str | None:
    """Gültiger historischer Name zum Datum, falls Zeiträume gepflegt sind."""
    for a in venue.aliases:
        if (a.valid_from or dt.date.min) <= date <= (a.valid_to or dt.date.max) and (
            a.valid_from or a.valid_to
        ):
            return a.name
    return None


def duplicate_events(db: Session, date: dt.date, venue_id: int, exclude_id: int | None = None):
    q = select(Event).where(Event.date == date, Event.venue_id == venue_id)
    if exclude_id:
        q = q.where(Event.id != exclude_id)
    return list(db.scalars(q))


def event_query():
    return select(Event).options(
        selectinload(Event.sport),
        selectinload(Event.venue).selectinload(Venue.aliases),
        selectinload(Event.competition),
        selectinload(Event.bouts).selectinload(Bout.home),
        selectinload(Event.bouts).selectinload(Bout.away),
        selectinload(Event.bouts).selectinload(Bout.winner),
        selectinload(Event.visit),
    )


def filter_events(q, f: dict):
    """Kombinierbare Suche: Sportart, Land, Wettbewerb, Verein, Jahr, Zeitraum, Ausland, Finals."""
    if f.get("sport_id"):
        q = q.where(Event.sport_id == int(f["sport_id"]))
    if f.get("competition_id"):
        q = q.where(Event.competition_id == int(f["competition_id"]))
    if f.get("venue_id"):
        q = q.where(Event.venue_id == int(f["venue_id"]))
    if f.get("year"):
        y = int(f["year"])
        q = q.where(Event.date >= dt.date(y, 1, 1), Event.date <= dt.date(y, 12, 31))
    if f.get("date_from"):
        q = q.where(Event.date >= dt.date.fromisoformat(f["date_from"]))
    if f.get("date_to"):
        q = q.where(Event.date <= dt.date.fromisoformat(f["date_to"]))
    if f.get("country") or f.get("abroad"):
        q = q.join(Venue, Event.venue_id == Venue.id)
        if f.get("country"):
            q = q.where(Venue.country == f["country"])
        if f.get("abroad"):
            q = q.where(Venue.country.is_not(None), Venue.country != settings.home_country)
    if f.get("final"):
        q = q.where(Event.is_final.is_(True))
    if f.get("team_id"):
        tid = int(f["team_id"])
        role = f.get("role")  # "" | home | away
        if role == "home":
            cond = Bout.home_id == tid
        elif role == "away":
            cond = Bout.away_id == tid
        else:
            cond = or_(Bout.home_id == tid, Bout.away_id == tid)
        q = q.where(Event.id.in_(select(Bout.event_id).where(cond)))
    if f.get("q"):
        like = f"%{f['q']}%"
        alias_venues = select(VenueAlias.venue_id).where(VenueAlias.name.ilike(like))
        part_ids = select(Participant.id).where(
            or_(Participant.name.ilike(like), Participant.aliases.ilike(like))
        )
        bout_events = select(Bout.event_id).where(
            or_(Bout.home_id.in_(part_ids), Bout.away_id.in_(part_ids))
        )
        visit_events = select(Visit.event_id).where(
            or_(Visit.notes.ilike(like), Visit.highlight.ilike(like), Visit.companions.ilike(like))
        )
        venue_ids = select(Venue.id).where(or_(Venue.name.ilike(like), Venue.city.ilike(like)))
        q = q.where(
            or_(
                Event.title.ilike(like),
                Event.venue_name_at_event.ilike(like),
                Event.venue_id.in_(venue_ids),
                Event.venue_id.in_(alias_venues),
                Event.id.in_(bout_events),
                Event.id.in_(visit_events),
            )
        )
    return q


def years(db: Session) -> list[int]:
    rows = db.scalars(select(func.strftime("%Y", Event.date)).distinct())
    return sorted({int(r) for r in rows if r}, reverse=True)


def to_float(v: str | None) -> float | None:
    v = (v or "").strip().replace(",", ".")
    return float(v) if v else None


def to_int(v: str | None) -> int | None:
    v = (v or "").strip()
    return int(v) if v else None


def to_str(v: str | None) -> str | None:
    v = (v or "").strip()
    return v or None


def to_date(v: str | None) -> dt.date | None:
    v = (v or "").strip()
    return dt.date.fromisoformat(v) if v else None


def to_time(v: str | None) -> dt.time | None:
    v = (v or "").strip()
    return dt.time.fromisoformat(v) if v else None
