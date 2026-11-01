# Projektübergabe: Persönliche Event- und Groundhopping-App

Stand: 31.10.2026
Grundlage: Projektgespräch „Groundia App erklärt“ vom 27.10.2026 und anschließende Wiederaufnahme.

> **Hinweis zur Übernahme ins Repository (31.10.2026):** Dieses Dokument ist die unveränderte Übergabe aus dem bisherigen Projektgespräch. Ergänzungen, die nach der Übergabe entschieden wurden, sind als **„Neue Entscheidung (31.10.2026)“** gekennzeichnet. Betroffen ist bisher nur der Betrieb: Die App wird als Docker-Container auf dem NAS gehostet und später über GitLab (CI) gebaut.

Dieses Dokument bündelt die rekonstruierbaren Anforderungen, Ideen, Entscheidungen und offenen Punkte. Es beschreibt den Konzeptstand; eine bereits vorhandene Implementierung ist im bisherigen Gespräch nicht dokumentiert.

Statuskennzeichnung:

- **Festgelegt:** ausdrücklich vom Nutzer gewünscht oder bestätigt.
- **Vorgeschlagen:** im Gespräch als Funktion oder technische Lösung eingebracht, aber nicht jeweils ausdrücklich bestätigt.
- **Offen:** noch nicht konkret entschieden oder technisch geprüft.
- **Überholt/verworfen:** früher angesprochen, durch spätere Entscheidungen ersetzt oder ausgeschlossen.

## 1) Ziel und Zweck des Projekts

### Grundidee

Eine eigene, plattformunabhängige Web-App als persönliches Archiv tatsächlich besuchter Sportveranstaltungen und Spielstätten.

Ausgangspunkt war die Beschäftigung mit Groundia. Der Nutzer möchte eine eigene Lösung mit manueller Erfassung, ausführlichen Veranstaltungsdaten, Fotos, Karten und persönlichen Statistiken.

Die App soll mehrere Perspektiven auf dieselbe Sammlung ermöglichen:

- Welche Veranstaltungen habe ich besucht?
- Welche Spiele und Kämpfe habe ich dabei gesehen?
- In welchen Stadien, Hallen und anderen Spielstätten war ich?
- Wann war ich dort und wie oft?
- Welche Vereine, Nationalmannschaften oder Kämpfer habe ich gesehen?
- Welche Erinnerungen, Bilder, Tickets und persönlichen Eindrücke gehören dazu?
- Wie verteilen sich meine Besuche nach Jahren, Orten, Ländern, Sportarten und Wettbewerben?
- Welche besonderen Erlebnisse, Meilensteine und Rekorde ergeben sich daraus?

### Nutzung und Betrieb

**Festgelegt:**

- Plattformunabhängige Web-App.
- Zentrale Datenhaltung, bevorzugt auf dem vorhandenen NAS.
- Manuelle Eingabe muss möglich sein.
- Einchecken am Veranstaltungsort ist unnötig.
- Vergangene Besuche müssen nachträglich erfasst werden können.
- Die App soll sportübergreifend funktionieren.

**Neue Entscheidung (31.10.2026):**

- Die App wird als Docker-Container gehostet (auf dem NAS).
- Gebaut wird später über GitLab (CI/CD).

### Sportlicher Umfang

**Ausdrücklich genannt:**

- Fußball.
- MMA, insbesondere Oktagon-Veranstaltungen.
- Später American Football beziehungsweise NFL.

**Weitere besprochene Beispiele:**

- Boxen tauchte als Beispiel für sportartspezifische Statistiken auf. Eine ausdrückliche Entscheidung, Boxen bereits zum Start umzusetzen, ist nicht dokumentiert.
- Stadionführungen, Museumsbesuche und Außenbesichtigungen wurden als mögliche zusätzliche Besuchsarten vorgeschlagen; siehe Abschnitt 2.

### Persönlicher Kontext

Der Nutzer ist Pfälzer und FCK-Fan, ausdrücklich nicht KSC-Fan. Er besucht und verfolgt trotzdem unterschiedliche Vereine und Sportarten.

Das ist insbesondere für Beispiele, Vereinsfilter und persönliche Auswertungen relevant. Eine Beschränkung der App auf den FCK wurde nicht gewünscht.

### Verbindliche Abgrenzung

- Erfasst werden tatsächlich besuchte Veranstaltungen.
- Keine Planung zukünftiger Events.
- Keine Wunschliste.
- Kein notwendiger Check-in.
- Alle Spiele beziehungsweise Kämpfe einer eingetragenen Veranstaltung gelten als gesehen.
- Der Nutzer kommt nach eigener Aussage nicht erst später zu Veranstaltungen; eine zusätzliche Auswahl „Welche Teile hast du tatsächlich gesehen?“ wird deshalb nicht benötigt.

## 2) Funktionen und Anforderungen

### 2.1 Manuelle Erfassung von Veranstaltungen und Besuchen

**Festgelegt:**

- Veranstaltungen und Besuche manuell anlegen.
- Auch ältere Besuche nachtragen.
- Die App bleibt ohne KI-Recherche nutzbar.
- Vorhandene Angaben können ergänzt und korrigiert werden.

Als Ausgangsdaten für die Erfassung und Recherche wurden genannt:

- Datum.
- Sportart.
- Ort beziehungsweise Spielstätte.
- Wettbewerb.
- Veranstaltung oder beteiligte Teams.

**Vorgeschlagene persönliche Besuchsfelder:**

- Notizen und Erinnerungen.
- Bewertung.
- Sitzplatz beziehungsweise Block.
- Fotos.
- Tickets und andere Erinnerungsstücke.
- Kosten.
- Begleitung.
- Persönliches Highlight.

Die genaue Formularstruktur, Pflichtfelder und Validierungsregeln wurden noch nicht festgelegt.

### 2.2 Recherche öffentlicher Veranstaltungsdaten

**Festgelegtes Ziel:**

Eine KI beziehungsweise Recherchefunktion soll zu einer Veranstaltung passende Informationen recherchieren und die manuelle Erfassung erleichtern.

Besprochen wurden insbesondere:

| Bereich | Gewünschte beziehungsweise vorgeschlagene Informationen |
|---|---|
| Allgemeines | Datum, Uhrzeit, Sportart, Wettbewerb, Spielstätte |
| Fußball | Beteiligte Teams, Ergebnis, Torschützen, Kader |
| Weitere Fußballdetails | Aufstellung, Ersatzbank, Karten, Wechsel, Schiedsrichter |
| MMA | Einzelne Kämpfe, beteiligte Kämpfer, Sieger, Siegermethode, Runde |
| Rahmenbedingungen | Wetter am Veranstaltungsort |
| Berichterstattung | News, Artikel, Spielberichte und Zusammenfassungen |
| Nachvollziehbarkeit | Quellen, offene Fragen und widersprüchliche Angaben |

Zuschauerzahlen wurden außerdem im Zusammenhang mit persönlichen Rekorden angesprochen. Sie sollen nur verwendet werden, wenn sie belegt sind.

### 2.3 Rechercheablauf und JSON-Import

**Vom Nutzer akzeptierter Ansatz:**

