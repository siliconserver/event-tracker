"""Datenmodell (vgl. docs/KONZEPT.md, Abschnitt 4).

Grundregeln:
- Nur tatsächlich besuchte Veranstaltungen: zu jeder Veranstaltung gehört genau ein Besuch.
- Alle Spiele/Kämpfe einer Veranstaltung gelten als gesehen.
- Eine Spielstätte hat einen Allzeitnamen; historische Namen sind Aliase derselben Spielstätte.
- Fehlende Angaben bleiben NULL und werden in Statistiken nicht als 0 gezählt.
- Öffentliche Fakten (Event, Bout, Source) und persönliche Daten (Visit, PhotoLink) sind getrennt.
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class Sport(Base):
    __tablename__ = "sport"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    # "match" (Team gegen Team, Tore/Punkte) oder "fight" (Kämpfer gegen Kämpfer)
    kind: Mapped[str] = mapped_column(String(10), default="match")


class Venue(Base):
    """Spielstätte. Umbau/Neubau am selben Ort und Umbenennung = dieselbe Spielstätte."""

    __tablename__ = "venue"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)  # Allzeitname
    city: Mapped[str | None] = mapped_column(String(120))
    country: Mapped[str | None] = mapped_column(String(80))
    lat: Mapped[float | None] = mapped_column(Float)
    lon: Mapped[float | None] = mapped_column(Float)
    notes: Mapped[str | None] = mapped_column(Text)

    aliases: Mapped[list[VenueAlias]] = relationship(
        back_populates="venue", cascade="all, delete-orphan", order_by="VenueAlias.valid_from"
    )
    events: Mapped[list[Event]] = relationship(back_populates="venue", order_by="Event.date")
    photo_links: Mapped[list[PhotoLink]] = relationship(back_populates="venue")


class VenueAlias(Base):
    """Historischer Name / Sponsorenname / alternative Schreibweise einer Spielstätte."""

    __tablename__ = "venue_alias"
    __table_args__ = (UniqueConstraint("venue_id", "name"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    venue_id: Mapped[int] = mapped_column(ForeignKey("venue.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(200))
    valid_from: Mapped[dt.date | None] = mapped_column(Date)
    valid_to: Mapped[dt.date | None] = mapped_column(Date)
    venue: Mapped[Venue] = relationship(back_populates="aliases")


class Competition(Base):
    __tablename__ = "competition"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    # Liga, Pokal, Turnier, Serie, Freundschaftsspiel ...
    type: Mapped[str | None] = mapped_column(String(40))
    aliases: Mapped[str | None] = mapped_column(Text)  # kommagetrennt


class Participant(Base):
    """Verein, Nationalmannschaft oder Sportler/Kämpfer mit einheitlicher Identität."""

    __tablename__ = "participant"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(10), default="team")  # team | person
    is_national: Mapped[bool] = mapped_column(Boolean, default=False)
    country: Mapped[str | None] = mapped_column(String(80))
    aliases: Mapped[str | None] = mapped_column(Text)  # kommagetrennt
    __table_args__ = (UniqueConstraint("name", "kind"),)


class Trip(Base):
    __tablename__ = "trip"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    cost: Mapped[float | None] = mapped_column(Float)  # gemeinsame Reisekosten
    notes: Mapped[str | None] = mapped_column(Text)
    visits: Mapped[list[Visit]] = relationship(back_populates="trip")


class Event(Base):
    """Veranstaltung (öffentliche Fakten). Wird nur angelegt, wenn sie besucht wurde."""

    __tablename__ = "event"
    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[dt.date] = mapped_column(Date, index=True)
    time: Mapped[dt.time | None] = mapped_column(Time)
    title: Mapped[str | None] = mapped_column(String(300))
    sport_id: Mapped[int] = mapped_column(ForeignKey("sport.id"))
    venue_id: Mapped[int] = mapped_column(ForeignKey("venue.id"))
    # Name der Spielstätte zum Zeitpunkt des Besuchs (z. B. Sponsorenname)
    venue_name_at_event: Mapped[str | None] = mapped_column(String(200))
    competition_id: Mapped[int | None] = mapped_column(ForeignKey("competition.id"))
    stage: Mapped[str | None] = mapped_column(String(120))  # z. B. "34. Spieltag", "Finale"
    is_final: Mapped[bool] = mapped_column(Boolean, default=False)
    attendance: Mapped[int | None] = mapped_column(Integer)  # nur wenn belegt
    weather: Mapped[str | None] = mapped_column(String(300))
    report: Mapped[str | None] = mapped_column(Text)  # Zusammenfassung/Spielbericht
    open_questions: Mapped[str | None] = mapped_column(Text)
    # Felder, die manuell gepflegt wurden und von Importen nicht überschrieben werden
    locked_fields: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.now)

    sport: Mapped[Sport] = relationship()
    venue: Mapped[Venue] = relationship(back_populates="events")
    competition: Mapped[Competition | None] = relationship()
    bouts: Mapped[list[Bout]] = relationship(
        back_populates="event", cascade="all, delete-orphan", order_by="Bout.position"
    )
    sources: Mapped[list[Source]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )
    visit: Mapped[Visit] = relationship(
        back_populates="event", cascade="all, delete-orphan", uselist=False
    )

    @property
    def display_title(self) -> str:
        if self.title:
            return self.title
        if self.bouts:
            b = self.bouts[0]
            return f"{b.home.name if b.home else '?'} – {b.away.name if b.away else '?'}"
        return f"{self.sport.name} in {self.venue.name}"


class Bout(Base):
    """Einzelnes Spiel oder einzelner Kampf innerhalb einer Veranstaltung."""

    __tablename__ = "bout"
    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("event.id", ondelete="CASCADE"))
    position: Mapped[int] = mapped_column(Integer, default=0)
    label: Mapped[str | None] = mapped_column(String(120))  # z. B. "Hauptkampf"
    home_id: Mapped[int | None] = mapped_column(ForeignKey("participant.id"))
    away_id: Mapped[int | None] = mapped_column(ForeignKey("participant.id"))
    home_score: Mapped[int | None] = mapped_column(Integer)
    away_score: Mapped[int | None] = mapped_column(Integer)
    winner_id: Mapped[int | None] = mapped_column(ForeignKey("participant.id"))
    is_draw: Mapped[bool] = mapped_column(Boolean, default=False)
    method: Mapped[str | None] = mapped_column(String(40))  # KO/TKO, Submission, Punktsieg ...
    round: Mapped[int | None] = mapped_column(Integer)
    # Sportartspezifisches: Torschützen, Aufstellungen, Karten, Wechsel, Schiedsrichter ...
    details: Mapped[dict] = mapped_column(JSON, default=dict)

    event: Mapped[Event] = relationship(back_populates="bouts")
    home: Mapped[Participant | None] = relationship(foreign_keys=[home_id])
    away: Mapped[Participant | None] = relationship(foreign_keys=[away_id])
    winner: Mapped[Participant | None] = relationship(foreign_keys=[winner_id])

    @property
    def score(self) -> str:
        if self.home_score is None or self.away_score is None:
            return ""
        return f"{self.home_score}:{self.away_score}"

    @property
    def goals(self) -> int | None:
        if self.home_score is None or self.away_score is None:
            return None
        return self.home_score + self.away_score


class Source(Base):
    __tablename__ = "source"
    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("event.id", ondelete="CASCADE"))
    url: Mapped[str | None] = mapped_column(String(1000))
    title: Mapped[str | None] = mapped_column(String(300))
    field: Mapped[str | None] = mapped_column(String(80))  # zu welcher Angabe die Quelle gehört
    note: Mapped[str | None] = mapped_column(Text)
    event: Mapped[Event] = relationship(back_populates="sources")


class Visit(Base):
    """Persönlicher Besuch (private Daten). Wird von Rechercheimporten nie verändert."""

    __tablename__ = "visit"
    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("event.id", ondelete="CASCADE"), unique=True)
    trip_id: Mapped[int | None] = mapped_column(ForeignKey("trip.id", ondelete="SET NULL"))
    seat: Mapped[str | None] = mapped_column(String(200))
    companions: Mapped[str | None] = mapped_column(String(300))
    cost: Mapped[float | None] = mapped_column(Float)
    rating_atmosphere: Mapped[int | None] = mapped_column(Integer)  # 1–5
    rating_view: Mapped[int | None] = mapped_column(Integer)
    rating_organisation: Mapped[int | None] = mapped_column(Integer)
    highlight: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    ticket_note: Mapped[str | None] = mapped_column(Text)  # Ticket/Erinnerungsstücke

    event: Mapped[Event] = relationship(back_populates="visit")
    trip: Mapped[Trip | None] = relationship(back_populates="visits")
    photo_links: Mapped[list[PhotoLink]] = relationship(
        back_populates="visit", order_by="PhotoLink.position"
    )


class Photo(Base):
    """Verweis auf ein Originalfoto auf dem NAS (nur lesend). Original wird nie verändert."""

    __tablename__ = "photo"
    id: Mapped[int] = mapped_column(primary_key=True)
    path: Mapped[str] = mapped_column(String(1000), unique=True)  # relativ zu PHOTO_ROOT
    fingerprint: Mapped[str | None] = mapped_column(String(64), index=True)
    size: Mapped[int | None] = mapped_column(Integer)
    mtime: Mapped[float | None] = mapped_column(Float)
    missing: Mapped[bool] = mapped_column(Boolean, default=False)  # Original nicht mehr gefunden
    taken_at: Mapped[dt.datetime | None] = mapped_column(DateTime, index=True)
    lat: Mapped[float | None] = mapped_column(Float)
    lon: Mapped[float | None] = mapped_column(Float)
    links: Mapped[list[PhotoLink]] = relationship(
        back_populates="photo", cascade="all, delete-orphan"
    )


class PhotoLink(Base):
    """Zuordnung eines Fotos zu einem Besuch und/oder einer Spielstätte."""

    __tablename__ = "photo_link"
    id: Mapped[int] = mapped_column(primary_key=True)
    photo_id: Mapped[int] = mapped_column(ForeignKey("photo.id", ondelete="CASCADE"))
    visit_id: Mapped[int | None] = mapped_column(ForeignKey("visit.id", ondelete="CASCADE"))
    venue_id: Mapped[int | None] = mapped_column(ForeignKey("venue.id", ondelete="CASCADE"))
    caption: Mapped[str | None] = mapped_column(String(300))
    position: Mapped[int] = mapped_column(Integer, default=0)
    is_cover: Mapped[bool] = mapped_column(Boolean, default=False)
    view: Mapped[str | None] = mapped_column(String(10))  # innen | aussen | sitzplatz

    photo: Mapped[Photo] = relationship(back_populates="links")
    visit: Mapped[Visit | None] = relationship(back_populates="photo_links")
    venue: Mapped[Venue | None] = relationship(back_populates="photo_links")


class User(Base):
    """Benutzer mit Rolle: viewer (nur lesen), editor (lesen + schreiben), admin (+ Benutzer)."""

    __tablename__ = "app_user"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True)
    password_hash: Mapped[str] = mapped_column(String(300))
    role: Mapped[str] = mapped_column(String(10), default="viewer")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    totp_secret: Mapped[str | None] = mapped_column(String(64))
    totp_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    totp_last_step: Mapped[int | None] = mapped_column(Integer)  # gegen Wiederverwendung
    recovery_codes: Mapped[list] = mapped_column(JSON, default=list)  # Hashes
    failed_logins: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[dt.datetime | None] = mapped_column(DateTime)
    # Erhöhen macht alle bestehenden Sitzungen des Benutzers ungültig
    session_epoch: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.now)
    last_login: Mapped[dt.datetime | None] = mapped_column(DateTime)

    @property
    def can_write(self) -> bool:
        return self.role in ("editor", "admin")

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"
