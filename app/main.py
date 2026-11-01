from __future__ import annotations

import datetime as dt
import json
import secrets
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload
from starlette.middleware.sessions import SessionMiddleware

from . import db as dbmod
from . import importer, photos, stats
from .access import check_access
from .auth_routes import register_auth_routes
from .config import settings
from .db import get_db
from .models import (
    Bout,
    Competition,
    Event,
    Participant,
    Photo,
    PhotoLink,
    Source,
    Sport,
    Trip,
    Venue,
    VenueAlias,
    Visit,
)
from .services import (
    duplicate_events,
    event_query,
    filter_events,
    find_venue,
    get_or_create_competition,
    get_or_create_participant,
    to_date,
    to_float,
    to_int,
    to_str,
    to_time,
    venue_name_on,
    years,
)

BASE = Path(__file__).parent
templates = Jinja2Templates(directory=BASE / "templates")
templates.env.globals["settings"] = settings


def _fmt_date(d):
    return d.strftime("%d.%m.%Y") if d else ""


def _fmt_money(v):
    return "" if v is None else f"{v:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


templates.env.filters["d"] = _fmt_date
templates.env.filters["money"] = _fmt_money


def _secret_key() -> str:
    if settings.secret_key:
        return settings.secret_key
    f = settings.data_dir / ".secret_key"
    f.parent.mkdir(parents=True, exist_ok=True)
    if not f.exists():
        f.write_text(secrets.token_urlsafe(32))
    return f.read_text().strip()


def create_app(database_url: str | None = None) -> FastAPI:
    dbmod.init_engine(database_url)
    app = FastAPI(title="Event-Tracker", docs_url=None, redoc_url=None)

    @app.middleware("http")
    async def security(request: Request, call_next):
        blocked = check_access(request)
        response = blocked if blocked is not None else await call_next(request)
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        return response

    app.add_middleware(SessionMiddleware, secret_key=_secret_key(),
                       max_age=60 * 60 * 24 * settings.session_days, same_site="lax",
                       https_only=settings.cookie_secure, session_cookie="et_session")
    app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
    register_routes(app)
    return app


def render(request: Request, name: str, **ctx):
    return templates.TemplateResponse(request, name, ctx)


def redirect(url: str):
    return RedirectResponse(url, status_code=303)


def lookups(db: Session) -> dict:
    return {
        "sports": list(db.scalars(select(Sport).order_by(Sport.name))),
        "venues": list(db.scalars(select(Venue).order_by(Venue.name))),
        "competitions": list(db.scalars(select(Competition).order_by(Competition.name))),
        "teams": list(db.scalars(select(Participant).order_by(Participant.name))),
        "trips": list(db.scalars(select(Trip).order_by(Trip.name))),
        "countries": sorted({c for c in db.scalars(select(Venue.country)) if c}),
        "years": years(db),
    }


def get_event(db: Session, event_id: int) -> Event:
    e = db.scalar(event_query().where(Event.id == event_id).options(
        selectinload(Event.sources),
        selectinload(Event.visit).selectinload(Visit.photo_links).selectinload(PhotoLink.photo)))
    if not e:
        raise HTTPException(404, "Event nicht gefunden")
    return e


EVENT_FORM_FIELDS = ("date", "time", "title", "sport_id", "venue_id", "venue_name_at_event",
                     "competition", "stage", "is_final", "attendance", "weather", "report",
                     "open_questions")