1. Der Nutzer legt eine Veranstaltung mit den bekannten Ausgangsdaten an.
2. Die App erzeugt einen Rechercheauftrag.
3. Dieser Auftrag kann beispielsweise in ChatGPT bearbeitet werden.
4. Die Recherche liefert strukturierte Daten als JSON zurück.
5. Die App importiert die Daten.
6. Vor dem endgültigen Speichern wird eine Vorschau gezeigt.
7. Angaben können geprüft und korrigiert werden.
8. Die übernommenen Daten werden mit ihren Quellen gespeichert.

Daneben wurde eine direkte Anbindung an eine kostenlose KI-API als mögliche Variante besprochen.

**Konzeptionell vorgesehene Regeln:**

- Fehlende Angaben bleiben leer.
- Keine erfundenen Ergebnisse oder Details.
- Unsicherheiten und Widersprüche sichtbar machen.
- Quellen möglichst den jeweiligen Angaben zuordnen.
- Manuelle Korrekturen vor unbeabsichtigtem Überschreiben schützen.
- Persönliche Besuchsdaten bei einer erneuten Recherche erhalten.
- Eine spätere ergänzende Recherche ermöglichen.
- Unterschiedliche Recherchewege sollen in dasselbe Datenmodell liefern.

**Weitere Importidee:**

CSV- oder JSON-Sammelimport für eine rückwirkend erfasste Sammlung. Ein konkretes Format oder eine bereits vorhandene Quelldatei wurde nicht festgelegt.

### 2.4 Veranstaltungen mit mehreren Spielen oder Kämpfen

Die App muss zwischen folgenden Ebenen unterscheiden können:

- Persönlicher Besuch.
- Veranstaltung.
- Einzelne Spiele oder Kämpfe innerhalb einer Veranstaltung.
- Besuchte Spielstätte.

Beispiel: Ein MMA-Abend ist eine Veranstaltung mit mehreren Kämpfen.

**Festgelegt:**

Alle Spiele beziehungsweise Kämpfe einer eingetragenen Veranstaltung gelten als gesehen.

**Wichtig für Statistiken:**

Die Anzahl besuchter Veranstaltungen und die Anzahl gesehener Spiele oder Kämpfe dürfen nicht vermischt werden.

Die ursprüngliche Idee, innerhalb eines Events nur bestimmte tatsächlich gesehene Programmpunkte anzukreuzen, wurde durch die Nutzerentscheidung überflüssig.

### 2.5 Spielstätten mit Allzeitnamen und Namenshistorie

**Festgelegt:**

Jede Spielstätte erhält einen dauerhaften, vom Nutzer gewählten Allzeitnamen.

Konkretes Beispiel:

- Das Stadion in Frankfurt heißt in der App „Waldstadion“.

Zusätzlich soll der zum jeweiligen Besuch gültige Veranstaltungs- beziehungsweise Sponsorenname erhalten bleiben.

**Besprochenes Verhalten:**

- Allzeitname als Hauptname in Listen, Karte und Übersichten.
- Historische Namen und alternative Schreibweisen für Suche und Zuordnung.
- Gegebenenfalls Zeiträume, in denen bestimmte Namen gültig waren.
- Beim historischen Besuch bleibt der damalige Name nachvollziehbar.
- Der damalige Name kann korrigiert werden.
- Eine Umbenennung erzeugt keine neue Spielstätte.
- Besuche unter unterschiedlichen Namen werden derselben Spielstätte zugeordnet.

### 2.6 Identität einer Spielstätte bei Umbauten und Neubauten

**Verbindliche Nutzerregel:**

| Situation | Behandlung in der App |
|---|---|
| Umbau einer bestehenden Spielstätte | Dieselbe Spielstätte |
| Neubau am exakt gleichen Standort | Dieselbe Spielstätte |
| Neubau an einem anderen Standort | Neue Spielstätte |
| Neuer Sponsorenname | Dieselbe Spielstätte |

Der Nutzer nannte den Stadionneubau des KSC am bisherigen Standort als Beispiel für dieselbe Spielstätte.

Diese Regel muss für Datenmodell, Kartenpunkte, Besuchshistorie und Statistik einheitlich gelten.

### 2.7 Eigene Detailseite für jede Location

**Ausdrücklich gewünscht:**

Der Nutzer möchte gezielt nach Veranstaltungsorten suchen und dort einen vollständigen Überblick bekommen.

Inhalte einer Location-Seite:

- Allzeitname.
- Frühere beziehungsweise alternative Namen.
- Innenbilder.
- Außenbilder.
- Wann der Nutzer dort war.
- Wie oft er dort war.
- Welche Veranstaltungen er dort gesehen hat.

**Weitere vorgeschlagene Ausgestaltung:**

- Erstes Besuchsdatum.
- Letztes Besuchsdatum.
- Chronologische Liste der Besuche beziehungsweise Veranstaltungen.
- Dort besuchte Sportarten.
- Bevorzugtes Innenbild.
- Bevorzugtes Außenbild.
- Titelbild.
- Sitzplatzangaben und zugehörige Sichtfotos.

**Fotozuordnung auf Location-Ebene:**

- Fotos können direkt einer Location zugeordnet werden.
- Fotos können einem konkreten Besuch zugeordnet werden.
- Besuchsfotos sollen auch über die zugehörige Location auffindbar sein.
- Dauerhafte Innen- und Außenbilder einer Spielstätte können unabhängig von einem bestimmten Besuch gepflegt werden.

### 2.8 Interaktive Kombi-Karte

**Vom Nutzer gewählt:**

Eine Kombi-Karte mit zusammengefassten Punkten bei großer Übersicht und einzelnen Spielstätten beim Hineinzoomen.

Verhalten:

- Herausgezoomt werden nahe beieinanderliegende Spielstätten zu einem Punkt mit Anzahl zusammengefasst.
- Hineingezoomt erscheinen die einzelnen Stadien, Hallen und Veranstaltungsorte.
- Antippen eines Ortes zeigt mindestens Name, Besuchsanzahl und zugehörige Veranstaltungen.
- Filter nach Zeitraum, Sportart und Wettbewerb.
- Verschiedene Sportarten am selben Veranstaltungsort bleiben derselben Location zugeordnet.

**Verbindliche Ortsgenauigkeit:**

- Exakte Spielstätten verwenden.
- Keine bloßen Stadtpunkte als Ersatz.
- Der Nutzer kennt seine Spielstätten auch rückwirkend.
- Koordinaten einmalig an der Spielstätte speichern und Besuche darauf beziehen.

**Benennung und Zählung:**

- Die Karte verwendet den Allzeitnamen.
- Umbenennungen erzeugen keine zusätzlichen Punkte.
- Neubau am selben Standort bleibt dieselbe Location.
- Neubau anderswo erzeugt eine neue Location.

Quellen- und Lizenzangaben für das Kartenmaterial sind zu beachten.

### 2.9 Statistiken

**Ausdrücklicher Nutzerwunsch:**

Statistiken nach Jahren, Orten, Sportarten, Vereinen und weiteren kombinierbaren Kriterien.

Die detaillierten Kennzahlen wurden im Gespräch als Ausgestaltung vorgeschlagen.

#### Zeitliche Auswertung

- Gesamter erfasster Zeitraum.
- Kalenderjahr.
- Saison.
- Frei gewählter Zeitraum.
- Entwicklung der Besuche und Sportarten über die Zeit.

#### Orte und Spielstätten

- Besuche je Spielstätte.
- Unterschiedliche besuchte Spielstätten.
- Erstmals besuchte Spielstätten.
- Städte.
- Länder.
- Häufigste beziehungsweise bevorzugte Spielstätten.

