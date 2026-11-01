# Betrieb: Docker auf der Synology DS420+ oder einem Rootserver, Image aus der GitHub Container Registry

## Überblick

- Ein Container (`event-tracker`), Port 8000 im Container.
- `/data` (beschreibbar): SQLite-Datenbank, Vorschaubilder, Sitzungsschlüssel. **Dieses Verzeichnis sichern.**
- `/photos` (nur lesend): der vorhandene Fotobestand des NAS. Die App verändert dort nichts.
- **NAS im VPN:** ohne Anmeldung (`AUTH_ENABLED=false`, Standard in `docker-compose.yml`).
- **Öffentlich erreichbar** (Rootserver mit Traefik oder Synology Reverse Proxy): Anmeldung mit
  Benutzern, 2FA per TOTP und Rollen (`docker-compose.server.yml`).

## Image bauen (GitHub Actions → ghcr.io)

Das Image liegt öffentlich unter **`ghcr.io/siliconserver/event-tracker`**; zum Herunterladen
braucht es kein `docker login`.

`.github/workflows/docker-image.yml` läuft automatisch:

1. **test**: `pytest` mit Python 3.13.
2. **image**: baut für `linux/amd64` (DS420+ und Rootserver), startet den Container kurz und
   prüft `/health` (Rauchtest). Nur wenn das klappt, wird veröffentlicht.

| Auslöser | Tags |
|---|---|
| Push auf `main` | `:latest`, `:sha-<kurzer-commit>` |
| Git-Tag `v1.2.3` | `:1.2.3`, `:1.2`, `:sha-<kurzer-commit>` |
| Pull Request | nichts, nur bauen und testen |

Secrets sind nicht nötig, der Push läuft mit dem automatischen `GITHUB_TOKEN`. Der Build-Cache
liegt im GitHub-Actions-Cache, ohne Änderung an `requirements.txt` geht ein Build schnell.

**Einmalig nach dem ersten Lauf:** Neue Pakete sind bei GitHub zunächst privat. Auf
github.com → Profil → *Packages* → `event-tracker` → *Package settings* → *Danger Zone* →
*Change visibility* → **Public**. Ab dann ist jede neue Version ohne Anmeldung abrufbar.
Achtung: Wer das Image zieht, sieht den Python-Quellcode der App (nicht die Daten, die liegen
nur im Volume `/data`).

Version veröffentlichen: `git tag v1.0.0 && git push origin v1.0.0`. Wer feste Stände statt
`latest` betreiben will, trägt diesen Tag in `EVENT_TRACKER_IMAGE` ein.

## Auf dem NAS starten

1. Ordner anlegen, z. B. `/volume1/docker/event-tracker` (File Station).
2. UID/GID des Benutzers ermitteln, dem der Ordner gehört (per SSH `id <benutzer>`), und in
   `docker-compose.yml` bei `user:` eintragen (Synology-Standard oft `1026:100`).
3. In `docker-compose.yml` den Fotopfad prüfen (Standard `/volume1/photo` bzw. der
   `Photos`-Ordner in den Benutzer-Homes, z. B. `/volume1/homes/christian/Photos`).
4. Container Manager → Projekt → Erstellen → `docker-compose.yml` hochladen, oder per SSH:
   `docker compose up -d` (das Image `ghcr.io/siliconserver/event-tracker:latest` ist voreingestellt)
5. Aufruf im VPN: `http://<nas-ip>:8085`

Aktualisieren: `docker compose pull && docker compose up -d` (oder im Container Manager
„Projekt → Aktion → Erstellen“).

## Umgebungsvariablen

