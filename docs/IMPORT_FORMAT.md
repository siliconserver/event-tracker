# Recherche-Austauschformat (Schema-Version 1)

Gilt für den ChatGPT-Weg (Rechercheauftrag auf der Event-Seite → „Recherche / JSON-Import“),
für spätere API-Adapter und für Sammelimporte. Alle Wege liefern in dieses Format.

## Aufbau

```json
{
  "schema_version": 1,
  "event": {
    "date": "2023-05-20",
    "time": "15:30",
    "sport": "Fußball",
    "title": null,
    "competition": "2. Bundesliga",
    "stage": "34. Spieltag",
    "is_final": false,
    "venue": {
      "name": "Fritz-Walter-Stadion",
      "name_at_event": "Fritz-Walter-Stadion",
      "city": "Kaiserslautern", "country": "Deutschland",
      "lat": 49.4345, "lon": 7.7765
    },
    "attendance": 49327,
    "weather": "sonnig, 21 °C (DWD-Station Kaiserslautern)",
    "report": "Kurze Zusammenfassung"
  },
  "bouts": [
    {
      "label": null,
      "home": "1. FC Kaiserslautern", "away": "Hannover 96",
      "home_score": 2, "away_score": 1,
      "winner": null, "method": null, "round": null,
      "details": {
        "goals": [{"minute": 20, "player": "Boyd", "team": "1. FC Kaiserslautern"}],
        "lineups": {}, "cards": [], "substitutions": [], "referee": null
      }
    }
  ],
  "sources": [{"url": "https://…", "title": "Spielbericht", "field": "bouts"}],
  "open_questions": ["Zuschauerzahl weicht zwischen Quellen ab"]
}
```

Pflicht sind nur `event.date` und (bei neuen Events) `event.sport` und `event.venue.name`.
Alles andere darf fehlen oder `null` sein. Bei Kampfabenden steht jeder Kampf als eigener
Eintrag in `bouts` (`home`/`away` = Kämpfer A/B, `winner`, `method`, `round`).

Sammelimport: eine Liste solcher Objekte oder `{"events": [ … ]}`.

## Regeln beim Import

- Vor dem Speichern wird immer eine Vorschau gezeigt.
- Spielstätten werden über Allzeitnamen **und** frühere Namen erkannt; `name_at_event` wird
  als früherer Name der Spielstätte gespeichert. Unbekannte Spielstätten werden neu angelegt.
- Vereine, Kämpfer und Wettbewerbe werden über Namen und alternative Schreibweisen erkannt.
- Leere Felder werden gefüllt. Vorhandene Werte werden nur überschrieben, wenn
  „überschreiben“ gewählt ist, und **nie**, wenn das Feld manuell gepflegt (🔒) ist.
- Spiele/Kämpfe werden nur angelegt, wenn noch keine erfasst sind (oder bei „überschreiben“,
  sofern nicht manuell korrigiert).
- Quellen und offene Fragen werden ergänzt, doppelte URLs übersprungen.
- Persönliche Besuchsdaten (Notizen, Kosten, Bewertungen, Fotos …) werden nie verändert.
- Gibt es am selben Tag in derselben Spielstätte schon ein Event, warnt die Vorschau.