#### Sportarten

- Veranstaltungen je Sportart.
- Verteilung auf die verschiedenen Sportarten.
- Zeitliche Entwicklung.

#### Vereine und Nationalmannschaften

- Welche Teams wurden gesehen?
- Wie häufig?
- In welchen Stadien?
- Siege, Unentschieden und Niederlagen bei den besuchten Spielen.

#### Wettbewerbe

- Wettbewerbe.
- Ligen.
- Pokale.
- Turniere.
- Veranstaltungsserien.

#### Fußball

- Insgesamt gesehene Tore.
- Tore pro Spiel.
- Höchste beziehungsweise torreichste Ergebnisse.
- Häufigste Paarungen.
- Gesehene Torschützen.

#### MMA und vergleichbare Kampfsportauswertungen

- Gesehene Kämpfer.
- Anzahl gesehener Kämpfe.
- KO/TKO.
- Submission.
- Punktsiege.

Boxen war in diesem Zusammenhang ein Beispiel, keine gesondert bestätigte Startanforderung.

#### Persönliche Auswertung

- Kosten.
- Bewertungen.
- Lieblingsspielstätten.
- Persönliche Highlights.

#### Regeln für belastbare Statistiken

- Besuche, Veranstaltungen, Spiele/Kämpfe und unterschiedliche Spielstätten getrennt zählen.
- Keine Doppelzählung durch Namenswechsel.
- Fehlende Angaben nicht als null behandeln.
- Datenabdeckung kenntlich machen: Eine Auswertung kann nur die tatsächlich vorhandenen Daten berücksichtigen.

### 2.10 Fotos aus dem vorhandenen NAS-Bestand

**Ausgangslage des Nutzers:**

Die Fotos liegen bereits auf dem NAS und stehen in der Photos-App zur Verfügung. Im Gespräch wurde die Anbindung als Synology-Photos-/NAS-Integration behandelt.

**Darauf aufbauender Lösungsansatz:**

- Vorhandene Originalfotos einbinden.
- Keine erneute Ablage aller Originale in einer zweiten Fotosammlung.
- Die App speichert Zuordnungen beziehungsweise Verweise.
- Synology Photos bleibt die zentrale Fotoverwaltung.
- Zugriff auf die Originalordner zunächst lesend.
- Entfernen einer Fotozuordnung in der Event-App löscht nur den Verweis, nicht das Originalfoto.

**Vorgeschlagener Auswahlablauf:**

- Fotoauswahl innerhalb eines Besuchs.
- Mehrfachauswahl.
- Filter nach Aufnahmedatum.
- Als Beispiel wurde Veranstaltungstag plus/minus ein Tag genannt.
- Manuelle Bestätigung der Zuordnung.
- Aufnahmezeit und gegebenenfalls GPS-/EXIF-Daten können Zuordnungsvorschläge erleichtern.
- Eine KI ist für diese grundlegende Fotozuordnung nicht erforderlich.

**Darstellung und Pflege:**

- Galerie pro Besuch.
- Bilder auch über die Location auffindbar.
- Titelbild pro Besuch beziehungsweise Spielstätte.
- Reihenfolge der Bilder.
- Optionale Bildunterschriften.
- Kennzeichnung als Innen- oder Außenaufnahme.
- Bilddarstellung in Chronik und beim Kartenpunkt wurde ebenfalls angesprochen.
- Vorschau- und Anzeigeversionen bei Bedarf.

**Dateiformate und Wiedererkennung:**

- HEIC berücksichtigen und für die Browseranzeige gegebenenfalls konvertieren.
- Live Photos zunächst als Standbild behandeln.
- Pfad plus Dateifingerabdruck als vorgeschlagener Ansatz zur Wiedererkennung nach Verschieben oder Umbenennen.
- Die konkrete Implementierung dieser Wiedererkennung ist noch offen.

**Zugriff:**

- Geschützter Zugriff.
- Keine öffentlichen Fotofreigaben als Voraussetzung.
- Zugriff auf NAS-Dateien und Integration von Synology-Photos-Alben beziehungsweise -Suche sind unterschiedliche technische Aufgaben.
- Die direkte Nutzung von Photos-Alben und Photos-Suchfunktionen muss gesondert geprüft werden.

Eine allgemeine Videoverwaltung oder vollständige Live-Photo-Wiedergabe wurde nicht konkret spezifiziert.

### 2.11 Persönliche Erinnerungen und Besuchsqualität

Folgende Zusatzideen wurden vorgeschlagen:

| Feature | Besprochene Ausgestaltung |
|---|---|
| Sitzplatz | Sitzplatz beziehungsweise Block festhalten |
| Sichtfoto | Foto der Sicht vom eigenen Platz zuordnen |
| Begleitung | Festhalten, mit wem man dort war; kein eigener Account der Begleitperson nötig |
| Tickets | Ticket am Besuch hinterlegen |
| Erinnerungsstücke | Beispielsweise Programmhefte zuordnen |
| Bewertungen | Atmosphäre, Sicht und Organisation getrennt bewerten |
| Persönliches Highlight | Besonderen Moment des Besuchs festhalten |
| Notizen | Freie Erinnerungen ergänzen |

Der Gedanke hinter getrennten Bewertungen: Die Qualität des Besuchs soll unabhängig vom sportlichen Ergebnis beschrieben werden können.

Diese Punkte wurden vorgeschlagen; eine ausdrückliche Einzelbestätigung aller Felder ist nicht dokumentiert.

### 2.12 Ausdrücklich übernommene zusätzliche Ideen

Der Nutzer erklärte zu den Zusatzideen der damaligen unteren Tabelle:

„Die zusätzlichen Ideen in der unteren Tabelle finde ich super. Unbedingt merken.“

Damit wurden folgende sechs Funktionsbereiche ausdrücklich übernommen:

#### Jahresrückblick

Zusammenstellung eines Jahres mit:

- Besuchen.
- Neu besuchten Spielstätten.
- Ländern.
- Lieblingsbildern.
- Persönlichen Highlights.

Die konkrete Gestaltung oder ein Exportformat wurden nicht festgelegt.

#### „An diesem Tag“

- Erinnerungen an Besuche am gleichen Kalendertag früherer Jahre.
- Beispiel: „Heute vor fünf Jahren warst du …“
- Als möglicher Platz wurde die Startseite genannt.

Ein E-Mail- oder Push-Versand wurde dazu nicht festgelegt.

#### Meilensteine

Genannte Beispiele:

- 50. Besuch.
- 20. Spielstätte.
- Erstmals eine neue Sportart besucht.

Die Zahlen sind Beispiele; ein abschließender Katalog oder feste Schwellenwerte wurden nicht definiert.

#### Persönliche Rekorde

Genannte Beispiele:

- Torreichstes gesehenes Spiel.
- Größte belegte Zuschauerzahl bei einer besuchten Veranstaltung.
- Am häufigsten besuchte Location.

#### Reisen zusammenfassen

- Zusammengehörige Veranstaltungen einer Reise bündeln.
- Gemeinsame Fotos zuordnen.
- Gemeinsame Reisekosten erfassen.

Wie Reisekosten auf einzelne Veranstaltungen verteilt werden, wurde nicht konkret festgelegt.

#### Gezielte, kombinierbare Suche

Genannte Kriterien:

- Sportart.
- Land.
- Wettbewerb.
- Verein.
- Jahr.