| Variable | Standard | Bedeutung |
|---|---|---|
| `DATA_DIR` | `/data` | Datenverzeichnis |
| `PHOTO_ROOT` | `/photos` | Wurzel des Fotobestands (nur lesend) |
| `AUTH_ENABLED` | `true` (NAS-Compose: `false`) | Anmeldung mit Benutzern; `false` nur in abgeschottetem Netz |
| `REQUIRE_2FA` | `true` | TOTP-2FA für alle Benutzer Pflicht |
| `COOKIE_SECURE` | `false` (Server-Compose: `true`) | Sitzungs-Cookie nur über HTTPS |
| `SESSION_DAYS` | `14` | Gültigkeit einer Anmeldung |
| `FORWARDED_ALLOW_IPS` | `127.0.0.1` | Proxys, deren `X-Forwarded-For` gilt (hinter Traefik: `*`, da kein offener Port) |
| `SECRET_KEY` | automatisch | Sitzungsschlüssel; ohne Angabe wird er in `/data/.secret_key` erzeugt |
| `HOME_COUNTRY` | `Deutschland` | Grundlage für „nur Ausland“ und Meilensteine |
| `TILE_URL` | OpenStreetMap | Kartenkacheln; bei viel Nutzung eigenen/kommerziellen Anbieter eintragen |
| `TILE_ATTRIBUTION` | OSM-Hinweis | Quellenangabe der Karte |

Hinweis Karte: Die öffentlichen OSM-Kacheln sind für geringe private Nutzung gedacht
(Tile Usage Policy). Ein Offline-Download ist nicht vorgesehen.

## Rootserver mit Traefik

`docker-compose.server.yml` setzt ein bestehendes Traefik mit externem Docker-Netz voraus
(Standardname `traefik`, Entrypoint `websecure`, Zertifikats-Resolver `letsencrypt`; alles per
Variable anpassbar: `TRAEFIK_NETWORK`, `TRAEFIK_ENTRYPOINT`, `TRAEFIK_CERTRESOLVER`).
Die App veröffentlicht keinen Port, HTTPS und HSTS kommen von Traefik.

```bash
mkdir -p data && sudo chown 1000:1000 data
DOMAIN=events.example.de docker compose -f docker-compose.server.yml up -d
docker exec -it event-tracker python -m app.cli create-user christian --role admin
```

Danach anmelden; beim ersten Login wird die 2FA eingerichtet (QR-Code für jede
Authenticator-App) und es werden 8 Wiederherstellungscodes angezeigt. Fotos sind auf dem
Server optional; ohne Foto-Volume bleibt nur die Fotofunktion leer.

## NAS über den Synology Reverse Proxy

Soll die App auf dem NAS ohne VPN erreichbar sein: in `docker-compose.yml`
`AUTH_ENABLED=true` und `COOKIE_SECURE=true` setzen, den Port nur lokal binden
(`127.0.0.1:8085:8000`) und in DSM unter Systemsteuerung → Anmeldeportal → Erweitert →
Reverse Proxy eine HTTPS-Regel auf `http://localhost:8085` anlegen (Zertifikat über DSM).
Bei benutzerdefinierten Kopfzeilen „WebSocket“ nicht nötig, aber `X-Forwarded-For` mitgeben und
`FORWARDED_ALLOW_IPS=*` setzen, damit die Login-Bremse die echte IP sieht.

## Benutzer und Rollen

| Rolle | Darf |
|---|---|
| Nur lesen | alles ansehen, eigenes Passwort und 2FA ändern |
| Lesen und schreiben | zusätzlich erfassen, bearbeiten, importieren, Fotos zuordnen, exportieren |
| Administrator | zusätzlich Benutzer anlegen, Rollen ändern, Passwörter/2FA zurücksetzen, sperren |

Schutzmaßnahmen: Passwörter mit scrypt gehasht (mind. 10 Zeichen), Kontosperre für 15 Minuten
nach 5 Fehlversuchen, Bremse je IP (10 Fehlversuche in 10 Minuten), TOTP-Codes nur einmal
gültig, Passwort- oder Rollenänderung meldet bestehende Sitzungen ab, Anfragen fremder
Herkunft werden abgelehnt, Sicherheits-Header (u. a. `X-Frame-Options: DENY`).
Benutzerdaten sind nicht im JSON-Export enthalten.

Kommandozeile im Container (`docker exec -it event-tracker python -m app.cli …`):
`create-user NAME --role admin|editor|viewer`, `set-password NAME`, `reset-2fa NAME`,
`unlock NAME`, `list-users`.

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
