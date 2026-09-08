# Tastenbelegung der TUI-Anwendungen

Erhebung vom **08.09.2026**, gemessen mit `tools/keymap_survey.py` über die
Aufrufe von `_bindings.bind()` und `Binding(...)` in acht Anwendungen. Reine
Dialog-Aktionen (schließen, abbrechen, bestätigen, speichern) sind
herausgefiltert, die sagen nichts über die Hauptbelegung.

> **Status: beschlossen am 08.09.2026.** Die Rückfrage im Textual-Discord ist
> gegenstandslos: Es wird keine einzelne Belegung festgelegt, sondern eine
> **umschaltbare**. Damit muss die Frage "welche ist die richtige" gar nicht
> entschieden werden. Die Mechanik liegt in `textual_widgets/keymap.py`,
> umgestellt wird zuerst `jira-timesheet`.

Gescannt: buildrunner-tui, c2pa-scanner, console-error-scanner, form-breaker,
inspectcode-tui, sitemap-tracker, visual-regression-scanner, jira-timesheet.

Die geteilte Bibliothek `textual-widgets` nutzen davon vier (c2pa-scanner,
console-error-scanner, sitemap-tracker, jira-timesheet). Die übrigen hängen
nicht daran - eine hier verankerte Konvention greift dort nicht automatisch.

## Was einheitlich ist

| Taste | Bedeutung | Verbreitung |
| --- | --- | --- |
| `q` | Beenden | **8 von 8** |
| `i` | Info / Über | **8 von 8** |
| `l` | Log ein/aus | **7 von 7**, die es haben |
| `h` | Historie | **6 von 6**, die es haben |
| `/` | Filter fokussieren | **5 von 5**, die es haben |
| `s` | Einstellungen | 5 von 8 |
| `z` | Zusammenfassung | 2 von 2 |
| `?` | HTTP-Codes | 2 von 2 |
| `+` / `-` | Log größer / kleiner | 2 von 2 |
| `w` | Whitelist | 2 von 2 |

Gemessen an denen, die die Funktion überhaupt haben, sind `l` und `h`
**lückenlos**. Der frühere Arbeitsstand vom 12.08.2026 hatte sie mit "8 von 9"
und "5 von 9" geführt und damit unterschätzt.

**Auch die Aktionsnamen sind bereits einheitlich:** `show_about` (7),
`toggle_log` (7), `quit` (7), `show_history` (6), `show_settings` (5),
`focus_filter` (5). Deshalb sind die Schlüssel in `COMMON_FUNCTION_KEYS` genau
diese Namen - keine Anwendung muss etwas umbenennen, um mitzumachen.

## Wo es wirr ist

| Taste | Apps | Bedeutungen |
| --- | --- | --- |
| `c` | 8 | Log kopieren (4) **gegen** Scan/Crawl starten (4) - exakt gespalten |
| `r` | 6 | sechs verschiedene: retry, save_reports, reload, copy_row, reset_site, reset_cache |
| `t` | 5 | Theme (2), Storybook, Testbild, Tabelle kopieren |
| `e` | 5 | Filter-Umschalter (4) **gegen** Excel-Export (1) |
| `m` | 4 | Sitemap laden (2), Sitemap speichern, manuelle Erfassung |
| `x` | 4 | Scan abbrechen (2), Log leeren, unbenannt |
| `o` | 3 | Sitemap wählen, häufigste Befunde, Bilder öffnen |
| `p` | 3 | Pause, Dateien prüfen, PDF-Export |

`c` und `r` sind die beiden echten Baustellen. Bei `r` gibt es keine Konvention
zu retten - sechs Anwendungen, sechs Bedeutungen.

## Der Beschluss: zwei Achsen, nicht drei Stile

1. **Stil** - `classic` (der Bestand) oder `function_keys` (allgemeine
   Funktionen zusätzlich auf F-Tasten). Betrifft nur die Aktionen der Anwendung.
2. **Vim-Navigation** - an oder aus. Ein Zusatz, kein eigener Stil.

Warum vim keine dritte Tabelle bekommt: Die Navigationstasten hängen am
**Widget** (Tabelle, Scroll-Bereich), die Aktionstasten an der **App**. Beides
in eine Tabelle zu gießen würde jede Aktion doppelt führen, ohne dass sich
etwas daran unterscheidet. Als eigene Achse lässt sich vim mit beiden Stilen
kombinieren.