Genannte Suchbeispiele:

- Alle Fußballspiele im Ausland.
- Alle besuchten Finals.
- Alle FCK-Auswärtsspiele.

Die allgemeine Suche nach Locations und ihren alternativen Namen gehört ebenfalls zum Konzept.

### 2.13 Datenpflege, Korrektur und Datensicherung

Vorgeschlagene Funktionen:

- Dublettenprüfung für Veranstaltungen.
- Dublettenprüfung für Spielstätten.
- Dublettenprüfung für Fotos beziehungsweise Fotozuordnungen.
- Korrektur versehentlicher Änderungen.
- Rückgängigmachen falscher Änderungen oder Rechercheergebnisse.
- Einheitliche Namen für Vereine, Wettbewerbe und Kämpfer.
- Alternative Schreibweisen zur Wiedererkennung und Suche.
- Schutz manuell korrigierter Angaben bei späteren Importen.
- Vollständiger Export beziehungsweise Backup von Datenbank, Zuordnungen und Einstellungen.

Ein konkretes Backupverfahren, Wiederherstellungsprozess oder vollständiges Exportformat wurde nicht festgelegt.

### 2.14 Weitere vorgeschlagene Besuchsarten

Angesprochen wurden:

- Stadionführung.
- Museumsbesuch.
- Außenbesichtigung einer Spielstätte.

Vorschlag war, diese als Location-Besuche getrennt von Live-Sportbesuchen zu zählen.

Dazu liegt keine ausdrückliche Annahme oder Ablehnung vor. Diese Idee darf daher nicht als bereits verbindlich beschlossene Erweiterung behandelt werden.

Insbesondere ist offen, ob und wie zwischen „Spielstätte besucht“ und „dort ein Spiel gesehen“ unterschieden werden soll.

### 2.15 Frühere, später ersetzte oder ausgeschlossene Ideen

Diese Punkte werden zur Vollständigkeit dokumentiert:

| Frühere Idee | Späterer Stand |
|---|---|
| Status „besucht / geplant / Wunschliste“ | Planung und Wunschliste ausgeschlossen; nur tatsächlich besuchte Events |
| Pro Event auswählen, welche Spiele/Fights tatsächlich gesehen wurden | Nicht benötigt; alle gehören als gesehen zum eingetragenen Event |
| Check-in am Veranstaltungsort | Nicht benötigt |
| Stadtpunkte als vereinfachte Kartenposition | Ausgeschlossen; exakte Spielstätten sind bekannt |
| Eigene Fotoablage der App als erste Version, NAS-Anbindung später | Nach Klärung des vorhandenen NAS-Fotobestands durch Verweise auf vorhandene Originale ersetzt |
| Erneuter Mehrfachupload vom iPhone/PC beziehungsweise per Drag-and-drop als primärer Fotoablauf | Ursprünglicher Vorschlag, durch NAS-Verweis-Konzept als Hauptweg überholt |

Die ursprüngliche Fotoidee enthielt bereits Galerien, Titelbilder, Bildunterschriften, Vorschaubilder, HEIC-Unterstützung und Metadaten. Diese Darstellungs- und Komfortideen bleiben für die NAS-Anbindung relevant.

## 3) Tech-Stack und Architektur

### 3.1 Vorhandene Infrastruktur

**Vom Nutzer genannt:**

- Synology DS420+.
- 6 GB RAM.
- Bereits vorhandener Fotobestand auf dem NAS.
- Fotos in der Photos-App verfügbar.

Im damaligen Gespräch wurde die NAS-Hardware als Intel Celeron J4025 mit zwei Kernen eingeordnet. Eine erneute Hardwareprüfung fand im Rahmen dieser Übergabe nicht statt.

### 3.2 Beschlossene technische Richtung

- Plattformunabhängige Web-App.
- Zentrale Datenhaltung bevorzugt auf dem NAS.
- Zugriff zunächst über VPN.
- Eine eigene Domain wurde als mögliche Alternative beziehungsweise spätere Ergänzung angesprochen.
- Manuelle Erfassung als eigenständig funktionierender Weg.
- Austauschbare Recherche-/KI-Schnittstelle.
- Einstieg mit kostenloser KI und/oder JSON-Import aus ChatGPT.
- Lokale KI als spätere Möglichkeit.
- **Neue Entscheidung (31.10.2026):** Betrieb als Docker-Container auf dem NAS.
- **Neue Entscheidung (31.10.2026):** Build später über GitLab (CI/CD).
- **Neue Entscheidung (01.11.2026):** Statt GitLab baut GitHub Actions das Image und veröffentlicht es öffentlich (ohne Login) in der GitHub Container Registry `ghcr.io/siliconserver/event-tracker`. Ersetzt die GitLab-Entscheidung vom 31.10.2026.

### 3.3 Vorgeschlagene Architekturbausteine

- Weboberfläche.
- Anwendungslogik.
- Zentrale Datenbank.
- Datei- beziehungsweise Dokumentzuordnungen.
- Lesender Zugriff auf vorhandene Fotoordner.
- Rechercheanbieter über austauschbare Adapter.
- Gemeinsames Datenformat für Rechercheergebnisse.
- Importvorschau vor Übernahme.
- Kartenansicht.
- Statistikfunktionen.
- Export und Backup.

~~Docker-Container auf dem NAS wurden als mögliche Betriebsform vorgeschlagen.~~ Eine konkrete Containerarchitektur wurde noch nicht erstellt.

**Neue Entscheidung (31.10.2026):** Die App wird als Docker-Container auf dem NAS gehostet; Docker ist damit nicht mehr nur Vorschlag, sondern festgelegte Betriebsform. Das Image wird später über eine GitLab-CI/CD-Pipeline gebaut. Weiterhin offen sind die konkrete Containeraufteilung (z. B. App und Datenbank getrennt), die Compose-Konfiguration, die Image-Registry, das Deployment aufs NAS sowie die Einbindung der Foto- und Datenvolumes.

### 3.4 Öffentliche Veranstaltungsdaten und private Besuchsdaten

Die Daten sollen logisch getrennt werden:

**Öffentlich recherchierbare Fakten:**

- Veranstaltung.
- Teams beziehungsweise Kämpfer.
- Wettbewerb.
- Spielstätte.
- Uhrzeit.
- Ergebnis.
- Sportliche Details.
- Wetter.
- Berichte und Quellen.

**Persönliche Daten:**

- Eigener Besuch.
- Notizen.
- Kosten.
- Tickets.
- Begleitung.
- Bewertungen.
- Highlights.
- Fotozuordnungen.

„Öffentliche Daten“ bezeichnet hier die Art der recherchierten Informationen. Daraus folgt keine beschlossene öffentliche Veröffentlichung der App oder der Sammlung.

### 3.5 Rechercheanbieter und Kosten

**Festgelegte Richtung:**

Die Recherche darf nicht fest an einen einzigen Anbieter gekoppelt werden.

**Besprochene Möglichkeiten:**

1. Manueller Rechercheauftrag an ChatGPT mit JSON-Rückgabe.
2. Kostenlose API, insbesondere Gemini als damaliger Kandidat.
3. Später lokale KI.

**Besprochene Kostenregel:**

Kein automatischer Wechsel auf eine kostenpflichtige Variante.

Im damaligen Gespräch wurden ChatGPT-Nutzung und API-Nutzung getrennt betrachtet. Der halbautomatische JSON-Austausch wurde gerade als eigenständiger Weg besprochen.