def register_routes(app: FastAPI) -> None:  # noqa: C901 - bewusst eine Routing-Datei

    register_auth_routes(app, render, redirect)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    # ---------- Start ----------
    @app.get("/", response_class=HTMLResponse)
    def home(request: Request, db: Session = Depends(get_db)):
        evs = stats.load_events(db)
        st = stats.compute(evs)
        return render(request, "home.html", stats=st, on_this_day=stats.on_this_day(evs),
                      recent=list(reversed(evs[-8:])), milestones=stats.milestones(evs)[-5:][::-1])

    # ---------- Events ----------
    @app.get("/events", response_class=HTMLResponse)
    def events(request: Request, db: Session = Depends(get_db)):
        f = {k: v for k, v in request.query_params.items() if v}
        evs = list(db.scalars(filter_events(event_query(), f).order_by(Event.date.desc())).unique())
        return render(request, "events.html", events=evs, f=f, **lookups(db))

    @app.get("/events/new", response_class=HTMLResponse)
    def event_new(request: Request, db: Session = Depends(get_db)):
        pre = {"venue_id": request.query_params.get("venue_id")}
        return render(request, "event_form.html", e=None, pre=pre, error=None, **lookups(db))

    def _apply_event_form(db: Session, e: Event, form, manual: bool) -> None:
        old = {k: getattr(e, k, None) for k in EVENT_FORM_FIELDS if k != "competition"}
        old["competition"] = e.competition.name if e.competition else None
        e.date = to_date(form.get("date"))
        e.time = to_time(form.get("time"))
        e.title = to_str(form.get("title"))
        e.sport_id = int(form["sport_id"])
        e.venue_id = int(form["venue_id"])
        e.venue_name_at_event = to_str(form.get("venue_name_at_event"))
        e.competition = get_or_create_competition(db, form.get("competition"))
        e.stage = to_str(form.get("stage"))
        e.is_final = bool(form.get("is_final"))
        e.attendance = to_int(form.get("attendance"))
        e.weather = to_str(form.get("weather"))
        e.report = to_str(form.get("report"))
        e.open_questions = to_str(form.get("open_questions"))
        if manual and e.id:
            # manuell geänderte Felder vor späteren Importen schützen
            new = {k: getattr(e, k, None) for k in EVENT_FORM_FIELDS if k != "competition"}
            new["competition"] = e.competition.name if e.competition else None
            locked = set(e.locked_fields or [])
            locked |= {k for k in new if new[k] != old[k] and k not in ("date", "sport_id",
                                                                        "venue_id")}
            e.locked_fields = sorted(locked)

    @app.post("/events/new")
    async def event_create(request: Request, db: Session = Depends(get_db)):
        form = await request.form()
        if not form.get("venue_id") and form.get("new_venue_name"):
            name = form["new_venue_name"].strip()
            v = find_venue(db, name)
            if v is None:
                v = Venue(name=name, city=to_str(form.get("new_venue_city")),
                          country=to_str(form.get("new_venue_country")))
                db.add(v)
                db.flush()
            form = dict(form)
            form["venue_id"] = str(v.id)
        if not form.get("venue_id") or not form.get("date") or not form.get("sport_id"):
            return render(request, "event_form.html", e=None, pre=dict(form),
                          error="Datum, Sportart und Spielstätte sind Pflichtfelder.",
                          **lookups(db))
        e = Event(locked_fields=[])
        _apply_event_form(db, e, form, manual=False)
        e.visit = Visit()
        db.add(e)
        db.flush()
        if not e.venue_name_at_event:
            e.venue_name_at_event = venue_name_on(db.get(Venue, e.venue_id), e.date)
        # Beteiligte direkt mit anlegen (ein Spiel bzw. Hauptkampf)
        kind = "person" if db.get(Sport, e.sport_id).kind == "fight" else "team"
        home = get_or_create_participant(db, form.get("home"), kind)
        away = get_or_create_participant(db, form.get("away"), kind)
        if home or away:
            e.bouts.append(Bout(position=0, home=home, away=away,
                                home_score=to_int(form.get("home_score")),
                                away_score=to_int(form.get("away_score")), details={}))
        db.commit()
        return redirect(f"/events/{e.id}")

    @app.get("/events/{event_id}", response_class=HTMLResponse)
    def event_detail(event_id: int, request: Request, db: Session = Depends(get_db)):
        e = get_event(db, event_id)
        dups = duplicate_events(db, e.date, e.venue_id, exclude_id=e.id)
        return render(request, "event_detail.html", e=e, duplicates=dups, **lookups(db))

    @app.get("/events/{event_id}/edit", response_class=HTMLResponse)
    def event_edit(event_id: int, request: Request, db: Session = Depends(get_db)):
        e = get_event(db, event_id)
        return render(request, "event_form.html", e=e, pre={}, error=None, **lookups(db))

    @app.post("/events/{event_id}/edit")
    async def event_update(event_id: int, request: Request, db: Session = Depends(get_db)):
        e = get_event(db, event_id)
        form = await request.form()
        _apply_event_form(db, e, form, manual=True)
        db.commit()
        return redirect(f"/events/{e.id}")

    @app.post("/events/{event_id}/unlock")
    async def event_unlock(event_id: int, request: Request, db: Session = Depends(get_db)):
        e = get_event(db, event_id)
        form = await request.form()
        fld = form.get("field")
        e.locked_fields = [f for f in (e.locked_fields or []) if f != fld] if fld else []
        db.commit()
        return redirect(f"/events/{e.id}")

    @app.post("/events/{event_id}/delete")
    def event_delete(event_id: int, db: Session = Depends(get_db)):
        e = get_event(db, event_id)
        db.delete(e)
        db.commit()
        return redirect("/events")

    @app.post("/events/{event_id}/visit")
    async def visit_update(event_id: int, request: Request, db: Session = Depends(get_db)):
        e = get_event(db, event_id)
        form = await request.form()
        v = e.visit or Visit(event=e)
        v.seat = to_str(form.get("seat"))
        v.companions = to_str(form.get("companions"))
        v.cost = to_float(form.get("cost"))
        v.rating_atmosphere = to_int(form.get("rating_atmosphere"))
        v.rating_view = to_int(form.get("rating_view"))
        v.rating_organisation = to_int(form.get("rating_organisation"))
        v.highlight = to_str(form.get("highlight"))
        v.notes = to_str(form.get("notes"))
        v.ticket_note = to_str(form.get("ticket_note"))
        v.trip_id = to_int(form.get("trip_id"))
        db.add(v)
        db.commit()
        return redirect(f"/events/{e.id}#besuch")

    # ---------- Spiele / Kämpfe ----------
    @app.post("/events/{event_id}/bouts")
    async def bout_add(event_id: int, request: Request, db: Session = Depends(get_db)):
        e = get_event(db, event_id)
        form = await request.form()
        kind = "person" if e.sport.kind == "fight" else "team"
        bid = to_int(form.get("bout_id"))
        b = db.get(Bout, bid) if bid else Bout(event=e, position=len(e.bouts), details={})
        if b is None or b.event_id not in (None, e.id):
            raise HTTPException(404)
        db.add(b)
        b.label = to_str(form.get("label"))
        b.home = get_or_create_participant(db, form.get("home"), kind)
        b.away = get_or_create_participant(db, form.get("away"), kind)
        b.home_score = to_int(form.get("home_score"))
        b.away_score = to_int(form.get("away_score"))
        w = form.get("winner")
        b.winner = b.home if w == "home" else b.away if w == "away" else None
        b.is_draw = w == "draw"
        b.method = to_str(form.get("method"))
        b.round = to_int(form.get("round"))
        scorers = [s.strip() for s in (form.get("scorers") or "").split("\n") if s.strip()]
        details = dict(b.details or {})
        if scorers or "goals" in details:
            details["goals"] = [{"player": s} for s in scorers]
        b.details = details
        db.add(b)
        if bid:  # manuelle Korrektur -> Spiele/Kämpfe vor Import schützen
            e.locked_fields = sorted(set(e.locked_fields or []) | {"bouts"})
        db.commit()
        return redirect(f"/events/{e.id}#spiele")

    @app.post("/bouts/{bout_id}/delete")
    def bout_delete(bout_id: int, db: Session = Depends(get_db)):
        b = db.get(Bout, bout_id)
        if not b:
            raise HTTPException(404)
        eid = b.event_id
        db.delete(b)
        db.commit()
        return redirect(f"/events/{eid}#spiele")

    @app.post("/events/{event_id}/sources")
    async def source_add(event_id: int, request: Request, db: Session = Depends(get_db)):
        e = get_event(db, event_id)
        form = await request.form()
        if to_str(form.get("url")) or to_str(form.get("title")):
            e.sources.append(Source(url=to_str(form.get("url")), title=to_str(form.get("title")),
                                    field=to_str(form.get("field"))))
            db.commit()
        return redirect(f"/events/{e.id}#quellen")

    @app.post("/sources/{source_id}/delete")
    def source_delete(source_id: int, db: Session = Depends(get_db)):
        s = db.get(Source, source_id)
        if not s:
            raise HTTPException(404)
        eid = s.event_id
        db.delete(s)
        db.commit()
        return redirect(f"/events/{eid}#quellen")

    # ---------- Recherche / Import ----------
    @app.get("/events/{event_id}/research", response_class=HTMLResponse)
    def research(event_id: int, request: Request, db: Session = Depends(get_db)):
        e = get_event(db, event_id)
        return render(request, "import.html", target=e, prompt=importer.research_prompt(e),
                      text="", plans=None, error=None, overwrite=False)

    @app.get("/import", response_class=HTMLResponse)
    def import_form(request: Request):
        tpl = json.dumps(importer.TEMPLATE, ensure_ascii=False, indent=2)
        return render(request, "import.html", target=None, prompt=None, template=tpl, text="",
                      plans=None, error=None, overwrite=False)

    @app.post("/import", response_class=HTMLResponse)
    async def import_run(request: Request, db: Session = Depends(get_db)):
        form = await request.form()
        text = form.get("json", "")
        target_id = to_int(form.get("target_id"))
        overwrite = bool(form.get("overwrite"))
        confirm = form.get("confirm") == "1"
        target = get_event(db, target_id) if target_id else None
        try:
            items = importer.parse(text)
            if target and len(items) != 1:
                raise importer.ImportError_("Für ein bestehendes Event genau einen Eintrag "
                                            "importieren.")
            plans = [importer.plan(db, it, target, overwrite) for it in items]
            if confirm:
                created = [importer.apply(db, p) for p in plans]
                db.commit()
                if len(created) == 1:
                    return redirect(f"/events/{created[0].id}")
                return redirect("/events")
        except importer.ImportError_ as ex:
            db.rollback()
            return render(request, "import.html", target=target, prompt=None, text=text,
                          plans=None, error=str(ex), overwrite=overwrite)
        return render(request, "import.html", target=target, prompt=None, text=text,
                      plans=plans, error=None, overwrite=overwrite)

    # ---------- Spielstätten ----------
    @app.get("/venues", response_class=HTMLResponse)
    def venues(request: Request, db: Session = Depends(get_db)):
        q = (request.query_params.get("q") or "").strip()
        counts = dict(db.execute(select(Event.venue_id, func.count()).group_by(Event.venue_id)).all())
        vs = list(db.scalars(select(Venue).options(selectinload(Venue.aliases))
                             .order_by(Venue.name)))
        if q:
            from .services import norm
            k = norm(q)
            vs = [v for v in vs if k in norm(v.name) or k in norm(v.city)
                  or any(k in norm(a.name) for a in v.aliases)]
        return render(request, "venues.html", venues=vs, counts=counts, q=q)

    @app.get("/venues/new", response_class=HTMLResponse)
    def venue_new(request: Request):
        return render(request, "venue_form.html", v=None, error=None)

    def _venue_from_form(v: Venue, form) -> None:
        v.name = form["name"].strip()
        v.city = to_str(form.get("city"))
        v.country = to_str(form.get("country"))
        v.lat = to_float(form.get("lat"))
        v.lon = to_float(form.get("lon"))
        v.notes = to_str(form.get("notes"))

    @app.post("/venues/new")
    async def venue_create(request: Request, db: Session = Depends(get_db)):
        form = await request.form()
        if not to_str(form.get("name")):
            return render(request, "venue_form.html", v=None, error="Name fehlt.")
        existing = find_venue(db, form["name"])
        if existing:
            return render(request, "venue_form.html", v=None,
                          error=f"„{form['name']}“ ist bereits als {existing.name} erfasst.")
        v = Venue()
        _venue_from_form(v, form)
        db.add(v)
        db.commit()
        return redirect(f"/venues/{v.id}")

    @app.get("/venues/{venue_id}", response_class=HTMLResponse)
    def venue_detail(venue_id: int, request: Request, db: Session = Depends(get_db)):
        v = db.scalar(select(Venue).where(Venue.id == venue_id).options(
            selectinload(Venue.aliases),
            selectinload(Venue.photo_links).selectinload(PhotoLink.photo)))
        if not v:
            raise HTTPException(404)
        evs = stats.load_events(db, {"venue_id": venue_id})
        links = sorted(v.photo_links, key=lambda pl: (not pl.is_cover, pl.view or "", pl.position))
        return render(request, "venue_detail.html", v=v, events=evs, links=links,
                      sports=sorted({e.sport.name for e in evs}),
                      all_venues=list(db.scalars(select(Venue).order_by(Venue.name))))

    @app.get("/venues/{venue_id}/edit", response_class=HTMLResponse)
    def venue_edit(venue_id: int, request: Request, db: Session = Depends(get_db)):
        v = db.get(Venue, venue_id)
        if not v:
            raise HTTPException(404)
        return render(request, "venue_form.html", v=v, error=None)

    @app.post("/venues/{venue_id}/edit")
    async def venue_update(venue_id: int, request: Request, db: Session = Depends(get_db)):
        v = db.get(Venue, venue_id)
        if not v:
            raise HTTPException(404)
        form = await request.form()
        old = v.name
        _venue_from_form(v, form)
        if old != v.name and not any(a.name == old for a in v.aliases):
            v.aliases.append(VenueAlias(name=old))  # alter Allzeitname bleibt suchbar
        db.commit()
        return redirect(f"/venues/{v.id}")

    @app.post("/venues/{venue_id}/aliases")
    async def alias_add(venue_id: int, request: Request, db: Session = Depends(get_db)):
        v = db.get(Venue, venue_id)
        if not v:
            raise HTTPException(404)
        form = await request.form()
        name = to_str(form.get("name"))
        if name and not any(a.name == name for a in v.aliases):
            v.aliases.append(VenueAlias(name=name, valid_from=to_date(form.get("valid_from")),
                                        valid_to=to_date(form.get("valid_to"))))
            db.commit()
        return redirect(f"/venues/{v.id}")

    @app.post("/aliases/{alias_id}/delete")
    def alias_delete(alias_id: int, db: Session = Depends(get_db)):
        a = db.get(VenueAlias, alias_id)
        if not a:
            raise HTTPException(404)
        vid = a.venue_id
        db.delete(a)
        db.commit()
        return redirect(f"/venues/{vid}")

    @app.post("/venues/{venue_id}/merge")
    async def venue_merge(venue_id: int, request: Request, db: Session = Depends(get_db)):
        """Dublette zusammenführen: diese Spielstätte geht in der Ziel-Spielstätte auf."""
        form = await request.form()
        src, dst = db.get(Venue, venue_id), db.get(Venue, to_int(form.get("target_id")) or 0)
        if not src or not dst or src.id == dst.id:
            raise HTTPException(400, "Ungültige Zusammenführung")
        for e in list(src.events):
            e.venue = dst
            e.venue_name_at_event = e.venue_name_at_event or src.name
        for pl in list(src.photo_links):
            pl.venue = dst
        names = {a.name for a in dst.aliases} | {dst.name}
        for n in [src.name] + [a.name for a in src.aliases]:
            if n not in names:
                dst.aliases.append(VenueAlias(name=n))
                names.add(n)
        for k in ("city", "country", "lat", "lon"):
            if getattr(dst, k) is None:
                setattr(dst, k, getattr(src, k))
        db.flush()
        db.delete(src)
        db.commit()
        return redirect(f"/venues/{dst.id}")

    # ---------- Vereine / Kämpfer ----------
    @app.get("/participants/{pid}", response_class=HTMLResponse)
    def participant(pid: int, request: Request, db: Session = Depends(get_db)):
        p = db.get(Participant, pid)
        if not p:
            raise HTTPException(404)
        evs = stats.load_events(db, {"team_id": pid})
        return render(request, "participant.html", p=p, events=evs, stats=stats.compute(evs),
                      all=list(db.scalars(select(Participant).where(Participant.kind == p.kind,
                                                                    Participant.id != p.id)
                                          .order_by(Participant.name))))

    @app.post("/participants/{pid}/edit")
    async def participant_update(pid: int, request: Request, db: Session = Depends(get_db)):
        p = db.get(Participant, pid)
        if not p:
            raise HTTPException(404)
        form = await request.form()
        p.name = form.get("name", p.name).strip() or p.name
        p.aliases = to_str(form.get("aliases"))
        p.country = to_str(form.get("country"))
        p.is_national = bool(form.get("is_national"))
        db.commit()
        return redirect(f"/participants/{p.id}")

    @app.post("/participants/{pid}/merge")
    async def participant_merge(pid: int, request: Request, db: Session = Depends(get_db)):
        form = await request.form()
        src, dst = db.get(Participant, pid), db.get(Participant, to_int(form.get("target_id")) or 0)
        if not src or not dst or src.id == dst.id:
            raise HTTPException(400)
        for col in ("home_id", "away_id", "winner_id"):
            for b in db.scalars(select(Bout).where(getattr(Bout, col) == src.id)):
                setattr(b, col, dst.id)
        aliases = {a for a in (dst.aliases or "").split(",") if a.strip()}
        aliases |= {src.name} | {a for a in (src.aliases or "").split(",") if a.strip()}
        dst.aliases = ", ".join(sorted(a.strip() for a in aliases))
        db.delete(src)
        db.commit()
        return redirect(f"/participants/{dst.id}")

    # ---------- Reisen ----------
    @app.get("/trips", response_class=HTMLResponse)
    def trips(request: Request, db: Session = Depends(get_db)):
        ts = list(db.scalars(select(Trip).options(
            selectinload(Trip.visits).selectinload(Visit.event).selectinload(Event.venue))
            .order_by(Trip.id.desc())))
        return render(request, "trips.html", trips=ts)

    @app.post("/trips")
    async def trip_create(request: Request, db: Session = Depends(get_db)):
        form = await request.form()
        if to_str(form.get("name")):
            db.add(Trip(name=form["name"].strip(), cost=to_float(form.get("cost")),
                        notes=to_str(form.get("notes"))))
            db.commit()
        return redirect("/trips")

    @app.post("/trips/{trip_id}/edit")
    async def trip_update(trip_id: int, request: Request, db: Session = Depends(get_db)):
        t = db.get(Trip, trip_id)
        if not t:
            raise HTTPException(404)
        form = await request.form()
        t.name = to_str(form.get("name")) or t.name
        t.cost = to_float(form.get("cost"))
        t.notes = to_str(form.get("notes"))
        db.commit()
        return redirect("/trips")

    # ---------- Karte ----------
    @app.get("/map", response_class=HTMLResponse)
    def map_view(request: Request, db: Session = Depends(get_db)):
        return render(request, "map.html", f=dict(request.query_params), **lookups(db))

    @app.get("/api/venues.geojson")
    def venues_geojson(request: Request, db: Session = Depends(get_db)):
        f = {k: v for k, v in request.query_params.items() if v}
        evs = list(db.scalars(filter_events(event_query(), f).order_by(Event.date)).unique())
        by_venue: dict[int, list[Event]] = {}
        for e in evs:
            by_venue.setdefault(e.venue_id, []).append(e)
        feats, missing = [], []
        for vid, es in by_venue.items():
            v = es[0].venue
            if v.lat is None or v.lon is None:
                missing.append({"id": v.id, "name": v.name})
                continue
            feats.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [v.lon, v.lat]},
                "properties": {
                    "id": v.id, "name": v.name, "city": v.city, "visits": len(es),
                    "events": [{"id": e.id, "date": _fmt_date(e.date), "title": e.display_title,
                                "sport": e.sport.name} for e in es[-10:][::-1]],
                },
            })
        return JSONResponse({"type": "FeatureCollection", "features": feats,
                             "without_coordinates": missing})

    # ---------- Statistik / Rückblick ----------
    @app.get("/stats", response_class=HTMLResponse)
    def stats_view(request: Request, db: Session = Depends(get_db)):
        f = {k: v for k, v in request.query_params.items() if v}
        evs = stats.load_events(db, f)
        return render(request, "stats.html", s=stats.compute(evs), f=f,
                      records=stats.records(evs), milestones=stats.milestones(evs), **lookups(db))

    @app.get("/review/{year}", response_class=HTMLResponse)
    def review(year: int, request: Request, db: Session = Depends(get_db)):
        evs = stats.load_events(db, {"year": year})
        before = {e.venue_id for e in stats.load_events(db, {"date_to": f"{year - 1}-12-31"})}
        new_venues = []
        for e in evs:
            if e.venue_id not in before:
                new_venues.append(e.venue)
                before.add(e.venue_id)
        covers = [pl for e in evs if e.visit for pl in e.visit.photo_links if pl.is_cover]
        return render(request, "review.html", year=year, events=evs, s=stats.compute(evs),
                      new_venues=new_venues, covers=covers,
                      highlights=[e for e in evs if e.visit and e.visit.highlight],
                      years=years(db))

    # ---------- Fotos ----------
    @app.post("/photos/scan")
    def photo_scan():
        photos.scan_in_background(dbmod.SessionLocal)
        return redirect("/photos")

    @app.get("/photos", response_class=HTMLResponse)
    def photo_status(request: Request, db: Session = Depends(get_db)):
        total = db.scalar(select(func.count(Photo.id)))
        missing = db.scalar(select(func.count(Photo.id)).where(Photo.missing.is_(True)))
        return render(request, "photos.html", state=photos.scan_state, total=total,
                      missing=missing, root=settings.photo_root)

    @app.get("/events/{event_id}/photos", response_class=HTMLResponse)
    def photo_pick(event_id: int, request: Request, db: Session = Depends(get_db)):
        e = get_event(db, event_id)
        days = to_int(request.query_params.get("days")) or 1
        linked = {pl.photo_id for pl in e.visit.photo_links}
        cands = photos.candidates(db, e.date, days)
        return render(request, "photo_pick.html", e=e, candidates=cands, linked=linked, days=days)

    @app.post("/events/{event_id}/photos")
    async def photo_link(event_id: int, request: Request, db: Session = Depends(get_db)):
        e = get_event(db, event_id)
        form = await request.form()
        ids = [int(i) for i in form.getlist("photo_id")]
        have = {pl.photo_id for pl in e.visit.photo_links}
        pos = len(e.visit.photo_links)
        for pid in ids:
            if pid not in have and db.get(Photo, pid):
                db.add(PhotoLink(photo_id=pid, visit_id=e.visit.id, venue_id=e.venue_id,
                                 position=pos))
                pos += 1
        db.commit()
        return redirect(f"/events/{e.id}#fotos")

    @app.post("/venues/{venue_id}/photos")
    async def venue_photo_link(venue_id: int, request: Request, db: Session = Depends(get_db)):
        """Dauerhaftes Innen-/Außenbild einer Spielstätte (unabhängig von einem Besuch)."""
        form = await request.form()
        rel = to_str(form.get("path"))
        if rel:
            try:
                p = photos.safe_path(rel)
            except ValueError as ex:
                raise HTTPException(400, str(ex)) from ex
            if not p.is_file():
                raise HTTPException(400, "Datei nicht gefunden")
            ph = db.scalar(select(Photo).where(Photo.path == rel))
            if ph is None:
                ph = Photo(path=rel, fingerprint=photos.fingerprint(p), taken_at=photos.taken_at(p))
                db.add(ph)
                db.flush()
            db.add(PhotoLink(photo_id=ph.id, venue_id=venue_id, view=to_str(form.get("view")),
                             caption=to_str(form.get("caption"))))
            db.commit()
        return redirect(f"/venues/{venue_id}")

    @app.post("/photolinks/{link_id}")
    async def photo_link_update(link_id: int, request: Request, db: Session = Depends(get_db)):
        pl = db.get(PhotoLink, link_id)
        if not pl:
            raise HTTPException(404)
        form = await request.form()
        back = form.get("back") or "/"
        if form.get("action") == "remove":
            db.delete(pl)  # nur der Verweis – das Original auf dem NAS bleibt unberührt
        else:
            pl.caption = to_str(form.get("caption"))
            pl.view = to_str(form.get("view"))
            pl.position = to_int(form.get("position")) or 0
            if form.get("is_cover"):
                scope = PhotoLink.visit_id == pl.visit_id if pl.visit_id else \
                    PhotoLink.venue_id == pl.venue_id
                for other in db.scalars(select(PhotoLink).where(scope)):
                    other.is_cover = False
                pl.is_cover = True
            else:
                pl.is_cover = False
        db.commit()
        return redirect(back if back.startswith("/") else "/")

    @app.get("/photo/{photo_id}/{size}")
    def photo_file(photo_id: int, size: int, db: Session = Depends(get_db)):
        if size not in (240, 1600):
            raise HTTPException(404)
        ph = db.get(Photo, photo_id)
        if not ph:
            raise HTTPException(404)
        try:
            out = photos.render(ph, size)
        except (OSError, ValueError) as ex:
            raise HTTPException(404, "Foto nicht verfügbar") from ex
        return FileResponse(out, media_type="image/jpeg",
                            headers={"Cache-Control": "private, max-age=604800"})

    # ---------- Export / Backup ----------
    @app.get("/export.json")
    def export(db: Session = Depends(get_db)):
        from .backup import export_all
        data = export_all(db)
        stamp = dt.datetime.now().strftime("%Y%m%d-%H%M")
        return Response(json.dumps(data, ensure_ascii=False, indent=1, default=str),
                        media_type="application/json",
                        headers={"Content-Disposition":
                                 f'attachment; filename="event-tracker-{stamp}.json"'})


app = None


def get_app() -> FastAPI:
    global app
    if app is None:
        app = create_app()
    return app
