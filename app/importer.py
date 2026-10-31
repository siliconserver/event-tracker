"""Recherche-Austauschformat (Schema-Version 1) und Import mit Vorschau.

Siehe docs/IMPORT_FORMAT.md. Regeln (KONZEPT 2.3):
- Fehlende Angaben bleiben leer, nichts wird geschätzt.
- Manuell gepflegte (gesperrte) Felder werden nie überschrieben.
- Bestehende Werte werden nur überschrieben, wenn das ausdrücklich gewählt wird.
- Persönliche Besuchsdaten werden nie verändert.
- Quellen und offene Fragen werden ergänzt, nicht ersetzt.
"""
from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from .models import Bout, Event, Source, Venue, VenueAlias, Visit
from .services import (
    duplicate_events,
    find_sport,
    find_venue,
    get_or_create_competition,
    get_or_create_participant,
)

SCHEMA_VERSION = 1

EVENT_FIELDS = ("time", "title", "stage", "is_final", "attendance", "weather", "report",
                "venue_name_at_event", "competition")


class ImportError_(ValueError):
    pass


@dataclass
class Change:
    field: str
    current: object
    new: object
    action: str  # "setzen" | "überschreiben" | "behalten (gesperrt)" | "behalten" | "neu"


@dataclass
class Plan:
    payload: dict
    event: Event | None  # Ziel (None = neu)
    venue: Venue | None
    new_venue: bool
    changes: list[Change] = field(default_factory=list)
    bouts_action: str = ""
    warnings: list[str] = field(default_factory=list)
    duplicates: list[Event] = field(default_factory=list)


def parse(text: str) -> list[dict]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ImportError_(f"Kein gültiges JSON: {e}") from e
    if isinstance(data, dict) and "events" in data and isinstance(data["events"], list):
        items = data["events"]
    elif isinstance(data, list):
        items = data
    else:
        items = [data]
    for i, it in enumerate(items, 1):
        if not isinstance(it, dict) or not isinstance(it.get("event"), dict):
            raise ImportError_(f"Eintrag {i}: Objekt mit Schlüssel \"event\" erwartet.")
        v = it.get("schema_version", SCHEMA_VERSION)
        if v != SCHEMA_VERSION:
            raise ImportError_(f"Eintrag {i}: schema_version {v} wird nicht unterstützt.")
        ev = it["event"]
        if not ev.get("date"):
            raise ImportError_(f"Eintrag {i}: event.date fehlt.")
        try:
            dt.date.fromisoformat(ev["date"])
        except ValueError as e:
            raise ImportError_(f"Eintrag {i}: event.date ist kein Datum (JJJJ-MM-TT).") from e
    return items


def _blank(v) -> bool:
    return v is None or v == "" or v == [] or v == {}


def _event_value(e: Event, name: str):
    if name == "competition":
        return e.competition.name if e.competition else None
    return getattr(e, name)


def _incoming(ev: dict, name: str):
    if name == "venue_name_at_event":
        return (ev.get("venue") or {}).get("name_at_event")
    if name == "time" and ev.get("time"):
        try:
            return dt.time.fromisoformat(ev["time"])
        except ValueError as e:
            raise ImportError_(f"event.time ist keine Uhrzeit (HH:MM): {ev['time']}") from e
    return ev.get(name)