Bei Gemini wurde damals ein Beispiel von bis zu 500 Suchanfragen pro Tag genannt, gleichzeitig aber auf weitere Modell- und Projektlimits hingewiesen. Diese Zahl ist eine historische Gesprächsangabe, kein in dieser Übergabe aktuell geprüftes Kontingent und keine Zusage für 500 vollständige Event-Recherchen.

### 3.6 Lokale KI als spätere Option

Damals konkret vorgeschlagen:

- Kleine Modelle mit ungefähr 1–2 Milliarden Parametern.
- Qwen2.5-1.5B-Instruct als Beispiel.
- 4-Bit-Quantisierung.
- llama.cpp als mögliche Laufzeit.
- Begrenzte Textmengen.
- Ein Bericht nach dem anderen.
- Schwerpunkt eher auf Textextraktion und Strukturierung.

Besprochene Einschränkungen:

- Mit 2 GB RAM wurde paralleler Betrieb neben DSM und App als nicht sinnvoll eingeschätzt.
- Nach Bestätigung von 6 GB RAM wurde ein Testbetrieb als mögliche spätere Option betrachtet.
- DSM, Datenbank, App und Modell konkurrieren um Ressourcen.
- Geschwindigkeit und Speicherverbrauch müssen praktisch geprüft werden.
- Ein lokales Sprachmodell ersetzt keinen Websuch- oder Seitenabrufdienst.

Diese Überlegungen sind keine bereits umgesetzte oder durch Messungen bestätigte Architektur.

### 3.7 Karten

- OpenStreetMap wurde als Kartenbasis vorgeschlagen.
- Quellenangaben und Nutzungsbedingungen berücksichtigen.
- Clustering für die Kombi-Karte.
- Koordinaten an der Spielstätte speichern.

**Noch offen:**

- Kartenbibliothek.
- Konkreter Karten-/Tile-Anbieter.
- Geocoding.
- Quelle beziehungsweise Eingabeverfahren der Koordinaten.
- Nutzungsgrenzen und technische Einbindung.

Ein Offline-Download öffentlicher Kartentiles wurde als problematischer Nutzungsfall angesprochen. Daraus wurde keine Offline-Kartenfunktion beschlossen. Die Bedingungen des tatsächlich gewählten Anbieters müssen bei der Umsetzung geprüft werden.

### 3.8 Noch nicht festgelegter Stack

Nicht verbindlich ausgewählt wurden:

- Programmiersprache.
- Frontend-Framework.
- Backend-Framework.
- Datenbankprodukt.
- Datenbankzugriff oder ORM.
- Authentifizierungslösung.
- Konkrete Docker-/Compose-Konfiguration. *(Neue Entscheidung (31.10.2026): Docker als Betriebsform steht fest; offen ist nur die konkrete Konfiguration.)*
- Konkrete GitLab-CI/CD-Pipeline. *(Neu ergänzt am 31.10.2026: GitLab als Build-Werkzeug steht fest; Pipeline, Runner und Registry sind offen.)*
- Reverse-Proxy- oder Domainkonfiguration.
- Kartenbibliothek.
- Konkrete Synology-Photos-Schnittstelle.
- Verbindliches JSON-Schema.

### 3.9 Gewählter Stack der ersten Version

**Neue Entscheidung (31.10.2026):** Auf Wunsch des Nutzers („Schreibe auch die Software als Container“) wurde eine erste Version umgesetzt. Den Stack hat der Assistent gewählt; er ist bewusst schlank für die DS420+ und kann geändert werden:

- Python 3.13 mit FastAPI, serverseitig gerenderte Seiten (Jinja2), kein separates Frontend-Build.
- SQLite als Datenbank (eine Datei im Datenvolume, einfach zu sichern), Zugriff über SQLAlchemy.
- Leaflet mit Leaflet.markercluster für die Kombi-Karte, Kacheln standardmäßig von OpenStreetMap (per `TILE_URL` austauschbar). Die Bibliotheken liegen im Repository, kein CDN nötig.
- Pillow und pillow-heif für Vorschaubilder inklusive HEIC.
- Ein einzelner Container, Fotos nur lesend eingebunden, Anmeldung mit Benutzern, TOTP-2FA und Rollen (im VPN abschaltbar, siehe 3.10).
- GitLab CI: Tests, dann Image-Build und Push in die GitLab Container Registry.

Details zu Betrieb und Import: `docs/BETRIEB.md`, `docs/IMPORT_FORMAT.md`.

### 3.10 Betrieb auf einem Rootserver, Login und Rollen

**Neue Entscheidung (31.10.2026):** Die App soll alternativ auf einem Rootserver laufen, dort hinter dem vorhandenen **Traefik** (kein Caddy). Dafür:

- Anmeldung mit Benutzern und **2FA per TOTP**, verpflichtend.
- Benutzer anlegen mit Rolle **nur lesen** oder **lesen und schreiben**; zusätzlich eine Administratorrolle für die Benutzerverwaltung (Ergänzung des Assistenten).
- Auf dem NAS im VPN kann die Anmeldung abgeschaltet bleiben; alternativ Betrieb über den Synology Reverse Proxy mit Anmeldung.
- Die Fotofunktion ist auf dem Server optional.

Mehrbenutzerbetrieb heißt hier: mehrere Zugänge auf dieselbe Sammlung, keine getrennten Sammlungen je Benutzer.

## 4) Datenmodell

### Einordnung

Ein implementiertes Datenbankschema existiert im dokumentierten Gespräch noch nicht.

Die folgende Struktur fasst die besprochenen fachlichen Objekte und Beziehungen zusammen. Die Bezeichnungen sind keine bereits angelegten Tabellen oder verbindlichen Codebezeichner.

### 4.1 Fachliche Objekte

| Objekt | Besprochene Inhalte und Zweck |
|---|---|
| Spielstätte / Location | Allzeitname, Ort, Stadt, Land, exakte Koordinaten, historische/alternative Namen, Innen-/Außenbilder |
| Namenshistorie | Alternative beziehungsweise historische Namen einer Spielstätte, gegebenenfalls Gültigkeitszeiträume |
| Veranstaltung | Datum, Uhrzeit, Sportart, Wettbewerb, Spielstätte, Veranstaltungstitel und allgemeine Fakten |
| Spiel / Kampf | Einzelner sportlicher Bestandteil einer Veranstaltung, Beteiligte, Ergebnis und sportartspezifische Details |
| Persönlicher Besuch | Persönliche Zuordnung zur Veranstaltung, Sitzplatz, Notizen, Bewertungen, Kosten, Begleitung, Highlights |
| Verein / Nationalmannschaft | Einheitliche Identität, Name, alternative Schreibweisen und Beteiligung an Spielen |
| Sportler / Kämpfer | Einheitliche Identität, Name, alternative Schreibweisen und Beteiligung an Kämpfen beziehungsweise sportlichen Details |
| Wettbewerb / Serie | Liga, Pokal, Turnier, Wettbewerb oder Veranstaltungsserie |
| Sportart | Grundlage für Filter, Statistik und passende Detailfelder |
| Foto | Verweis auf vorhandenes NAS-Original, Dateifingerabdruck als vorgeschlagene Wiedererkennung, Metadaten und gegebenenfalls Vorschau |
| Fotozuordnung | Verbindung zu Besuch und/oder Location, Bildunterschrift, Reihenfolge, Titelbild- und Innen-/Außenkennzeichnung |
| Dokument / Erinnerungsstück | Ticket, Programmheft oder ähnlicher Anhang zum Besuch |
| Rechercheergebnis / Quelle | Gefundene Angaben, zugehörige Quellen, offene Fragen und Widersprüche |
| Reise | Zusammenfassung zugehöriger Veranstaltungen mit gemeinsamen Fotos und Reisekosten |

