"""Statistiken, Meilensteine, Rekorde, Jahresrückblick, „An diesem Tag“.

Regeln (KONZEPT 2.9): Besuche/Veranstaltungen, Spiele/Kämpfe und Spielstätten werden getrennt
gezählt. Fehlende Werte werden nicht als 0 gerechnet; die Datenabdeckung wird mit ausgegeben.
"""
from __future__ import annotations

import datetime as dt
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from .config import settings
from .models import Event
from .services import event_query, filter_events


@dataclass
class Coverage:
    known: int = 0
    total: int = 0

    @property
    def text(self) -> str:
        return f"{self.known} von {self.total}"


@dataclass
class Stats:
    events: int = 0
    bouts: int = 0
    venues: int = 0
    cities: int = 0
    countries: int = 0
    by_year: list = field(default_factory=list)
    by_sport: list = field(default_factory=list)
    by_venue: list = field(default_factory=list)
    by_country: list = field(default_factory=list)
    by_competition: list = field(default_factory=list)
    teams: list = field(default_factory=list)
    fighters: list = field(default_factory=list)
    pairings: list = field(default_factory=list)
    scorers: list = field(default_factory=list)
    goals_total: int = 0
    goals_coverage: Coverage = field(default_factory=Coverage)
    goals_per_game: float | None = None
    top_scoring: list = field(default_factory=list)
    methods: list = field(default_factory=list)
    cost_total: float = 0.0
    cost_coverage: Coverage = field(default_factory=Coverage)
    rating_avg: dict = field(default_factory=dict)
    first_visits: list = field(default_factory=list)


def load_events(db: Session, filters: dict | None = None) -> list[Event]:
    q = filter_events(event_query(), filters or {}).order_by(Event.date, Event.time)
    return list(db.scalars(q).unique())


def compute(events: list[Event]) -> Stats:
    s = Stats(events=len(events))
    venues, cities, countries = Counter(), set(), Counter()
    years, sports, comps = Counter(), Counter(), Counter()
    team_record: dict[int, dict] = {}
    fighters: dict[int, dict] = {}
    pairings, scorers, methods = Counter(), Counter(), Counter()
    first_seen: dict[int, Event] = {}
    ratings = defaultdict(list)
    scored_games: list = []
    football_games = 0

    for e in events:
        venues[e.venue] += 1
        first_seen.setdefault(e.venue.id, e)
        if e.venue.city:
            cities.add((e.venue.city, e.venue.country))
        if e.venue.country:
            countries[e.venue.country] += 1
        years[e.date.year] += 1
        sports[e.sport.name] += 1
        if e.competition:
            comps[e.competition.name] += 1
        s.bouts += len(e.bouts)

        for b in e.bouts:
            if e.sport.kind == "match":
                football_games += 1
                if b.goals is not None:
                    s.goals_total += b.goals
                    s.goals_coverage.known += 1
                    scored_games.append((b.goals, b, e))
                if b.home and b.away:
                    pairings[" – ".join(sorted([b.home.name, b.away.name]))] += 1
                for side, other, mine, theirs in (
                    (b.home, b.away, b.home_score, b.away_score),
                    (b.away, b.home, b.away_score, b.home_score),
                ):
                    if not side:
                        continue
                    r = team_record.setdefault(
                        side.id, {"p": side, "n": 0, "w": 0, "d": 0, "l": 0, "unknown": 0,
                                  "venues": set()}
                    )
                    r["n"] += 1
                    r["venues"].add(e.venue.name)
                    if mine is None or theirs is None:
                        r["unknown"] += 1
                    elif mine > theirs:
                        r["w"] += 1
                    elif mine < theirs:
                        r["l"] += 1
                    else:
                        r["d"] += 1
                for g in (b.details or {}).get("goals", []) or []:
                    name = g.get("player") if isinstance(g, dict) else str(g)
                    if name:
                        scorers[name] += 1
            else:
                for f in (b.home, b.away):
                    if f:
                        r = fighters.setdefault(f.id, {"p": f, "n": 0, "w": 0})
                        r["n"] += 1
                        if b.winner_id == f.id:
                            r["w"] += 1
                if b.method:
                    methods[b.method] += 1

        v = e.visit
        if v:
            s.cost_coverage.total += 1
            if v.cost is not None:
                s.cost_total += v.cost
                s.cost_coverage.known += 1
            for k in ("rating_atmosphere", "rating_view", "rating_organisation"):
                if getattr(v, k) is not None:
                    ratings[k].append(getattr(v, k))

    s.goals_coverage.total = football_games
    if s.goals_coverage.known:
        s.goals_per_game = round(s.goals_total / s.goals_coverage.known, 2)
    s.venues = len(venues)
    s.cities = len(cities)
    s.countries = len(countries)
    s.by_year = sorted(years.items())
    s.by_sport = sports.most_common()
    s.by_venue = venues.most_common()
    s.by_country = countries.most_common()
    s.by_competition = comps.most_common()
    s.teams = sorted(team_record.values(), key=lambda r: -r["n"])
    s.fighters = sorted(fighters.values(), key=lambda r: -r["n"])
    s.pairings = pairings.most_common(10)
    s.scorers = scorers.most_common(15)
    s.top_scoring = sorted(scored_games, key=lambda t: -t[0])[:5]
    s.methods = methods.most_common()
    s.rating_avg = {k: round(sum(v) / len(v), 1) for k, v in ratings.items() if v}
    s.first_visits = sorted(first_seen.values(), key=lambda e: e.date)
    return s