def plan(db: Session, item: dict, target: Event | None, overwrite: bool) -> Plan:
    ev = item["event"]
    vinfo = ev.get("venue") or {}
    venue = target.venue if target else None
    new_venue = False
    if venue is None:
        for n in (vinfo.get("name"), vinfo.get("name_at_event")):
            if n and (venue := find_venue(db, n)):
                break
        if venue is None:
            if not vinfo.get("name"):
                raise ImportError_("Spielstätte fehlt (event.venue.name).")
            new_venue = True

    p = Plan(payload=item, event=target, venue=venue, new_venue=new_venue)
    if target is None and venue is not None:
        p.duplicates = duplicate_events(db, dt.date.fromisoformat(ev["date"]), venue.id)
        if p.duplicates:
            p.warnings.append("Am selben Tag gibt es in dieser Spielstätte bereits ein Event. "
                              "Bitte prüfen, ob die Daten dort ergänzt werden sollen.")
    if target is None and not find_sport(db, ev.get("sport")):
        p.warnings.append(f"Sportart „{ev.get('sport')}“ unbekannt – bitte vor dem Import anlegen.")

    locked = set(target.locked_fields or []) if target else set()
    for name in EVENT_FIELDS:
        new = _incoming(ev, name)
        if _blank(new):
            continue
        cur = _event_value(target, name) if target else None
        if target is None:
            action = "neu"
        elif name in locked:
            action = "behalten (gesperrt)"
        elif _blank(cur):
            action = "setzen"
        elif cur == new:
            continue
        elif overwrite:
            action = "überschreiben"
        else:
            action = "behalten"
        p.changes.append(Change(name, cur, new, action))

    bouts = item.get("bouts") or []
    if bouts:
        if target is None or not target.bouts:
            p.bouts_action = f"{len(bouts)} Spiel(e)/Kampf/Kämpfe anlegen"
        elif "bouts" in locked:
            p.bouts_action = "Spiele/Kämpfe sind gesperrt – werden nicht verändert"
        elif overwrite:
            p.bouts_action = f"Bestehende {len(target.bouts)} ersetzen durch {len(bouts)}"
        else:
            p.bouts_action = "Bereits vorhanden – werden nicht verändert"
    return p


def apply(db: Session, p: Plan) -> Event:
    item, ev = p.payload, p.payload["event"]
    vinfo = ev.get("venue") or {}
    e = p.event
    if e is None:
        sport = find_sport(db, ev.get("sport"))
        if sport is None:
            raise ImportError_(f"Sportart „{ev.get('sport')}“ unbekannt.")
        venue = p.venue
        if venue is None:
            venue = Venue(name=vinfo["name"].strip(), city=vinfo.get("city"),
                          country=vinfo.get("country"), lat=vinfo.get("lat"), lon=vinfo.get("lon"))
            db.add(venue)
            db.flush()
        e = Event(date=dt.date.fromisoformat(ev["date"]), sport=sport, venue=venue,
                  locked_fields=[])
        e.visit = Visit()
        db.add(e)
    else:
        venue = e.venue
        # Fehlende Koordinaten/Ort der Spielstätte ergänzen, nie überschreiben.
        for k in ("city", "country", "lat", "lon"):
            if getattr(venue, k) is None and vinfo.get(k) is not None:
                setattr(venue, k, vinfo[k])

    for c in p.changes:
        if c.action not in ("neu", "setzen", "überschreiben"):
            continue
        if c.field == "competition":
            e.competition = get_or_create_competition(db, c.new)
        else:
            setattr(e, c.field, c.new)

    # damaligen Namen als Alias der Spielstätte merken
    at = vinfo.get("name_at_event")
    if at and at.strip() and at.strip() != venue.name and not any(
        a.name == at.strip() for a in venue.aliases
    ):
        venue.aliases.append(VenueAlias(name=at.strip()))

    bouts = item.get("bouts") or []
    replace = bool(e.bouts) and p.event is not None and "bouts" not in (e.locked_fields or []) \
        and p.bouts_action.startswith("Bestehende")
    if bouts and (not e.bouts or replace):
        e.bouts.clear()
        kind = "person" if e.sport.kind == "fight" else "team"
        for i, b in enumerate(bouts):
            home = get_or_create_participant(db, b.get("home"), kind)
            away = get_or_create_participant(db, b.get("away"), kind)
            winner = None
            if b.get("winner"):
                winner = get_or_create_participant(db, b["winner"], kind)
            e.bouts.append(Bout(
                position=i, label=b.get("label"), home=home, away=away,
                home_score=b.get("home_score"), away_score=b.get("away_score"),
                winner=winner, is_draw=bool(b.get("is_draw")), method=b.get("method"),
                round=b.get("round"), details=b.get("details") or {},
            ))

    known = {s.url for s in e.sources if s.url}
    for s in item.get("sources") or []:
        if isinstance(s, str):
            s = {"url": s}
        if s.get("url") and s["url"] in known:
            continue
        e.sources.append(Source(url=s.get("url"), title=s.get("title"), field=s.get("field"),
                                note=s.get("note")))
    qs = [q for q in (item.get("open_questions") or []) if q]
    if qs:
        existing = e.open_questions or ""
        add = [q for q in qs if q not in existing]
        if add:
            e.open_questions = "\n".join(filter(None, [existing] + add))
    db.flush()
    return e