### 4.2 Wichtige Beziehungen

- Eine Spielstätte kann viele Veranstaltungen und Besuche haben.
- Verschiedene Sportarten können dieselbe Spielstätte nutzen.
- Eine Veranstaltung kann mehrere Spiele oder Kämpfe enthalten.
- Ein persönlicher Besuch enthält persönliche Daten zur besuchten Veranstaltung.
- Teams und Kämpfer müssen wiedererkennbar sein, damit sie über mehrere Veranstaltungen ausgewertet werden können.
- Eine Reise kann mehrere Veranstaltungen zusammenfassen.
- Fotos können Besuchen und Locations zugeordnet sein.
- Ein Besuchsfoto soll über die Location ebenfalls erreichbar sein.
- Mehrere historische Namen gehören zu derselben Spielstättenidentität.
- Quellen müssen recherchierte Angaben nachvollziehbar machen.

Die genaue technische Beziehung zwischen Besuch und Veranstaltung sowie die Umsetzung einzelner Sportdetails in Tabellen oder strukturierten Feldern sind noch offen.

### 4.3 Sportartspezifische Daten

**Fußball:**

- Teams.
- Ergebnis.
- Torschützen.
- Kader.
- Aufstellung.
- Ersatzbank.
- Karten.
- Wechsel.
- Schiedsrichter.

**MMA:**

- Kämpfer.
- Sieger.
- Siegermethode.
- Runde.

**American Football/NFL:**

Als spätere Sportart vorgesehen; ein detailliertes Feldschema wurde noch nicht besprochen.

### 4.4 Fachliche Regeln und Datenqualität

- Historischer Stadionname und dauerhafte Spielstättenidentität sind unterschiedliche Informationen.
- Umbau oder Neubau am selben Standort erzeugt keine neue Spielstätte.
- Neubau an einem anderen Standort erzeugt eine neue Spielstätte.
- Veranstaltungen und ihre einzelnen Spiele/Kämpfe getrennt auswerten.
- Alle erfassten Spiele/Kämpfe eines besuchten Events gelten als gesehen.
- Fehlende Daten als fehlend behandeln, nicht als null oder geschätzten Wert.
- Manuell korrigierte Angaben gegen unbeabsichtigtes Überschreiben schützen.
- Persönliche Daten nicht durch Rechercheimporte ersetzen.
- Alternative Schreibweisen dürfen keine ungewollten neuen Teams, Kämpfer oder Wettbewerbe erzeugen.
- Das Entfernen einer Fotozuordnung darf das NAS-Original nicht löschen.
- Datenabdeckung bei Statistiken berücksichtigen.

### 4.5 Recherche-Austauschformat

Als inhaltliche Bestandteile wurden besprochen:

- Veranstaltung.
- Details.
- Quellen.
- Offene Fragen.

Es gibt noch keine verbindlichen Feldnamen, Datentypen, Schema-Versionen oder Beispielpayloads. Diese müssen bei der Implementierung definiert werden.

## 5) Getroffene Entscheidungen samt Begründung

Die Begründungen sind aus den Nutzerangaben und dem Gesprächszusammenhang zusammengefasst.

| Entscheidung | Status | Begründung |
|---|---|---|
| Eigene plattformunabhängige Web-App | Festgelegt | Persönliche Sammlung mit eigenen Anforderungen und geräteübergreifender Nutzung |
| Zentrale Ablage bevorzugt auf dem NAS | Festgelegt | Vorhandene Infrastruktur und zentraler Datenbestand |
| Zunächst Zugriff über VPN | Festgelegte Richtung | Gewünschter Zugang zur privaten NAS-Anwendung |
| Manuelle Erfassung bleibt möglich | Festgelegt | Besuche müssen unabhängig von KI und vorhandenen Online-Daten erfasst werden können |
| Kein Check-in erforderlich | Festgelegt | Manuelle und rückwirkende Erfassung genügt |
| Nur tatsächlich besuchte Events | Festgelegt | Die App ist ein persönliches Besuchsarchiv |
| Keine Planung und Wunschliste | Festgelegt | Vom Nutzer ausdrücklich ausgeschlossen |
| Alle Spiele/Fights eines Events zählen als gesehen | Festgelegt | Nutzer besucht Veranstaltungen vollständig |
| Fußball und MMA, später NFL | Festgelegter Umfang | Genannte Interessen und Erweiterungsrichtung |
| Austauschbare Recherche-Schnittstelle | Festgelegt | Anbieter und später lokale KI sollen wechselbar bleiben |
| Start mit Gratis-KI und/oder ChatGPT-JSON | Festgelegt | Akzeptierter Einstieg ohne sofortige lokale KI-Lösung |
| Keine automatische kostenpflichtige Ausweichlösung | Vorgeschlagene Betriebsregel | Kosten sollen kontrollierbar bleiben |
| Öffentliche Fakten und persönliche Daten trennen | Besprochenes Architekturprinzip | Recherche soll persönliche Erinnerungen und Eingaben nicht überschreiben |
| Eigener Allzeitname je Spielstätte | Festgelegt | Dauerhafte, persönliche und von Sponsorenwechseln unabhängige Benennung |
| Damaligen Namen je Besuch erhalten | Besprochenes Konzept | Historische Bezeichnung bleibt nachvollziehbar |
| Umbau/Neubau am selben Ort bleibt dieselbe Spielstätte | Festgelegt | Ausdrückliche Definition des Nutzers |
| Neubau an anderer Stelle ist eine neue Spielstätte | Festgelegt | Neuer Standort gilt als neuer Ort |
| Exakte Spielstätten statt Stadtpunkte | Festgelegt | Die tatsächlich besuchten Orte sind bekannt |
| Kombi-Karte mit Clustering | Festgelegt | Überblick bei großer Entfernung und genaue Orte beim Hineinzoomen |
| Bestehende NAS-Fotos einbinden | Festgelegte Richtung | Bilder sind bereits zentral vorhanden |
| Verweise statt zweiter Originalsammlung | Darauf aufgebauter Lösungsansatz | Doppelte Originalablage vermeiden und vorhandene Fotoverwaltung weiter nutzen |
| Eigene Location-Seiten | Festgelegt | Orte sollen mit Bildern, Besuchshäufigkeit und Historie durchsuchbar sein |
| Jahresrückblick, „An diesem Tag“, Meilensteine, Rekorde, Reisen und kombinierbare Suche | Ausdrücklich übernommen | Nutzer hat die gesamte entsprechende Ideenliste bestätigt |
| Stadionführung/Museum/Außenbesichtigung als separate Besuchsarten | Offen | Vorgeschlagen, aber nicht ausdrücklich entschieden |
| Betrieb als Docker-Container auf dem NAS | **Neue Entscheidung (31.10.2026):** Festgelegt | Vom Nutzer nach der Übergabe ausdrücklich so festgelegt |
| Build über GitLab (CI/CD), später | **Neue Entscheidung (31.10.2026):** Festgelegt | Vom Nutzer nach der Übergabe ausdrücklich so festgelegt |
| Alternativ Rootserver hinter Traefik, Login mit TOTP-2FA, Rollen lesen/schreiben | **Neue Entscheidung (31.10.2026):** Festgelegt | Öffentlicher Zugriff ohne VPN braucht echte Anmeldung |
| NAS im VPN ohne Anmeldung oder über Synology Reverse Proxy | **Neue Entscheidung (31.10.2026):** Festgelegt | Im abgeschotteten Netz genügt der VPN-Schutz |

