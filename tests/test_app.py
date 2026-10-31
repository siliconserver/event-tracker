import datetime as dt
import json

from sqlalchemy import select

from app import db as dbmod
from app.models import Event, Participant, Photo, PhotoLink, Sport, Venue


def sport_id(name):
    with dbmod.SessionLocal() as db:
        return db.scalar(select(Sport.id).where(Sport.name == name))


def make_venue(client, name="Waldstadion", **kw):
    data = {"name": name, "city": "Frankfurt am Main", "country": "Deutschland",
            "lat": "50.0686", "lon": "8.6455", **kw}
    r = client.post("/venues/new", data=data, follow_redirects=False)
    assert r.status_code == 303, r.text
    return int(r.headers["location"].rsplit("/", 1)[1])


def make_event(client, venue_id, date="2023-05-20", sport="Fußball", **kw):
    data = {"date": date, "sport_id": str(sport_id(sport)), "venue_id": str(venue_id), **kw}
    r = client.post("/events/new", data=data, follow_redirects=False)
    assert r.status_code == 303, r.text
    return int(r.headers["location"].rsplit("/", 1)[1])


def test_pages_render(client):
    vid = make_venue(client)
    eid = make_event(client, vid, home="Eintracht Frankfurt", away="1. FC Kaiserslautern",
                     home_score="1", away_score="2", competition="DFB-Pokal")
    for url in ["/", "/events", "/venues", f"/venues/{vid}", f"/events/{eid}",
                f"/events/{eid}/edit", "/map", "/stats", "/review/2023", "/trips", "/import",
                f"/events/{eid}/research", "/photos", f"/events/{eid}/photos", "/events/new",
                "/venues/new", "/health", "/export.json"]:
        r = client.get(url)
        assert r.status_code == 200, (url, r.text[:500])


def test_alias_search_and_no_duplicate_venue(client):
    vid = make_venue(client)
    client.post(f"/venues/{vid}/aliases", data={"name": "Commerzbank-Arena",
                                                "valid_from": "2005-05-01",
                                                "valid_to": "2020-06-30"})
    r = client.get("/venues", params={"q": "commerzbank"})
    assert "Waldstadion" in r.text
    # Neue Spielstätte mit historischem Namen wird als vorhanden erkannt
    r = client.post("/venues/new", data={"name": "Commerzbank Arena"})
    assert "bereits als Waldstadion" in r.text
    # damaliger Name wird aus dem Gültigkeitszeitraum übernommen
    eid = make_event(client, vid, date="2010-03-01")
    with dbmod.SessionLocal() as db:
        assert db.get(Event, eid).venue_name_at_event == "Commerzbank-Arena"


def test_stats_count_separately_and_missing_not_zero(client):
    vid = make_venue(client, name="Oktagon Halle")
    eid = make_event(client, vid, sport="MMA", title="OKTAGON 60",
                     home="Fighter A", away="Fighter B")
    client.post(f"/events/{eid}/bouts", data={"home": "Fighter C", "away": "Fighter D",
                                              "winner": "home", "method": "KO/TKO"})
    v2 = make_venue(client, name="Fritz-Walter-Stadion", city="Kaiserslautern",
                    lat="49.4345", lon="7.7765")
    make_event(client, v2, home="1. FC Kaiserslautern", away="Karlsruher SC",
               home_score="3", away_score="0")
    make_event(client, v2, date="2024-01-01", home="FCK", away="SV Darmstadt 98")  # ohne Ergebnis
    from app import stats
    with dbmod.SessionLocal() as db:
        s = stats.compute(stats.load_events(db))
    assert s.events == 3 and s.bouts == 4 and s.venues == 2
    assert s.goals_total == 3 and s.goals_coverage.known == 1 and s.goals_coverage.total == 2
    assert s.goals_per_game == 3.0


