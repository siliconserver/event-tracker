# Event-Tracker

Persönliches Archiv tatsächlich besuchter Sportveranstaltungen und Spielstätten
(Groundhopping): Fußball, MMA (z. B. Oktagon), später NFL. Selbst gehostet als
Docker-Container auf der Synology DS420+, Zugriff per VPN, Build über GitLab CI.

Das vollständige Konzept mit allen Entscheidungen steht in [docs/KONZEPT.md](docs/KONZEPT.md).

## Was die App kann

- **Besuche erfassen**, auch rückwirkend und ohne KI. Nur besuchte Events, keine Planung,
  kein Check-in. Alle Spiele/Kämpfe eines Events gelten als gesehen.
- **Spielstätten mit Allzeitnamen** (z. B. „Waldstadion“), früheren Namen mit
  Gültigkeitszeitraum und dem damaligen Namen je Besuch. Umbenennung oder Neubau am selben
  Ort erzeugt keine neue Spielstätte; Dubletten lassen sich zusammenführen.
- **Location-Seiten**: Besuche, erster/letzter Besuch, Sportarten, Innen-/Außenbilder, Karte.
- **Kombi-Karte** (Leaflet + Clustering) mit exakten Koordinaten und Filtern nach Zeitraum,
  Sportart, Wettbewerb.
- **Recherche per JSON**: die App erzeugt einen Rechercheauftrag (z. B. für ChatGPT),
  die Antwort wird mit Vorschau importiert. Manuell gepflegte Felder und persönliche Daten
  bleiben geschützt; Quellen und offene Fragen werden gespeichert. Format:
  [docs/IMPORT_FORMAT.md](docs/IMPORT_FORMAT.md).
- **Fotos aus dem NAS** als Verweise: Bestand einlesen, Fotos nach Aufnahmedatum (Eventtag ± n)
  auswählen, Titelbild, Reihenfolge, Bildunterschrift, innen/außen/Sitzplatz. HEIC wird für
  den Browser umgewandelt, verschobene Dateien werden über ihren Fingerabdruck wiedererkannt.
  Originale werden nie verändert.
- **Statistiken**: Jahre, Sportarten, Spielstätten, Länder, Wettbewerbe, Vereine mit S/U/N,
  Tore, Torschützen, Paarungen, Kämpfer, Siegmethoden, Kosten und Bewertungen. Besuche,
  Spiele/Kämpfe und Spielstätten werden getrennt gezählt; fehlende Werte zählen nicht als 0.
- **Persönliches**: Sitzplatz, Begleitung, Kosten, getrennte Bewertungen, Highlight, Ticket,
  Notizen; Reisen mit gemeinsamen Kosten; Jahresrückblick, „An diesem Tag“, Meilensteine,
  persönliche Rekorde; kombinierbare Suche (z. B. alle FCK-Auswärtsspiele, alle Finals,
  alle Spiele im Ausland).
- **Backup**: vollständiger JSON-Export unter `/export.json`.

## Technik

Python 3.13 · FastAPI · Jinja2 · SQLite (SQLAlchemy) · Leaflet · Pillow/pillow-heif.
Ein Container, kein separates Frontend-Build. Der Stack ist eine neue, vom Assistenten
getroffene Entscheidung (Konzept Abschnitt 3.9) und kann geändert werden.

```
app/            Anwendung (main.py = Routen, models.py = Datenmodell, importer.py, photos.py, stats.py)
app/templates/  Seiten
app/static/     CSS, Karte, Leaflet (im Repo, kein CDN)
tests/          pytest
docs/           Konzept, Betrieb, Importformat
```

## Schnellstart

```bash
docker build -t event-tracker .
docker run -p 8085:8000 -v $PWD/data:/data -v /pfad/zu/fotos:/photos:ro event-tracker
```

Betrieb auf der Synology, GitLab-Pipeline und Sicherung: [docs/BETRIEB.md](docs/BETRIEB.md).

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```