## 6) Aktueller Stand: Was fertig ist, was offen ist

### Inhaltlich ausgearbeitet

- Grundidee und Zweck.
- Wesentliche Sportarten.
- Abgrenzung auf tatsächlich besuchte Veranstaltungen.
- Regel zur vollständigen Teilnahme an einem Event.
- Regeln zur Identität einer Spielstätte.
- Allzeitnamen und historische Namen.
- Kombi-Karte mit exakten Spielstätten.
- Gewünschte Statistikbereiche.
- Location-Seiten.
- Fotoeinbindung aus dem bestehenden NAS-Bestand.
- Halbautomatischer Recherche-/JSON-Ablauf.
- Austauschbarkeit des Rechercheanbieters.
- Die sechs ausdrücklich übernommenen Zusatzfunktionen.

„Ausgearbeitet“ bedeutet hier konzeptionell beschrieben, nicht programmiert.

### Nicht als fertig dokumentiert

- Kein lauffähiger Prototyp. *(Stand 31.10.2026: erste Version im Repository, siehe Abschnitt 3.9 und README.)*
- Keine eingerichtete Web-App.
- Kein dokumentiertes Repository. *(Stand 31.10.2026: Repository `siliconserver/event-tracker` auf GitHub angelegt; dieses Dokument liegt dort unter `docs/KONZEPT.md`.)*
- Kein implementiertes Datenbankschema.
- Keine geschriebene Importfunktion.
- Keine angebundene KI.
- Keine getestete lokale KI.
- Keine umgesetzte Fotoanbindung.
- Keine implementierte Karte.
- Keine fertigen Statistiken.
- Keine eingerichtete Datensicherung.
- Keine dokumentierten Tests.
- Keine angelegte oder konfigurierte Betriebsumgebung für dieses Projekt.

### Noch offene Entscheidungen und Prüfungen

- Konkreter Tech-Stack.
- Projektname.
- Gestaltung und Navigation.
- Technisches Datenbankschema.
- JSON-Schema und CSV-Importformat.
- Pflichtfelder und Formularabläufe.
- Exakte Namensnormalisierung und Dublettenlogik.
- Kartenbibliothek, Tile-Anbieter und Koordinatenerfassung.
- NAS-Pfade und Zugriffsrechte.
- Einbindung von Synology-Photos-Alben und -Suche.
- Foto-Vorschauen und HEIC-Konvertierung.
- Robuste Wiedererkennung verschobener Fotos.
- Authentifizierung und konkrete Zugriffskonfiguration.
- Backup- und Wiederherstellungsverfahren.
- Kosten- und Kontingentgrenzen eines gewählten Rechercheanbieters.
- Praktische Eignung lokaler KI.
- Genaue Bewertungsskalen.
- Konkrete Meilensteine und Rekorddefinitionen.
- Verteilung gemeinsamer Reisekosten.
- Behandlung zusätzlicher Location-Besuchsarten wie Stadionführungen.
- Priorisierung und Umfang einer ersten Version.
- *(Neu ergänzt am 31.10.2026)* Konkrete Docker-/Compose-Konfiguration, GitLab-Pipeline, Image-Registry und Deployment-Weg aufs NAS.

Mehrbenutzerbetrieb, Rollenmodell, allgemeiner Offlinebetrieb und ein konkreter Installations-/PWA-Umfang wurden nicht festgelegt. *(Neue Entscheidung (31.10.2026): Benutzer mit Rollen und 2FA, siehe Abschnitt 3.10.)*

## 7) Bekannte Probleme

Es gibt noch keine dokumentierten Programmfehler einer bestehenden Anwendung. Bekannt sind fachliche und technische Problemstellen aus der Planung.

### 7.1 Lückenhafte historische Daten

- Alte Veranstaltungsdaten können unvollständig sein.
- Besonders kleinere Ligen oder Veranstaltungen können schlecht dokumentiert sein.
- Kader, Aufstellungen und Schiedsrichter sind nicht immer öffentlich auffindbar.
- Fehlende Werte dürfen nicht erfunden werden.

### 7.2 Widersprüchliche Rechercheergebnisse

- Unterschiedliche Quellen können unterschiedliche Angaben liefern.
- Quellen und Unsicherheiten müssen nachvollziehbar bleiben.
- Importvorschau und manuelle Korrektur wurden deshalb vorgesehen.
- Eine spätere Recherche darf sorgfältig korrigierte Angaben nicht wieder ersetzen.

### 7.3 Wetterdaten

- Historisches Wetter ist ortsbezogen.
- Daten können auf Messstationen oder Modellen beruhen.
- Die Genauigkeit am konkreten Stadion beziehungsweise zur konkreten Uhrzeit darf nicht vorgetäuscht werden.

### 7.4 Zugriff auf Artikel und Berichte

- Bezahlschranken.
- Gesperrte oder nicht mehr verfügbare Seiten.
- Fehlende historische Berichte.
- Eingeschränkte Abrufbarkeit.

### 7.5 Sprachmodell und Internetzugriff sind getrennte Bausteine

- Ein Modell kann Texte auswerten, ohne selbst recherchieren zu können.
- Auch eine lokale KI benötigt für aktuelle oder historische Webrecherche einen gesonderten Such-/Abrufweg.
- Die Architektur muss diese Trennung berücksichtigen.

### 7.6 Kosten und Kontingente

- Kostenlose Angebote haben Grenzen.
- Modell-, Such- und Projektlimits können voneinander abweichen.
- Frühere Kontingentangaben müssen vor Umsetzung neu geprüft werden.
- Keine unbemerkte Umschaltung auf kostenpflichtigen Betrieb.

### 7.7 Ressourcen des NAS

- DSM, App, Datenbank, Fotoverarbeitung und gegebenenfalls KI teilen sich die Hardware.
- Lokale KI-Leistung wurde noch nicht gemessen.
- Kleine Modelle und begrenzte Einzelaufträge wurden als möglicher Ansatz diskutiert.

### 7.8 Fotoeinbindung

- Zugriff auf NAS-Dateien ist nicht automatisch gleichbedeutend mit Zugriff auf alle Synology-Photos-Funktionen.
- Verschieben oder Umbenennen kann einfache Pfadverweise ungültig machen.
- Pfad plus Dateifingerabdruck wurde als Gegenmaßnahme vorgeschlagen.
- HEIC muss für die Browserdarstellung berücksichtigt werden.
- Live Photos sind zunächst nur als Standbild vorgesehen.
- Berechtigungen und Verfügbarkeit der Originalordner müssen geklärt werden.

### 7.9 Dubletten und Identitäten

- Sponsorennamen können dieselbe Spielstätte unterschiedlich erscheinen lassen.
- Verschiedene Schreibweisen können Teams, Wettbewerbe oder Kämpfer doppelt anlegen.
- Mehrfachimporte können Veranstaltungen oder Fotozuordnungen verdoppeln.
- Die Identitäts- und Dublettenlogik ist fachlich wichtig, aber noch nicht implementiert.