def test_participant_alias_matching(client):
    vid = make_venue(client)
    make_event(client, vid, home="1. FC Kaiserslautern", away="Eintracht Frankfurt")
    with dbmod.SessionLocal() as db:
        p = db.scalar(select(Participant).where(Participant.name == "1. FC Kaiserslautern"))
        pid = p.id
    client.post(f"/participants/{pid}/edit", data={"name": "1. FC Kaiserslautern",
                                                   "aliases": "FCK, Lautern"})
    make_event(client, vid, date="2024-02-02", home="Eintracht Frankfurt", away="fck")
    r = client.get("/events", params={"team_id": pid, "role": "away"})
    assert r.text.count("/events/") >= 1
    with dbmod.SessionLocal() as db:
        assert db.scalar(select(Participant).where(Participant.name == "fck")) is None


SAMPLE = {
    "schema_version": 1,
    "event": {"date": "2023-05-20", "time": "15:30", "sport": "Fußball",
              "competition": "2. Bundesliga", "stage": "34. Spieltag",
              "venue": {"name": "Waldstadion", "name_at_event": "Deutsche Bank Park"},
              "attendance": 51500, "weather": "sonnig, 22 °C (DWD Station Frankfurt)"},
    "bouts": [{"home": "Eintracht Frankfurt", "away": "1. FC Kaiserslautern",
               "home_score": 1, "away_score": 2,
               "details": {"goals": [{"minute": 12, "player": "Boyd"}]}}],
    "sources": [{"url": "https://example.org/bericht", "field": "bouts"}],
    "open_questions": ["Zuschauerzahl in zwei Quellen unterschiedlich"],
}


def test_import_preview_and_apply_new_event(client):
    make_venue(client)
    text = json.dumps(SAMPLE)
    r = client.post("/import", data={"json": text})
    assert r.status_code == 200 and "Vorschau" in r.text and "vorhanden" in r.text
    r = client.post("/import", data={"json": text, "confirm": "1"}, follow_redirects=False)
    assert r.status_code == 303
    eid = int(r.headers["location"].rsplit("/", 1)[1])
    with dbmod.SessionLocal() as db:
        e = db.get(Event, eid)
        assert e.attendance == 51500 and e.visit is not None
        assert e.venue.name == "Waldstadion"
        assert "Deutsche Bank Park" in [a.name for a in e.venue.aliases]
        assert e.bouts[0].goals == 3 and len(e.sources) == 1
        assert e.time == dt.time(15, 30)


def test_import_respects_locked_and_personal_data(client):
    vid = make_venue(client)
    eid = make_event(client, vid)
    client.post(f"/events/{eid}/visit", data={"notes": "Gänsehaut", "cost": "25,50"})
    # manuell gepflegtes Feld -> gesperrt
    form = {"date": "2023-05-20", "sport_id": str(sport_id("Fußball")), "venue_id": str(vid),
            "attendance": "50000"}
    client.post(f"/events/{eid}/edit", data=form)
    with dbmod.SessionLocal() as db:
        assert "attendance" in db.get(Event, eid).locked_fields
    r = client.post("/import", data={"json": json.dumps(SAMPLE), "target_id": eid,
                                     "overwrite": "1", "confirm": "1"}, follow_redirects=False)
    assert r.status_code == 303
    with dbmod.SessionLocal() as db:
        e = db.get(Event, eid)
        assert e.attendance == 50000  # gesperrt, nicht überschrieben
        assert e.weather.startswith("sonnig")  # leer -> gesetzt
        assert e.visit.notes == "Gänsehaut" and e.visit.cost == 25.5
        assert len(e.bouts) == 1
    # zweiter Import dupliziert keine Quellen
    client.post("/import", data={"json": json.dumps(SAMPLE), "target_id": eid, "confirm": "1"})
    with dbmod.SessionLocal() as db:
        assert len(db.get(Event, eid).sources) == 1


