# textual-widgets

<p align="center">
  <img src="docs/flags/gb.svg" height="13" alt=""> <a href="README.md">English</a> ·
  <img src="docs/flags/de.svg" height="13" alt=""> <b>Deutsch</b>
</p>

---

[![Stars](https://img.shields.io/github/stars/michaelblaess/textual-widgets?logo=github&logoColor=white&color=fbbf24)](https://github.com/michaelblaess/textual-widgets/stargazers)
[![Forks](https://img.shields.io/github/forks/michaelblaess/textual-widgets?logo=github&logoColor=white&color=34d399)](https://github.com/michaelblaess/textual-widgets/network/members)
[![Issues](https://img.shields.io/github/issues/michaelblaess/textual-widgets?logo=github&logoColor=white&color=f87171)](https://github.com/michaelblaess/textual-widgets/issues)
[![Pull Requests](https://img.shields.io/github/issues-pr/michaelblaess/textual-widgets?logo=github&logoColor=white&color=a78bfa)](https://github.com/michaelblaess/textual-widgets/pulls)

[![Last Commit](https://img.shields.io/github/last-commit/michaelblaess/textual-widgets?logo=git&logoColor=white&color=3b82f6)](https://github.com/michaelblaess/textual-widgets/commits/main)
[![License](https://img.shields.io/badge/license-Apache_2.0-3b82f6)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-3b82f6?logo=python&logoColor=white)](https://www.python.org/)

Wiederverwendbare [Textual](https://textual.textualize.io/)-Widgets für Terminal-Benutzeroberflächen.

## Schnellstart

```bash
# Linux / macOS
./setup.sh
./run.sh

# Windows (CMD)
setup.bat
run.bat

# Windows (PowerShell)
.\setup.bat
.\run.ps1
```

`setup` legt eine `.venv` an und installiert das Paket inklusive Entwicklungs- und Storybook-Abhängigkeiten. `run` startet die Storybook-App.

## Storybook

```bash
python -m textual_widgets.storybook
# oder ueber das installierte Konsolen-Skript:
textual-widgets-storybook
```

Interaktive Showcase-App mit einer Sidebar, die alle Widgets listet — eines auswählen und Live-Demo, Code-Snippet und Status-Anzeige beobachten. Tasten: `n` / `p` blättern durch die Stories, `Strg+P` öffnet den Theme-Picker, `Strg+S` speichert einen SVG-Screenshot der aktuellen Ansicht, `q` beendet. Mit installiertem `[storybook]`-Extra sind die Retro-Themes aus [textual-themes](https://github.com/michaelblaess/textual-themes) automatisch registriert.

## Widgets

### DatePicker

Kalender-basierter Datums-Picker mit Monatsnamen, Wochenend-Hervorhebung und Klick-Auswahl.

| Widget | Beschreibung |
|--------|--------------|
| `CalendarGrid` | Reines Kalender-Grid zum Einbetten |
| `DatePicker` | Grid mit Monats- und Jahresnavigation |
| `DatePickerScreen` | Modaler Dialog |

**Features:**
- Deutsche Monatsnamen und Wochentage (Mo–So)
- Wochenenden farblich hervorgehoben, heutiges Datum unterstrichen, ausgewähltes Datum invers
- Monats- und Jahresnavigation `<` `>` `<<` `>>`, "Heute"-Schnellauswahl
- Klick auf einen Tag liefert ein ISO-Datum `YYYY-MM-DD`

```python
from textual_widgets import DatePickerScreen

def action_pick_date(self) -> None:
    self.push_screen(
        DatePickerScreen(initial_date="2024-05-21"),
        callback=self._on_date_selected,
    )

def _on_date_selected(self, selected: str | None) -> None:
    if selected:
        print(f"Picked: {selected}")  # "2024-05-21"
```

### SearchHistoryDropdown / SearchInputWithHistory

Such-Verlauf-Dropdown mit Substring-Filter und Treffer-Hervorhebung. `SearchInputWithHistory` ist die fertig verdrahtete Variante mit optionalem permanentem Icon-Präfix.

| Widget | Beschreibung |
|--------|--------------|
| `SearchHistoryDropdown` | OptionList mit Filter und Hervorhebung |
| `SearchInputWithHistory` | Input und Dropdown verdrahtet, optional mit Icon |

**Features:**
- Substring-Filter (case-insensitive) während des Tippens
- Treffer hervorgehoben in Akzentfarbe und fett
- Pfeil-Tasten oder Maus zur Auswahl, `Enter` übernimmt und sendet
- `Entf` löscht einen Eintrag aus dem Verlauf
- Optional permanentes Icon-Präfix (`icon="🔍"`) — wie die Textual Command-Palette

```python
from textual.widgets import Input
from textual_widgets import SearchInputWithHistory

class MyApp(App):
    def compose(self) -> ComposeResult:
        yield SearchInputWithHistory(
            icon="🔍",
            placeholder="Search ...",
            entries=self._history.list_recent(20),
            id="global-search",
        )

    def on_input_submitted(self, event: Input.Submitted) -> None:
        query = event.value.strip()
        if not query:
            return
        self._history.add(query)
        wrapper = self.query_one("#global-search", SearchInputWithHistory)
        wrapper.set_entries(self._history.list_recent(20))
        # ... Suche starten ...
```

### ContextMenu

Wiederverwendbares Kontextmenü als ModalScreen. Items werden als Liste von `ContextMenuItem` deklariert; das Widget übernimmt Layout, Cursor-Positionierung, Tastatur-Navigation und Theme-Farben.

| Widget | Beschreibung |
|--------|--------------|
| `ContextMenuItem` | Dataclass mit `id`, `label`, optional `icon`, `shortcut`, `enabled` |
| `ContextMenuScreen` | Modaler Dialog mit OptionList |

**Features:**
- Positionierung am Maus-Cursor (`at=(event.screen_x, event.screen_y)`)
- Off-Screen-Schutz pinnt das Menü bei Bedarf an den Terminal-Rand
- Optional zentriert als Fallback für Tastatur-Trigger
- Icons als Präfix (Emoji oder Unicode), Shortcuts rechtsbündig in dim (reine Anzeige)
- Deaktivierte Items werden ausgegraut und sind nicht wählbar
- Trennlinien über `ContextMenuItem.separator()`
- ESC oder Klick außerhalb schließt mit `None`

```python
from textual.events import Click
from textual_widgets import ContextMenuItem, ContextMenuScreen

class FolderBrowser(Tree):
    def on_click(self, event: Click) -> None:
        if event.button != 3:  # nur Rechtsklick
            return
        items = [
            ContextMenuItem("open", "Open", icon="📂", shortcut="Enter"),
            ContextMenuItem("rename", "Rename", icon="✎", shortcut="Ctrl+R"),
            ContextMenuItem.separator(),
            ContextMenuItem("delete", "Delete", icon="✕", shortcut="Del"),
        ]
        self.app.push_screen(
            ContextMenuScreen(items, at=(event.screen_x, event.screen_y)),
            callback=self._on_menu_action,
        )

    def _on_menu_action(self, action_id: str | None) -> None:
        if action_id is None:
            return  # ESC oder Klick ausserhalb
        # ... Aktion behandeln ...
```

Das `shortcut`-Feld ist **reine Anzeige** — den Tastendruck verdrahtet der Konsument selbst über Textual-`Bindings`.

### HamburgerMenu

Klappbares Seitenmenü im DevExpress/Outlook-Stil. Klick auf das Hamburger-Symbol oben blendet das Menü ein oder aus — die Breite wird sanft animiert. Im eingeklappten Zustand zeigen die Items nur Icons; Tooltips beim Hover blenden die Labels ein. Group-Header trennen Abschnitte visuell, Bottom-Items docken unten an (z.B. für Settings).

| Widget | Beschreibung |
|--------|--------------|
| `HamburgerItem` | Dataclass mit `id`, `label`, optional `icon`. Factories `HamburgerItem.group(label)` und `HamburgerItem.separator()`. |
| `HamburgerMenu` | Widget — Liste von Items + optionale Bottom-Items. Sendet `ItemSelected`- und `Toggled`-Messages. |

**Features:**
- Animiertes Ein- / Ausklappen (Breite animiert mit `styles.animate`)
- Klick auf Hamburger-Symbol **oder** programmatisch via `menu.toggle()`
- Group-Header über `HamburgerItem.group("Accounts")`, Trenner über `HamburgerItem.separator()`
- Optional Bottom-Items (Settings, Profil etc.)
- Reactive `selected_id` für programmatische Hervorhebung des aktiven Items
- Tooltips zeigen im eingeklappten Zustand die Labels beim Hover
- Optional über JSON konfigurierbar (`HamburgerMenu.from_json("menu.json")`)

```python
from textual.containers import Horizontal, Container
from textual_widgets import HamburgerMenu, HamburgerItem

class MyApp(App):
    def compose(self) -> ComposeResult:
        with Horizontal():
            yield HamburgerMenu(
                items=[
                    HamburgerItem("new", "New mail", icon="+"),
                    HamburgerItem.group("Accounts"),
                    HamburgerItem("inbox", "Inbox", icon="📧"),
                    HamburgerItem("sent", "Sent", icon="📤"),
                    HamburgerItem.group("Folders"),
                    HamburgerItem("drafts", "Drafts", icon="📝"),
                ],
                bottom_items=[
                    HamburgerItem("settings", "Settings", icon="⚙"),
                ],
            )
            yield Container(id="main")

    def on_hamburger_menu_item_selected(
        self, event: HamburgerMenu.ItemSelected,
    ) -> None:
        self.notify(f"Selected: {event.item_id}")
```

**JSON-Konfiguration:**

```json
{
  "items": [
    {"id": "new", "label": "New mail", "icon": "+"},
    {"group": "Accounts"},
    {"id": "inbox", "label": "Inbox", "icon": "📧"},
    {"separator": true},
    {"id": "sent", "label": "Sent", "icon": "📤"}
  ],
  "bottom_items": [
    {"id": "settings", "label": "Settings", "icon": "⚙"}
  ]
}
```

```python
yield HamburgerMenu.from_json("menu.json")
```

Die JSON-Datei beschreibt nur die Struktur — die Selection-Events werden weiterhin in Python verdrahtet (`on_hamburger_menu_item_selected`), da JSON keine Callbacks transportieren kann.

### Splitter (VerticalSplitter / HorizontalSplitter)

1-Zellen-breite / -hohe Trennlinien zwischen zwei Panels — per Maus-Drag lässt sich die Größe des angrenzenden Panels ändern. Vergleichbar mit den Splittern in IDEs / VS Code. Ein zentrierter Drag-Handle (`┊` vertikal, `┄` horizontal) markiert die Greifzone visuell.

| Widget | Beschreibung |
|--------|--------------|
| `VerticalSplitter` | Vertikale Linie in `Horizontal` — ändert die Breite des linken Panels |
| `HorizontalSplitter` | Horizontale Linie in `Vertical` — ändert die Höhe des oberen Panels |

**Features:**
- Zentrierter Drag-Handle-Glyph
- Hover und aktiver Drag färben den Splitter in `$accent`
- `min_size`- und `max_size`-Beschränkungen
- Target über `target_id` oder als vorhergehendes Geschwister im DOM
- `Resized`-Message nach dem Drag — der Konsument persistiert die neue Größe

```python
from textual.containers import Horizontal, Vertical
from textual_widgets import VerticalSplitter, HorizontalSplitter

class MyApp(App):
    def compose(self) -> ComposeResult:
        with Horizontal():
            yield FolderBrowser(id="folder", classes="left-pane")
            yield VerticalSplitter(target_id="folder", min_size=15, max_size=80)
            with Vertical():
                yield FileTable(id="files", classes="top-pane")
                yield HorizontalSplitter(target_id="files", min_size=5)
                yield Lyrics(classes="bottom-pane")

    def on_vertical_splitter_resized(
        self, event: VerticalSplitter.Resized,
    ) -> None:
        self._settings.set_panel_size(event.target_id, event.size)
```

**CSS-Voraussetzung:** Das Target-Panel braucht eine Größe, die der Splitter überschreiben kann (Prozent- oder Zellen-Default sind beide in Ordnung, `1fr` wäre zu flexibel).

### AboutScreen

Standardisierter About-Dialog als ModalScreen — statt in jeder App einen eigenen zu bauen. Aufbau: Headline-Balken, Meta-Zeile (`Version · Autor · Release · Lizenz`), Beschreibung, ein Trenner, ein Zitat, eine optionale anklickbare URL und ein Schließen-Button. Die Dialogbreite wird aus der längsten Inhaltszeile berechnet, sodass der Trenner bündig sitzt.

| Widget | Beschreibung |
|--------|--------------|
| `AboutScreen` | Modaler Dialog. App-Fakten kommen als Konstruktor-Argumente herein |
| `Quote` | Dataclass für ein Zitat (`text`, `author`) |
| `load_quotes(lang)` | Lädt den mitgelieferten de/en-Zitatpool |

**Features:**
- App-Fakten (`version`, `author`, `release`, `license`) als Argumente übergeben — nie im Dialog hartkodiert
- Breite automatisch aus der längsten Inhaltszeile; keine festen Dimensionen
- Bei jedem Öffnen ein zufälliges Zitat aus dem de/en-Pool; mit `quote=` (fest) oder `quotes=` (eigene Liste) überschreibbar
- Optional anklickbare Projekt-URL (OSC-8, STRG+Klick)
- Schließen über ESC, den Button oder Klick außerhalb

```python
from textual_widgets import AboutScreen

from . import __author__, __version__, __year__

def action_show_about(self) -> None:
    self.push_screen(AboutScreen(
        app_name="my-tool",
        version=__version__,        # ohne führendes "v"
        author=__author__,
        release=__year__,
        description="Einzeiler.\nZweite Zeile.",
        lang="de",
        license="Apache 2.0",
        url="https://github.com/me/my-tool",
    ))
```

### BaseSettingsScreen

Basisklasse für App-Settings-Dialoge — davon erben, statt einen von Grund auf zu bauen. Sie liefert einen einheitlichen Look, einen Sprach-Tab (de/en mit Neustart-Hinweis), Save/Cancel-Buttons und `Strg+S` / `Esc`-Bindings. Die App überschreibt zwei Hooks.

| Widget | Beschreibung |
|--------|--------------|
| `BaseSettingsScreen` | `ModalScreen`-Basisklasse — `dict` rein, geändertes `dict` (oder `None`) raus |

**Features:**
- Nimmt das aktuelle Settings-`dict`, gibt das geänderte `dict` zurück (oder `None` bei Abbruch) — der Storage bleibt in der App
- Kopiert das übergebene Dict, sodass Abbruch jede Änderung verwirft
- Sprach-Tab ist in jeder App fest eingebaut
- Hook `app_tabs()` ergänzt die app-eigenen `TabPane`s; Hook `collect_app_settings()` sammelt deren Werte ein
- Postet beim Speichern ein `LogMessage` — läuft via `LogRouter` ins `LogPanel`

```python
from textual.widgets import Checkbox, TabPane
from textual_widgets import BaseSettingsScreen

class MySettingsScreen(BaseSettingsScreen):
    def app_tabs(self) -> ComposeResult:           # Hook 1: eigene Tabs
        with TabPane("Crawl", id="settings-tab-crawl"):
            yield Checkbox("robots.txt beachten", value=..., id="set-robots")

    def collect_app_settings(self, settings: dict[str, object]) -> None:
        # Hook 2: Widget-Werte ins Ergebnis-Dict schreiben
        settings["respect_robots"] = self.query_one("#set-robots", Checkbox).value

class MyApp(App):
    def action_show_settings(self) -> None:
        self.push_screen(
            MySettingsScreen(self._settings_store.load(), lang="de"),
            callback=self._on_settings_closed,
        )

    def _on_settings_closed(self, result: dict[str, object] | None) -> None:
        if result is None:
            return  # abgebrochen
        self._settings_store.save(result)
```

### LogPanel / LogMessage / LogRouter

Entkoppeltes Logging. Ein beliebiges Widget postet ein `LogMessage`; es bubbelt zur App, wo der `LogRouter`-Mixin es ins `LogPanel` leitet. Das postende Widget referenziert das Panel nie.

| Widget | Beschreibung |
|--------|--------------|
| `LogMessage` | Message-Klasse. Konstruktoren `LogMessage.info/.success/.warning/.error/.debug` |
| `LogPanel` | `RichLog`-basiertes Panel — Zeitstempel, Level-Farben, Plain-Text-Spiegel, Rechtsklick-Kontextmenü |
| `LogRouter` | Mixin für `App` — fängt `LogMessage` ab und schreibt es ins erste `LogPanel` im DOM |

**Features:**
- `LogMessage` von überall posten — keine Referenz aufs Panel nötig
- Zeitstempel + Level-Farbe pro Zeile (info / success / warning / error / debug)
- Plain-Text-Spiegel für Copy/Export (ein `RichLog` speichert nur gerenderte Strips)
- Eingebautes Rechtsklick-Kontextmenü: Kopieren / Exportieren / Ausblenden
- `hide()` postet `LogPanel.Hidden`, damit eine App einen Splitter darüber mit ausblenden kann
- Direktes Schreiben ohne Event geht weiter: `query_one(LogPanel).write_log(text, level)`

```python
from textual.app import App
from textual_widgets import LogMessage, LogPanel, LogRouter

class MyApp(LogRouter, App):          # LogRouter VOR App
    def compose(self) -> ComposeResult:
        yield LogPanel(lang="de", export_name="my-tool", id="log")

# Irgendein Widget, irgendwo — kennt das LogPanel NICHT:
self.post_message(LogMessage.success("Datei gespeichert"))
```

### CrashGuard / ErrorScreen

Fängt unbehandelte Exceptions ab, statt die App von Textual abräumen zu lassen. Der `CrashGuard`-Mixin zeigt den `ErrorScreen` — eine Entschuldigung, die Fehlerzeile, einen scroll- und kopierbaren Traceback sowie Kopieren / Weitermachen / Beenden — und überlässt die Wahl dem Anwender.

| Widget | Beschreibung |
|--------|--------------|
| `CrashGuard` | Mixin für `App` — fängt unbehandelte Exceptions ab |
| `ErrorScreen` | Modaler Dialog mit kopierbarem Fehlerbericht |

**Features:**
- Fängt Exceptions aus Message-Handlern, Timern und Workern (alles läuft über `_handle_exception`)
- Zeigt einen kopierbaren Traceback; der Anwender wählt Weitermachen (App läuft weiter) oder Beenden
- `crash_guard_lang` wählt die Dialogsprache (`de` / `en`)
- Re-Entrancy-Schutz: ein zweiter Fehler bei offenem Dialog fällt auf den regulären Absturzpfad zurück

```python
from textual.app import App
from textual_widgets import CrashGuard

class MyApp(CrashGuard, App):         # CrashGuard VOR App
    def __init__(self) -> None:
        super().__init__()
        self.crash_guard_lang = "de"  # "de" | "en"
```

Die Reihenfolge `CrashGuard, App` ist wichtig: `super()._handle_exception()` im Mixin muss `App._handle_exception` treffen (der reguläre Absturzpfad, als Fallback falls der Fehlerdialog selbst scheitert). Fehler vor `app.run()` in `__main__.py` werden nicht gefangen — die brauchen dort ein eigenes `try/except`.

## Helfer

### Terminal-Titel (set_terminal_title / reset_terminal_title)

Textual setzt den OS-Terminal-Titel nicht selbst — `App.TITLE` füttert nur das interne `Header`-Widget, der Terminal-Tab zeigt also weiter den Shell-/Profilnamen. Diese Helfer schreiben die OSC-Escape-Sequenz direkt, damit der Tab-Text die App widerspiegelt.

| Funktion | Beschreibung |
|----------|--------------|
| `set_terminal_title(title)` | Setzt den Terminal-Fenster-/Tab-Titel |
| `reset_terminal_title()` | Löscht den Titel (der Shell-Prompt setzt ihn ohnehin neu) |

**Hinweise:**
- Schreibt über `sys.__stdout__` (Windows: `WriteConsoleW`), das die aktive Code-Page umgeht — rohe Byte-Writes würden UTF-8 auf einer cp1252-Konsole zu Mojibake machen
- Funktioniert mit Windows Terminal, mintty, xterm, GNOME Terminal, Konsole, iTerm2, Terminal.app, Alacritty, kitty, WezTerm
- Für ein Pseudo-"Icon" ein monochromes Text-Symbol voranstellen (z.B. `♬`) — es übernimmt die Tab-Textfarbe. Color-Emoji lassen sich nicht umfärben. Das echte Tab-Icon kommt aus dem Terminal-Profil und kann von einer App nicht geändert werden.

```python
from textual_widgets import reset_terminal_title, set_terminal_title

def main() -> None:
    set_terminal_title("♬ my-app v1.0.0")
    try:
        MyApp().run()
    finally:
        reset_terminal_title()
```

Für Laufzeit-Updates (z.B. pro Track) `set_terminal_title()` aus einem `watch_`-Handler aufrufen — OSC-Titel-Sequenzen zeichnen nichts und stören das Textual-Rendering nicht.

## Installation

```bash
pip install "textual-widgets @ git+https://github.com/michaelblaess/textual-widgets.git"
```

Mit Storybook und Retro-Themes:

```bash
pip install "textual-widgets[storybook] @ git+https://github.com/michaelblaess/textual-widgets.git"
```

Oder in `pyproject.toml`:

```toml
dependencies = [
    "textual-widgets @ git+https://github.com/michaelblaess/textual-widgets.git@v0.14.2",
]
```

## Abhängigkeiten

- Python ≥ 3.12
- textual ≥ 0.40
- rich ≥ 13.0
- *(optional, für `[storybook]`)* `textual-themes`

## Verwendet von

- **[retro-amp](https://github.com/michaelblaess/retro-amp)** — Terminal-Musikplayer mit Retro-Charme. Nutzt `SearchInputWithHistory` für die globale Suche, `ContextMenuScreen` für den Visualizer-Mode-Switch und die Splitter-Widgets für anpassbare Panel-Größen.

## Lizenz

Apache License 2.0