## Die gemeinsame Konvention

Steht als `COMMON_FUNCTION_KEYS` in `textual_widgets/keymap.py`. Die F-Taste
tritt **neben** den Buchstaben, sie ersetzt ihn nicht.

| Taste | Zweitbelegung | Aktion | Aktionsname |
| --- | --- | --- | --- |
| `F1` | `i` | Info / Über | `show_about` |
| `F2` | `s` | Einstellungen | `show_settings` |
| `F3` | `/` | Suchen / Filter | `focus_filter` |
| `F4` | `alt+l` | Log ein/aus | `toggle_log` |
| `F5` | - | Aktualisieren | `refresh` |
| `F6` | `d` | Details | `show_details` |
| - | `alt+h` | Historie | `show_history` |
| - | `q` | Beenden | `quit` |
| `Esc` | - | Dialog schließen | - |

**Ab `F7` vergibt die Anwendung selbst.** Was dort sinnvoll liegt, hängt davon
ab, was sie überhaupt kann - sie ergänzt ihre Einträge beim Aufruf von
`resolve_keymap()`. `F11` und `F12` bleiben frei, viele Terminals und Browser
belegen sie selbst mit Vollbild.

**Der Footer sortiert nach F-Nummer.** `sort_for_footer()` zieht alles mit
F-Taste nach vorn, aufsteigend, danach folgt der Rest unverändert. Ohne das
stünde dort `F2 Settings` vor `F1 Info`, weil die Bestandstabelle die
Reihenfolge vorgibt - das sieht aus wie ein Versehen. Im Bestandsstil wird
**nicht** sortiert: dort hätte nur `refresh` eine F-Taste, und die allein nach
vorn zu ziehen wäre eine Änderung ohne Gewinn.

Vier Festlegungen, die man sonst nachschlagen muss:

- **`F2` behält `s`** (Michael am 08.09.2026). Das ist die gewachsene
  Konvention aus fünf Anwendungen, und sie schlägt die ursprüngliche Idee,
  `s` für "Start" freizuräumen.
  **Folge:** Der `s`-Konflikt ist damit **nicht** gelöst. Die Anwendungen mit
  einem Lauf brauchen für "Start" eine andere Taste - welche, wird beim
  Umstellen der jeweiligen Anwendung entschieden, nicht hier auf Vorrat.
- **Das Log zieht von `l` weg**, die Historie von `h` weg. Beide sind
  vim-Navigationstasten, und eine Widget-Bindung verdeckt die der App
  (gemessen, siehe unten). `ctrl+h` ist kein Ersatz, das kommt in Textual gar
  nicht an - `alt+h` schon.
- **`quit` bekommt keine F-Taste.** `q` ist die einzige Taste, die in acht von
  acht Anwendungen dasselbe tut, und `F10` ist in console-error-scanner bereits
  belegt (häufigste Fehler). Auf dem Mac wäre `F10` ohnehin unsicher.
  **`F10` bleibt damit offen:** `jira-timesheet` legt seit dem 08.09.2026 den
  PDF-Export darauf, console-error-scanner die häufigsten Fehler. Innerhalb je
  einer Anwendung kollidiert nichts, über die Familie hinweg bedeutet `F10`
  zweierlei - zu entscheiden, wenn console-error-scanner an der Reihe ist.
- **`F1`, `F3` und `F4` sind in keiner Anwendung belegt**, `F2` ist in
  buildrunner-tui bereits die Einstellungen. Die Konvention bestätigt also
  einen bestehenden Stand, statt einen neuen zu erfinden.

**Fachlich, wo die Anwendung es hat:**

| Taste | Aktion |
| --- | --- |
| `x` | Abbrechen |
| `c` | Kopieren |
| `e` | Exportieren |
| offen | Start (Scan, Crawl, Build, Abruf) |
| offen | `c` gegen "Scan starten" - der ungelöste Zweitkonflikt |

`d` (Details) ist aus dieser Liste in die gemeinsame Konvention gewandert: Es
macht in 5 von 8 Anwendungen etwas mit Details oder einem Diff und ist damit
die einzige fachliche Taste, die einheitlich genug dafür ist.

## Die Vim-Ebene

Steht als `VIM_NAVIGATION` im selben Modul. Wird am **Widget** gebunden.