def test_import_rejects_invalid(client):
    r = client.post("/import", data={"json": "{kaputt"})
    assert "Kein gültiges JSON" in r.text
    r = client.post("/import", data={"json": json.dumps({"event": {"sport": "Fußball"}})})
    assert "event.date fehlt" in r.text


def test_geojson_and_merge(client):
    v1 = make_venue(client)
    v2 = make_venue(client, name="Frankfurt Stadion Dublette", lat="", lon="")
    make_event(client, v1)
    make_event(client, v2, date="2022-01-01")
    data = client.get("/api/venues.geojson").json()
    assert len(data["features"]) == 1 and data["without_coordinates"][0]["id"] == v2
    client.post(f"/venues/{v2}/merge", data={"target_id": v1})
    data = client.get("/api/venues.geojson").json()
    assert data["features"][0]["properties"]["visits"] == 2
    with dbmod.SessionLocal() as db:
        v = db.get(Venue, v1)
        assert "Frankfurt Stadion Dublette" in [a.name for a in v.aliases]


def test_photos_scan_link_unlink_keeps_original(client, tmp_path):
    from PIL import Image
    from app.config import settings
    folder = settings.photo_root / "2023"
    folder.mkdir()
    img = folder / "IMG_1.jpg"
    exif = Image.Exif()
    exif[306] = "2023:05:20 16:01:00"
    Image.new("RGB", (800, 600), "red").save(img, exif=exif)
    from app import photos
    with dbmod.SessionLocal() as db:
        assert photos.scan(db)["added"] == 1
    vid = make_venue(client)
    eid = make_event(client, vid)
    r = client.get(f"/events/{eid}/photos")
    assert "IMG_1.jpg" in r.text
    with dbmod.SessionLocal() as db:
        pid = db.scalar(select(Photo.id))
    client.post(f"/events/{eid}/photos", data={"photo_id": str(pid)})
    assert client.get(f"/photo/{pid}/240").headers["content-type"] == "image/jpeg"
    # verschieben -> wird über Fingerabdruck wiedererkannt, Zuordnung bleibt
    (settings.photo_root / "neu").mkdir()
    img.rename(settings.photo_root / "neu" / "umbenannt.jpg")
    with dbmod.SessionLocal() as db:
        res = photos.scan(db)
        assert res["moved"] == 1 and res["added"] == 0
        assert db.get(Photo, pid).path == "neu/umbenannt.jpg"
        lid = db.scalar(select(PhotoLink.id))
    client.post(f"/photolinks/{lid}", data={"action": "remove", "back": f"/events/{eid}"})
    assert (settings.photo_root / "neu" / "umbenannt.jpg").exists()
    with dbmod.SessionLocal() as db:
        assert db.scalar(select(PhotoLink.id)) is None


def test_photo_path_traversal_blocked(client):
    vid = make_venue(client)
    r = client.post(f"/venues/{vid}/photos", data={"path": "../../etc/passwd"})
    assert r.status_code == 400


def test_on_this_day_and_milestones(client):
    vid = make_venue(client)
    today = dt.date.today()
    make_event(client, vid, date=today.replace(year=today.year - 5).isoformat(),
               home="A", away="B")
    from app import stats
    with dbmod.SessionLocal() as db:
        evs = stats.load_events(db)
    assert stats.on_this_day(evs)[0][0] == 5
    assert "Heute vor 5 Jahren" in client.get("/").text
    assert stats.milestones(evs)[0][1] == "1. Besuch"


def test_password_protection(client, monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "app_password", "geheim")
    r = client.get("/events", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/login"
    assert client.get("/health").status_code == 200
    client.post("/login", data={"password": "falsch"})
    assert client.get("/events", follow_redirects=False).status_code == 303
    client.post("/login", data={"password": "geheim"})
    assert client.get("/events").status_code == 200


def test_escaping(client):
    vid = make_venue(client, name="<script>x</script>")
    r = client.get(f"/venues/{vid}")
    assert "<script>x</script>" not in r.text
