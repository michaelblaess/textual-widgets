# Tastenbelegung der TUI-Anwendungen

Arbeitsstand vom 12.08.2026. Erhoben aus den `BINDINGS`- und
`_bindings.bind()`-Stellen von neun Anwendungen. Noch keine beschlossene
Konvention - Grundlage für die Entscheidung.

> **Status: beschlossen am 08.09.2026.** Die Rückfrage im Textual-Discord
> ist damit gegenstandslos: Es wird keine einzelne Belegung festgelegt,
> sondern eine **umschaltbare**. Damit muss die Frage "welche ist die
> richtige" gar nicht mehr entschieden werden. Die Mechanik liegt in
> `textual-widgets`, umgestellt wird zuerst `jira-timesheet`.

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
  Umstellung in den Systemeinstellungen. Schlimmer: **F3, F4 und F11 holt sich
  das Betriebssystem ganz** (Mission Control, Spotlight, Schreibtisch), die
  kommen bei der Anwendung gar nicht erst an. Brauchbar bleiben dort im
  Wesentlichen F1, F2 und F5. Nicht gemessen mangels Gerät - angelesen.
  Der frühere Vermerk "für den eigenen Gebrauch gegenstandslos" war zu kurz
  gedacht: Michael hat keinen Mac, seine **Anwender** schon - acht der Repos
  bauen macOS-Artefakte im Release.
- `alt+Buchstabe` ist auf dem Mac kein sicherer Ersatz: Option+Buchstabe
  erzeugt dort Sonderzeichen, solange im Terminal nicht "Option als
  Meta-Taste verwenden" eingeschaltet ist.
- `ctrl+Buchstabe` ist plattformübergreifend am robustesten, aber viele davon
  gehören dem Terminal (`ctrl+c`, `ctrl+d`, `ctrl+z`, und `ctrl+s`/`ctrl+q`
  sind die alte Flusssteuerung).

**Es gibt keine Tastenkombination, die überall funktioniert.** Genau deshalb
wird die Belegung umschaltbar statt festgelegt.

Deshalb: **F-Taste und Buchstabe auf dieselbe Aktion binden.** Textual
nimmt beides in einem Aufruf (`"f1,i"`), das kostet nichts. Im Footer steht
nur eine der beiden - wer die F-Taste gewohnt ist, benutzt sie, wer sie nicht
losbekommt, hat den Buchstaben.

## Der Beschluss: zwei Achsen, nicht drei Stile

Die Belegung hat **zwei unabhängige Schalter**:

1. **Stil** - `classic` (der Bestand) oder `function_keys` (allgemeine
   Funktionen auf F-Tasten). Betrifft nur die Aktionen der Anwendung.
2. **Vim-Navigation** - an oder aus. Ein Zusatz, kein eigener Stil.

Warum vim keine dritte Tabelle bekommt: Die Navigationstasten hängen am
**Widget** (Tabelle, Scroll-Bereich), die Aktionstasten an der **App**. Beides
in eine Tabelle zu gießen würde jede Aktion doppelt führen, ohne dass sich
etwas daran unterscheidet. Als eigene Achse lässt sich vim mit beiden Stilen
kombinieren.

## Die gemeinsame Konvention

Steht als `COMMON_FUNCTION_KEYS` in `textual_widgets/keymap.py`.

| Taste | Zweitbelegung | Aktion |
| --- | --- | --- |
| `F1` | `i` | Info / Über |
| `F2` | - | Einstellungen |
| `F3` | `/` | Suchen / Filter |
| `F4` | `alt+l` | Log ein/aus |
| `F5` | - | Aktualisieren |
| `F10` | `q` | Beenden |
| `Esc` | - | Dialog schließen |

Zwei Korrekturen gegenüber dem ersten Entwurf vom 12.08.2026:

- **`F2` bekommt keinen Buchstaben.** Der Entwurf hatte dort `s` stehen und
  darunter in der fachlichen Tabelle `s` = Start - dieselbe Taste für zwei
  Dinge. Das hätte genau das Argument ausgehebelt, für das die Umstellung
  gemacht wird. Ein Test hält das jetzt fest.
- **Das Log zieht von `l` weg** auf `F4` beziehungsweise `alt+l`. Grund ist
  die Vim-Ebene: `l` ist dort "nach rechts", und eine Widget-Bindung verdeckt
  die der App (siehe unten). Damit bleibt `hjkl` vollständig nutzbar.

**Fachlich, wo die Anwendung es hat** (bleibt bei den Buchstaben, die durch
die Umstellung frei werden):

| Taste | Aktion |
| --- | --- |
| `s` | Start (Scan, Crawl, Build, Abruf) |
| `x` | Abbrechen |
| `c` | Kopieren |
| `e` | Exportieren |
| `d` | Details |
| `alt+h` | Historie |

`h` für Historie ist gestrichen: `h` ist in der Vim-Ebene "nach links" und
würde genauso verdeckt wie vorher `l`. `ctrl+h` ist kein Ersatz, das kommt in
Textual gar nicht an - `alt+h` schon.

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

Angenehmer Nebenbefund: `q` zum Beenden, `/` für den Filter und `Esc` zum
Abbrechen sind bereits vim-konform und in allen neun Anwendungen gleich. Die
Aktionsebene ist also schon halb da, es fehlt im Wesentlichen die Navigation.

## Eigene Belegungen des Anwenders

Feste Stile allein reichen nicht, weil das Terminal mitredet und man es nicht
kennt - der Mac-Fall oben ist genau das. Deshalb: **Stil als Grundlage plus
Einzelkorrekturen** in der Einstellungsdatei, so wie lazygit, k9s und btop es
machen.

```yaml
tastatur:
  stil: function_keys      # classic | function_keys
  vim_navigation: true
  eigene:
    settings: [f2, alt+s]
    log: [alt+l]
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

## Die Falle, die Zeit kostet

**Eine Bindung am Widget schlägt die gleichnamige an der App, und die
App-Aktion feuert dann gar nicht** - ohne Fehler und ohne Hinweis im Footer.
Gemessen am 08.09.2026 mit Textual 8.2.8: `l` gleichzeitig an einer
`DataTable` und an der `App`, über `run_test()` gedrückt, Ergebnis eindeutig
`['widget']`. Das ist der ganze Grund, warum das Log von `l` wegzieht.

Aus derselben Ecke, übernommen aus jiratui (`actions/constants.py`, PR 327):
`ctrl+h` kommt in Textual nicht an, `alt+f` und `alt+b` sind belegt (sie sind
`ctrl+right` und `ctrl+left`).

## Stand der Umsetzung

- [x] `textual_widgets/keymap.py` - Stile, Vim-Ebene, Zusammenführen, Prüfer.
- [x] `tests/test_keymap.py` - 30 Tests, je Stil und für jede Regel oben.
- [ ] `jira-timesheet` auf die Schleife umstellen, Schalter in die
      Einstellungen, Vim-Ebene an die Tabellen.
- [ ] Übersichtsseite mit der aktuellen Belegung (fällt aus der Tabelle ab).
- [ ] Die übrigen drei `textual-widgets`-Anwendungen nachziehen
      (c2pa-scanner, console-error-scanner, sitemap-tracker).
- [ ] Die fünf ohne diese Abhängigkeit - offen, ob sie die Bibliothek bekommen
      oder eine eigene Kopie.