| Taste | Bedeutung |
| --- | --- |
| `j` / `k` | Zeile runter / hoch |
| `h` / `l` | Spalte links / rechts |
| `g` / `G` | an den Anfang / ans Ende |
| `ctrl+d` / `ctrl+u` | halbe Seite runter / hoch |

Textual bringt davon nichts mit. Gemessen an Textual 8.2.8 kennt
`DataTable.BINDINGS` nur `enter`, die Pfeiltasten, `pageup`, `pagedown`,
`home`, `end`, `ctrl+home` und `ctrl+end`.

**Der teure Befund:** vim kollidiert ausgerechnet mit den beiden Buchstaben,
die in der Familie am saubersten etabliert sind.

| vim-Taste | belegt in | wodurch |
| --- | --- | --- |
| `l` | **7 Apps** | Log ein/aus - einheitlich |
| `h` | **6 Apps** | Historie - einheitlich |
| `j` | 3 Apps | Jira-Export, Wiki öffnen, Jira-Report |
| `g` | 1 App | Formulare speichern (sitemap-tracker) |
| `k`, `G` | 0 | frei |

Daraus folgt die Rolle der Vim-Ebene: Sie ist etwas, das man **einschaltet und
wofür man `h` und `l` bewusst aufgibt.** Genau deshalb meldet
`resolve_keymap()` beim Einschalten, welche Aktionen dadurch verdeckt werden -
das ist nicht Beiwerk, das ist die Hauptfunktion.

Angenehmer Nebenbefund: `q` zum Beenden, `/` für den Filter und `Esc` zum
Abbrechen sind bereits vim-konform und in allen Anwendungen gleich. Die
Aktionsebene ist also schon halb da, es fehlt im Wesentlichen die Navigation.

## Eigene Belegungen des Anwenders

Feste Stile allein reichen nicht, weil das Terminal mitredet und man es nicht
kennt - der Mac-Fall unten ist genau das. Deshalb: **Stil als Grundlage plus
Einzelkorrekturen** in der Einstellungsdatei, so wie lazygit, k9s und btop es
machen.

```yaml
tastatur:
  stil: function_keys      # classic | function_keys
  vim_navigation: true
  eigene:
    show_settings: [f2, alt+s]
    toggle_log: [alt+l]
```

Regeln beim Zusammenführen (`resolve_keymap()`):

- Eine Korrektur gewinnt immer gegen die Vorgabe.
- Nimmt sie einer anderen Aktion eine Taste weg, verliert die andere genau
  diese eine Taste. Bleibt ihr danach keine mehr, fällt sie raus und das steht
  als Beanstandung im Log.
- **Ausnahme `quit`:** Eine Korrektur, die der letzten Ausstiegstaste an den
  Kragen geht, wird verworfen statt übernommen.
- Ein unbekannter Aktionsname wird übergangen und gemeldet, nicht verschluckt.
- Bei aktiver Vim-Ebene wird zusätzlich geprüft, ob eine App-Aktion auf einer
  Navigationstaste liegt und dort verdeckt würde.

Startwert je Betriebssystem über `default_style_for_platform()`: auf macOS
`classic`, sonst `function_keys`. Kein eigener Mac-Stil, nur ein anderer
Startwert - umschalten kann der Anwender überall.

## Der Einwand gegen F-Tasten

- Manche Terminals fangen `F1` und `F10` selbst ab (Menüleiste, Hilfe).
- Über SSH und in Multiplexern kommen F-Tasten je nach `TERM` unterschiedlich an.
- macOS: alle aktuellen Macs haben eine physische Reihe F1-F12, sie senden ab
  Werk aber Systemfunktionen - ein echtes F1 braucht `fn` oder eine einmalige
  Umstellung in den Systemeinstellungen. Schlimmer: **F3, F4 und F11 holt sich
  das Betriebssystem ganz** (Mission Control, Spotlight, Schreibtisch), die
  kommen bei der Anwendung gar nicht erst an. Brauchbar bleiben dort im
  Wesentlichen F1, F2 und F5. Nicht gemessen mangels Gerät - angelesen.
  Der frühere Vermerk "für den eigenen Gebrauch gegenstandslos" war zu kurz
  gedacht: Michael hat keinen Mac, seine **Anwender** schon - acht der Repos
  bauen macOS-Artefakte im Release.