def on_this_day(events: list[Event], today: dt.date | None = None) -> list[tuple[int, Event]]:
    today = today or dt.date.today()
    return [
        (today.year - e.date.year, e)
        for e in events
        if e.date.month == today.month and e.date.day == today.day and e.date.year < today.year
    ]


MILESTONE_STEPS = (1, 10, 25, 50, 100, 150, 200, 250, 300, 400, 500, 750, 1000)


def milestones(events: list[Event]) -> list[tuple[dt.date, str, Event]]:
    """Beispiel-Meilensteine (Schwellen sind konfigurierbar, siehe KONZEPT 2.12)."""
    out = []
    venues: set[int] = set()
    sports: set[str] = set()
    countries: set[str] = set()
    for i, e in enumerate(sorted(events, key=lambda e: (e.date, e.time or dt.time.min)), 1):
        if i in MILESTONE_STEPS:
            out.append((e.date, f"{i}. Besuch", e))
        if e.venue_id not in venues:
            venues.add(e.venue_id)
            if len(venues) in MILESTONE_STEPS and len(venues) > 1:
                out.append((e.date, f"{len(venues)}. Spielstätte", e))
        if e.sport.name not in sports:
            sports.add(e.sport.name)
            if len(sports) > 1:
                out.append((e.date, f"Erstmals {e.sport.name}", e))
        c = e.venue.country
        if c and c not in countries:
            countries.add(c)
            if c != settings.home_country:
                out.append((e.date, f"Erstes Event in {c}", e))
    return out


def records(events: list[Event]) -> list[tuple[str, str, Event | None]]:
    out = []
    best_goals = None
    for e in events:
        for b in e.bouts:
            if b.goals is not None and (best_goals is None or b.goals > best_goals[0]):
                best_goals = (b.goals, b, e)
    if best_goals:
        g, b, e = best_goals
        out.append(("Torreichstes Spiel",
                    f"{b.home.name if b.home else '?'} – {b.away.name if b.away else '?'} {b.score}",
                    e))
    with_att = [e for e in events if e.attendance]
    if with_att:
        e = max(with_att, key=lambda e: e.attendance)
        out.append(("Größte belegte Zuschauerzahl", f"{e.attendance:,}".replace(",", "."), e))
    if events:
        c = Counter(e.venue for e in events).most_common(1)[0]
        out.append(("Häufigste Spielstätte", f"{c[0].name} ({c[1]}×)", None))
    most_bouts = max(events, key=lambda e: len(e.bouts), default=None)
    if most_bouts and len(most_bouts.bouts) > 1:
        out.append(("Meiste Spiele/Kämpfe an einem Event", str(len(most_bouts.bouts)), most_bouts))
    return out