### 7.10 Irreführende Statistiken

- Ein Event mit vielen Kämpfen darf nicht mit derselben Anzahl Stadionbesuche verwechselt werden.
- Fehlende Tore, Zuschauerzahlen oder Kosten dürfen nicht als null gerechnet werden.
- Datenabdeckung muss erkennbar sein.
- Umbenennungen und Umbauten dürfen die Spielstättenanzahl nicht künstlich erhöhen.

### 7.11 Kartennutzung

- Lizenz- und Quellenangaben müssen stimmen.
- Bedingungen des gewählten Karten-/Tile-Anbieters müssen berücksichtigt werden.
- Eine Offline-Kartenlösung ist nicht beschlossen.

## 8) Nächste Schritte

Eine verbindliche Entwicklungsreihenfolge wurde bisher nicht beschlossen. Die folgende Reihenfolge ist eine aus dem Konzept abgeleitete Übergabeempfehlung.

### Schritt 1: Technischen Rahmen konkretisieren

- Web-Stack und Datenbank auswählen.
- Betrieb auf der DS420+ planen.
- ~~Docker-Einsatz konkret entscheiden.~~ *Neue Entscheidung (31.10.2026): Docker ist entschieden. Stattdessen: Container-Aufteilung, Compose-Datei und Volumes für Daten und Fotos (lesend) festlegen.*
- *(Neu ergänzt am 31.10.2026)* GitLab-CI/CD-Pipeline für den Image-Build und den Weg des Images aufs NAS (Registry, Deployment) planen.
- NAS-Pfade und lesenden Fotozugriff klären.
- VPN-Zugriff und Authentifizierung konkretisieren.
- Prüfen, welche Synology-Photos-Funktionen technisch nutzbar sind.

### Schritt 2: Fachliches Modell und Importformat festlegen

- Spielstättenidentität und Allzeitnamen modellieren.
- Besuche, Veranstaltungen und Spiele/Kämpfe sauber unterscheiden.
- Öffentliche Fakten und persönliche Daten trennen.
- Foto-, Quellen- und Reisezuordnungen definieren.
- Einheitliches JSON-Format festlegen.
- Umgang mit fehlenden Werten, Quellen und manuell geschützten Feldern bestimmen.
- Dublettenregeln definieren.

### Schritt 3: Manuell nutzbaren Kern bauen

- Spielstätten anlegen und bearbeiten.
- Veranstaltungen und Besuche erfassen.
- Spiele beziehungsweise Kämpfe zuordnen.
- Listen und Detailansichten.
- Grundlegende Suche.
- Persönliche Notizen und die für die erste Version ausgewählten Besuchsfelder.

Der Kern soll bereits ohne KI nutzbar sein.

### Schritt 4: Recherche und Import anbinden

- Rechercheauftrag erzeugen.
- JSON einlesen und prüfen.
- Vorschau und Korrektur ermöglichen.
- Quellen und offene Fragen speichern.
- Schutz manueller Angaben umsetzen.
- Später ergänzende Recherche ermöglichen.
- Eine direkte kostenlose API als separaten Adapter prüfen.

### Schritt 5: Fotos und Location-Seiten umsetzen

- Vorhandene Fotos auswählen und referenzieren.
- Mehrfachauswahl und Datumfilter.
- Galerien, Titelbilder, Bildunterschriften und Reihenfolge.
- Innen-/Außenbilder.
- Besuchsfotos auf Location-Seiten.
- HEIC-Anzeige und gegebenenfalls Vorschaubilder.
- Verhalten bei verschobenen Originaldateien prüfen.

### Schritt 6: Karte und Statistiken umsetzen

- Exakte Koordinaten an Spielstätten.
- Kombi-Karte mit Clustering.
- Zeit-, Sportart- und Wettbewerbsfilter.
- Getrennte Zählung von Besuchen, Events, Spielen/Kämpfen und Spielstätten.
- Allgemeine und sportartspezifische Statistiken.
- Sichtbare Datenabdeckung.

### Schritt 7: Persönliche Zusatzfunktionen ergänzen

- Jahresrückblick.
- „An diesem Tag“.
- Meilensteine.
- Rekorde.
- Reisen mit Fotos und Kosten.
- Kombinierbare Suche.
- Weitere vorgeschlagene Erinnerungs- und Bewertungsfunktionen nach Priorisierung.

### Schritt 8: Sicherung und praktische Prüfung

- Vollständigen Export und Backup umsetzen.
- Wiederherstellung prüfen.
- Mit echten historischen Besuchen testen.
- Namenswechsel, Neubau-Regeln und Mehrkampfveranstaltungen prüfen.
- Mehrfachimporte und manuelle Korrekturen prüfen.
- Fotozuordnungen nach Verschieben oder Umbenennen prüfen.
- Laufzeit und Ressourcenbedarf auf dem NAS messen.

### Vorgabe für den übernehmenden Assistenten

Bereits entschiedene Grundregeln beibehalten. Insbesondere keine Planung/Wunschliste, keine notwendige Check-in-Funktion, keine erneute Auswahl tatsächlich gesehener Kämpfe und keine neue Spielstätte allein wegen eines Namenswechsels oder Neubaus am selben Standort einführen.

Offene technische Fragen dürfen konkretisiert werden. Vorschläge und neue Entscheidungen müssen als solche kenntlich bleiben.

## 9) Wichtige Code-Ausschnitte oder Dateinamen

### Vorhandener Code

Im bisherigen Projektgespräch sind keine geschriebenen Code-Ausschnitte dokumentiert.

### Vorhandene Dateien und Projektzugänge

Nicht dokumentiert sind:

- Repository-URL. *(Stand 31.10.2026: https://github.com/siliconserver/event-tracker)*
- Projektverzeichnis.
- Quelldateien.
- Datenbankdatei.
- SQL-Schema oder Migrationen.
- Dockerfile.
- Compose-Datei.
- Konfigurationsdateien.
- JSON-Schema.
- Beispiel-JSON.
- CSV-Vorlage.
- API-Endpunkte.
- NAS-Fotoverzeichnisse.
- Zugangsdaten.
- Deployment-Adresse.

Es dürfen deshalb keine konkreten Dateinamen, Pfade, Endpunkte oder vorhandenen Implementierungen als bereits existierend vorausgesetzt werden.

### Tatsächlich genannte technische Bezeichnungen

- Synology DS420+.
- 6 GB RAM.
- Synology Photos.
- VPN.
- Docker als ~~vorgeschlagene~~ Betriebsform. *(Neue Entscheidung (31.10.2026): festgelegt.)*
- GitLab für den späteren Build (CI/CD). *(Neu ergänzt am 31.10.2026.)*
- OpenStreetMap als vorgeschlagene Kartenbasis.
- JSON für den Rechercheaustausch.
- CSV als mögliche Sammelimportoption.
- ChatGPT für den halbautomatischen Rechercheweg.
- Gemini als damaliger Kandidat für eine kostenlose API.
- Qwen2.5-1.5B-Instruct als Beispiel für spätere lokale KI.
- 4-Bit-Quantisierung.
- llama.cpp als mögliche lokale Laufzeit.

Diese Namen dokumentieren die bisherige Diskussion. Sie ersetzen keine noch ausstehende technische Auswahl, Konfiguration oder Prüfung.
