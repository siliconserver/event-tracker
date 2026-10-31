# Betrieb: Docker auf der Synology DS420+, Build mit GitLab

## Überblick

- Ein Container (`event-tracker`), Port 8000 im Container.
- `/data` (beschreibbar): SQLite-Datenbank, Vorschaubilder, Sitzungsschlüssel. **Dieses Verzeichnis sichern.**
- `/photos` (nur lesend): der vorhandene Fotobestand des NAS. Die App verändert dort nichts.
- Zugriff über VPN. Optional zusätzlich ein Passwort (`APP_PASSWORD`).

## Image bauen (GitLab)

`.gitlab-ci.yml` führt bei jedem Push die Tests aus, baut das Image und legt es in der
GitLab Container Registry des Projekts ab (`$CI_REGISTRY_IMAGE:<commit>`, auf dem
Standard-Branch zusätzlich `:latest`). Der Build-Job braucht einen Runner mit
Docker-in-Docker (bei gitlab.com die Shared Runner; bei einem eigenen Runner `privileged = true`).

Das GitHub-Repository kann per GitLab „Repository mirroring“ (Pull) gespiegelt werden,
oder das Projekt zieht ganz nach GitLab um.

## Auf dem NAS starten

1. Ordner anlegen, z. B. `/volume1/docker/event-tracker` (File Station).
2. UID/GID des Benutzers ermitteln, dem der Ordner gehört (per SSH `id <benutzer>`), und in
   `docker-compose.yml` bei `user:` eintragen (Synology-Standard oft `1026:100`).
3. In `docker-compose.yml` den Fotopfad prüfen (Standard `/volume1/photo` bzw. der
   `Photos`-Ordner in den Benutzer-Homes, z. B. `/volume1/homes/christian/Photos`).
4. Bei privater Registry einmalig anmelden: `docker login registry.gitlab.com`
   (Deploy-Token mit `read_registry`).
5. Container Manager → Projekt → Erstellen → `docker-compose.yml` hochladen, oder per SSH:
   `EVENT_TRACKER_IMAGE=registry.gitlab.com/<gruppe>/event-tracker:latest docker compose up -d`
6. Aufruf im VPN: `http://<nas-ip>:8085`

Aktualisieren: `docker compose pull && docker compose up -d` (oder im Container Manager
„Projekt → Aktion → Erstellen“).

## Umgebungsvariablen

| Variable | Standard | Bedeutung |
|---|---|---|
| `DATA_DIR` | `/data` | Datenverzeichnis |
| `PHOTO_ROOT` | `/photos` | Wurzel des Fotobestands (nur lesend) |
| `APP_PASSWORD` | leer | Passwort für die Anmeldung; leer = keine Anmeldung |
| `SECRET_KEY` | automatisch | Sitzungsschlüssel; ohne Angabe wird er in `/data/.secret_key` erzeugt |
| `HOME_COUNTRY` | `Deutschland` | Grundlage für „nur Ausland“ und Meilensteine |
| `TILE_URL` | OpenStreetMap | Kartenkacheln; bei viel Nutzung eigenen/kommerziellen Anbieter eintragen |
| `TILE_ATTRIBUTION` | OSM-Hinweis | Quellenangabe der Karte |

Hinweis Karte: Die öffentlichen OSM-Kacheln sind für geringe private Nutzung gedacht
(Tile Usage Policy). Ein Offline-Download ist nicht vorgesehen.

## Sicherung

- Hyper Backup auf `/volume1/docker/event-tracker` einrichten (SQLite im WAL-Modus; für eine
  konsistente Kopie den Container kurz stoppen oder zusätzlich den JSON-Export nutzen).
- Vollständiger JSON-Export aller Tabellen: `http://<nas-ip>:8085/export.json`.
- Vorschaubilder (`/data/thumbs`) können jederzeit gelöscht werden, sie werden neu erzeugt.

## Ressourcen

Im Leerlauf rund 60–80 MB RAM. `mem_limit` steht in der Compose-Datei auf 512 MB. Das erste
Einlesen eines großen Fotobestands liest jede Datei kurz an (Fingerabdruck, EXIF) und kann
dauern; danach werden nur geänderte Dateien gelesen.

## Lokal entwickeln

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest -q
DATA_DIR=./data PHOTO_ROOT=./photos uvicorn app.main:get_app --factory --reload
```