TEMPLATE = {
    "schema_version": 1,
    "event": {
        "date": "JJJJ-MM-TT",
        "time": "HH:MM oder null",
        "sport": "Fußball | MMA | American Football | Boxen",
        "title": "z. B. OKTAGON 60 oder null",
        "competition": "z. B. 2. Bundesliga oder null",
        "stage": "z. B. 12. Spieltag, Halbfinale, Finale oder null",
        "is_final": False,
        "venue": {"name": "Name der Spielstätte", "name_at_event": "Name zum Zeitpunkt",
                  "city": "Stadt", "country": "Land (deutsch)", "lat": None, "lon": None},
        "attendance": None,
        "weather": "kurz, mit Hinweis auf Quelle/Messstation, oder null",
        "report": "kurze Zusammenfassung oder null",
    },
    "bouts": [
        {"label": "z. B. Hauptkampf oder null", "home": "Heimteam / Kämpfer A",
         "away": "Gastteam / Kämpfer B", "home_score": None, "away_score": None,
         "winner": "nur bei Kämpfen", "method": "KO/TKO | Submission | Punktsieg | ...",
         "round": None,
         "details": {"goals": [{"minute": None, "player": "", "team": ""}],
                     "lineups": {}, "cards": [], "substitutions": [], "referee": None}}
    ],
    "sources": [{"url": "https://...", "title": "", "field": "z. B. bouts oder attendance"}],
    "open_questions": ["Unklare oder widersprüchliche Angaben"],
}


def research_prompt(e: Event) -> str:
    known = {
        "Datum": e.date.isoformat(),
        "Sportart": e.sport.name,
        "Spielstätte": e.venue.name + (f" (damals: {e.venue_name_at_event})"
                                       if e.venue_name_at_event else ""),
        "Ort": ", ".join(filter(None, [e.venue.city, e.venue.country])),
        "Wettbewerb": e.competition.name if e.competition else None,
        "Veranstaltung": e.title,
        "Beteiligte": "; ".join(
            f"{b.home.name if b.home else '?'} – {b.away.name if b.away else '?'}" for b in e.bouts
        ) or None,
    }
    lines = [f"- {k}: {v}" for k, v in known.items() if v]
    return (
        "Recherchiere bitte die öffentlichen Fakten zu dieser Sportveranstaltung, "
        "die ich besucht habe:\n\n" + "\n".join(lines) + "\n\n"
        "Regeln:\n"
        "- Gib ausschließlich JSON zurück, genau in der Struktur der Vorlage unten.\n"
        "- Fehlende oder nicht belegbare Angaben als null bzw. leere Liste. Nichts erfinden "
        "oder schätzen.\n"
        "- Zuschauerzahl nur, wenn belegt.\n"
        "- Wetter nur mit Hinweis, worauf es beruht (Station/Modell).\n"
        "- Jede Angabe möglichst mit Quelle in \"sources\" (Feld \"field\" nennt die Angabe).\n"
        "- Widersprüche und Unsicherheiten in \"open_questions\" auflisten.\n"
        "- Bei Kampfabenden alle Kämpfe in Reihenfolge der Card als \"bouts\".\n"
        "- Bei Fußball in details.goals Torschützen mit Minute.\n\n"
        "Vorlage:\n" + json.dumps(TEMPLATE, ensure_ascii=False, indent=2)
    )