- `alt+Buchstabe` ist auf dem Mac kein sicherer Ersatz: Option+Buchstabe
  erzeugt dort Sonderzeichen, solange im Terminal nicht "Option als Meta-Taste
  verwenden" eingeschaltet ist.
- `ctrl+Buchstabe` ist plattformübergreifend am robustesten, aber viele davon
  gehören dem Terminal (`ctrl+c`, `ctrl+d`, `ctrl+z`, und `ctrl+s`/`ctrl+q`
  sind die alte Flusssteuerung).

**Es gibt keine Tastenkombination, die überall funktioniert.** Genau deshalb
wird die Belegung umschaltbar statt festgelegt, und deshalb tritt die F-Taste
neben den Buchstaben, statt ihn zu ersetzen.

## Die Falle, die Zeit kostet

**Eine Bindung am Widget schlägt die gleichnamige an der App, und die
App-Aktion feuert dann gar nicht** - ohne Fehler und ohne Hinweis im Footer.
Gemessen am 08.09.2026 mit Textual 8.2.8: `l` gleichzeitig an einer
`DataTable` und an der `App`, über `run_test()` gedrückt, Ergebnis eindeutig
`['widget']`. Das ist der ganze Grund, warum Log und Historie umziehen.

Aus derselben Ecke, übernommen aus jiratui (`actions/constants.py`, PR 327):
`ctrl+h` kommt in Textual nicht an, `alt+f` und `alt+b` sind belegt (sie sind
`ctrl+right` und `ctrl+left`).

## Was die Umstellung für jira-timesheet bedeutet

Berechnet über `resolve_keymap()` gegen den heutigen Stand aus `app.py`:

| Aktion | klassisch | F-Tasten |
| --- | --- | --- |
| Info / Über | `i` `I` | **`F1`** `i` `I` |
| Einstellungen | `s` `S` | **`F2`** `s` `S` |
| Filter | `/` | **`F3`** `/` |
| Log ein/aus | `l` `L` | **`F4`** `alt+l` |
| Aktualisieren | `F5` | `F5` |
| Details | `d` `D` | **`F6`** `d` `D` |
| Analyse | `b` `B` | **`F7`** `b` `B` |
| Manuelle Erfassung | `m` `M` | **`F8`** `m` `M` |
| Excel-Export | `e` `E` | **`F9`** `e` `E` |
| PDF-Export | `p` `P` | **`F10`** `p` `P` |

Unverändert bleiben: `q` Beenden, `c` Log kopieren, `TAB` Ansicht wechseln,
`a` Anonymisieren, `r` Cache zurücksetzen, `t` Theme, `DEL` löschen, `,` und
`.` Monatswechsel, `?` Übersicht.

**Nur eine der Änderungen nimmt etwas weg** - alle F-Tasten treten neben die
vorhandenen Buchstaben. Die einzige echte Umgewöhnung ist das Log.

Mit eingeschalteter Vim-Navigation meldet der Prüfer:

- **klassisch:** `toggle_log` liegt auf `l` und ist stumm, solange eine Tabelle
  den Fokus hat.
- **F-Tasten:** keine Aktion wird verdeckt.

`jira-timesheet` ist im F-Tasten-Stil also restlos vim-tauglich, weil es keine
der Tasten `h`, `j`, `k` oder `g` benutzt.

## Stand der Umsetzung

- [x] `textual_widgets/keymap.py` - Stile, Vim-Ebene, Zusammenführen, Prüfer.
- [x] `tests/test_keymap.py` - 30 Tests, gegengeprüft per Mutation.
- [x] `tools/keymap_survey.py` - die Erhebung, wiederholbar nach jeder Umstellung.
- [x] `jira-timesheet` umgestellt (v1.21.0+, Commit `beabcda`): Schleife statt
      19 Einzelbindungen, Schalter unter Einstellungen -> Tastatur, Vim-Ebene
      an `ResizableDataTable`, eigene Belegungen über `keymap_custom`.
- [x] Übersichtsseite auf `?`, die die aufgelöste Belegung zeigt.
- [ ] Die übrigen drei `textual-widgets`-Anwendungen nachziehen
      (c2pa-scanner, console-error-scanner, sitemap-tracker).
- [ ] Die vier ohne diese Abhängigkeit - offen, ob sie die Bibliothek bekommen
      oder eine eigene Kopie.
- [ ] Offen: Ersatztaste für "Start" und die Spaltung von `c`.
