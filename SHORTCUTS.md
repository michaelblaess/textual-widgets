# Tastenbelegung der TUI-Anwendungen

Arbeitsstand vom 12.08.2026. Erhoben aus den `BINDINGS`- und
`_bindings.bind()`-Stellen von neun Anwendungen. Noch keine beschlossene
Konvention - Grundlage für die Entscheidung.

> **Status: zurückgestellt.** Der Eingriff geht über neun Anwendungen,
> deshalb erst die Rückfrage im Textual-Discord nach der allgemeinen
> Empfehlung. Bis dahin wird nichts umgestellt.

## Erhebung

Gescannt wurden: c2pa-scanner, console-error-scanner, sitemap-tracker,
buildrunner-tui, inspectcode-tui, visual-regression-scanner, form-breaker,
jira-timesheet und die Vorlage `_template-python-tui`.

Die geteilte Bibliothek `textual-widgets` nutzen davon nur vier
(c2pa-scanner, console-error-scanner, sitemap-tracker, jira-timesheet).
Die übrigen fünf hängen nicht daran - eine zentral verankerte Konvention
greift dort heute nicht automatisch.

## Was bereits einheitlich ist

| Taste | Bedeutung | Verbreitung |
| --- | --- | --- |
| `q` | Beenden bzw. Dialog schließen | **9 von 9** |
| `Esc` | Dialog schließen / abbrechen | 9 von 9 |
| `i` | Info / Über | 8 von 9 |
| `l` | Log ein- und ausblenden | 8 von 9 |
| `h` | Historie | 5 von 9 |
| `/` | Filter fokussieren | 5 von 9 |
| `d` | Details zur markierten Zeile | 5 von 9 |

`q` ist die einzige Taste, die in **jeder** Anwendung dasselbe tut.

## Wo es wirklich wirr ist

Nicht bei den Tasten oben, sondern hier:

| Taste | Bedeutungen im Bestand |
| --- | --- |
| `r` | Berichte speichern, Site zurücksetzen, neu laden, Zeile kopieren, Cache leeren |
| `t` | Theme wechseln, Testbild erzeugen, Tabelle kopieren, Storybook |
| `s` | **Einstellungen** (4 Anwendungen) gegen **Start / Stopp** (4 Anwendungen) |
| `c` | **Log kopieren** (5) gegen **Scan/Crawl starten** (3) |
| `x` | Scan abbrechen, Log leeren |
| `e` | Fehler filtern, KI-Kennzeichnung, Excel-Export |
| `m` | Sitemap laden, Sitemap speichern, manuelle Erfassung |

Die beiden gefährlichen Paare sind `s` und `x`: In einer Anwendung öffnet
`s` die Einstellungen, in einer anderen **stoppt** es den Lauf. `x` bricht
mal den Scan ab und leert mal das Log.

## Belegte Kollisionen mit F-Tasten

- `F10` ist in console-error-scanner bereits belegt (häufigste Fehler).
- `F2` öffnet in buildrunner-tui die Einstellungen.
- `F5` aktualisiert in jira-timesheet.

## Das strukturelle Argument für F-Tasten

Es geht nicht darum, dass F-Tasten "richtiger" wären als Buchstaben. Der
Gewinn ist ein anderer: Liegen die **allgemeinen** Funktionen auf F-Tasten,
werden die Buchstaben für die **fachlichen** frei. Genau deshalb hat CUA das
damals so gemacht.

Konkret: Sobald Einstellungen nicht mehr auf `s` liegen, kann `s` überall
"Start" heißen - und der schlimmste Konflikt der Tabelle oben ist weg, ohne
dass irgendwo ein Kompromiss nötig wäre. Dasselbe gilt für `c`, sobald
Kopieren einen festen Platz hat.

## Der Einwand gegen F-Tasten

Nicht nachgeprüft, aber bekannt und ernst zu nehmen:

- Manche Terminals fangen `F1` und `F10` selbst ab (Menüleiste, Hilfe).
- Über SSH und in Multiplexern kommen F-Tasten je nach `TERM` unterschiedlich an.
- macOS: alle aktuellen Macs haben eine physische Reihe F1-F12, sie senden ab
  Werk aber Systemfunktionen - ein echtes F1 braucht `fn` oder eine einmalige
  Umstellung in den Systemeinstellungen. **Für den eigenen Gebrauch
  gegenstandslos** (rainbow, dell, senza und der Arbeitsrechner sind Windows
  bzw. Ubuntu, kein Mac). Zählt nur, falls jemand anderes die macOS-Artefakte
  benutzt, die acht der Repos im Release bauen - ob das jemand tut, ist offen.

Deshalb: **F-Taste und Buchstabe auf dieselbe Aktion binden.** Textual
nimmt beides in einem Aufruf (`"f1,i"`), das kostet nichts. Im Footer steht
nur eine der beiden - wer die F-Taste gewohnt ist, benutzt sie, wer sie nicht
losbekommt, hat den Buchstaben.

## Vorschlag

**Allgemein, in jeder Anwendung gleich:**

| Taste | Zweitbelegung | Aktion |
| --- | --- | --- |
| `F1` | `i` | Info / Über |
| `F2` | `s` | Einstellungen |
| `F3` | `/` | Suchen / Filter |
| `F5` | - | Aktualisieren |
| `F10` | `q` | Beenden |
| `Esc` | - | Dialog schließen |

**Fachlich, wo die Anwendung es hat:**

| Taste | Aktion |
| --- | --- |
| `s` | Start (Scan, Crawl, Build, Abruf) |
| `x` | Abbrechen |
| `c` | Kopieren |
| `e` | Exportieren |
| `d` | Details |
| `h` | Historie |
| `l` | Log ein/aus |

Der Bruch mit dem bisherigen Stand liegt bei `s`: bisher galt `s` als
Einstellungen. Neu wäre `s` = Start und `F2` = Einstellungen. Das ist die
einzige Umgewöhnung, die weh tut - dafür verschwindet der Konflikt, bei dem
dieselbe Taste einmal einen Dialog öffnet und einmal einen Lauf stoppt.

## Offen

- Entscheidung über die Grundrichtung.
- Ob die Konvention in `textual-widgets` als gemeinsame Basis landet - dann
  müssten die fünf Anwendungen ohne diese Abhängigkeit sie zuerst bekommen.
- Reihenfolge der Umstellung. `jira-timesheet` steht ohnehin an.
