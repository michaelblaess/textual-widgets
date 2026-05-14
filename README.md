# textual-widgets

[![Stars](https://img.shields.io/github/stars/michaelblaess/textual-widgets?style=for-the-badge&logo=github&logoColor=white&labelColor=1e2228&color=fbbf24)](https://github.com/michaelblaess/textual-widgets/stargazers)
[![Forks](https://img.shields.io/github/forks/michaelblaess/textual-widgets?style=for-the-badge&logo=github&logoColor=white&labelColor=1e2228&color=34d399)](https://github.com/michaelblaess/textual-widgets/network/members)
[![Issues](https://img.shields.io/github/issues/michaelblaess/textual-widgets?style=for-the-badge&logo=github&logoColor=white&labelColor=1e2228&color=f87171)](https://github.com/michaelblaess/textual-widgets/issues)
[![Pull Requests](https://img.shields.io/github/issues-pr/michaelblaess/textual-widgets?style=for-the-badge&logo=github&logoColor=white&labelColor=1e2228&color=a78bfa)](https://github.com/michaelblaess/textual-widgets/pulls)

[![Last Commit](https://img.shields.io/github/last-commit/michaelblaess/textual-widgets?style=for-the-badge&logo=git&logoColor=white&labelColor=1e2228&color=3b82f6)](https://github.com/michaelblaess/textual-widgets/commits/main)
[![License](https://img.shields.io/badge/license-Apache_2.0-3b82f6?style=for-the-badge&labelColor=1e2228)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-3b82f6?style=for-the-badge&logo=python&logoColor=white&labelColor=1e2228)](https://www.python.org/)

Reusable [Textual](https://textual.textualize.io/) widgets for terminal user interfaces.

Wiederverwendbare [Textual](https://textual.textualize.io/) Widgets für Terminal-Benutzeroberflächen.

## Quick Start / Schnellstart

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

`setup` creates a `.venv` and installs the package with development and storybook dependencies. `run` launches the storybook app.

`setup` legt eine `.venv` an und installiert das Paket inklusive Entwicklungs- und Storybook-Abhängigkeiten. `run` startet die Storybook-App.

## Storybook

```bash
python -m textual_widgets.storybook
# or via the installed console script:
textual-widgets-storybook
```

Interactive showcase app with a sidebar listing every widget — pick one and see a live demo, a code snippet, and a result label that updates as you interact. Bindings: `n` / `p` to cycle through stories, `Ctrl+P` for the theme picker, `Ctrl+S` to save an SVG screenshot of the current view, `q` to quit. With the `[storybook]` extra installed, the retro themes from [textual-themes](https://github.com/michaelblaess/textual-themes) are registered too.

Interaktive Showcase-App mit einer Sidebar, die alle Widgets listet — eines auswählen und Live-Demo, Code-Snippet und Status-Anzeige beobachten. Tasten: `n` / `p` blättern durch die Stories, `Strg+P` öffnet den Theme-Picker, `Strg+S` speichert einen SVG-Screenshot der aktuellen Ansicht, `q` beendet. Mit installiertem `[storybook]`-Extra sind die Retro-Themes aus [textual-themes](https://github.com/michaelblaess/textual-themes) automatisch registriert.

## Widgets

### DatePicker

Calendar-based date picker with month names, weekend highlighting, and click-to-select.

Kalender-basierter Datums-Picker mit Monatsnamen, Wochenend-Hervorhebung und Klick-Auswahl.

| Widget | Description / Beschreibung |
|--------|--------------------------|
| `CalendarGrid` | Pure calendar grid for embedding / Reines Kalender-Grid zum Einbetten |
| `DatePicker` | Grid + month/year navigation / Grid mit Monats- und Jahresnavigation |
| `DatePickerScreen` | Modal dialog / Modaler Dialog |

**Features:**
- German month names and weekdays (Mon–Sun)
- Deutsche Monatsnamen und Wochentage (Mo–So)
- Weekends colour-highlighted, today underlined, selected date inversed
- Wochenenden farblich hervorgehoben, heutiges Datum unterstrichen, ausgewähltes Datum invers
- Month and year navigation `<` `>` `<<` `>>`, "Today" shortcut
- Monats- und Jahresnavigation `<` `>` `<<` `>>`, "Heute"-Schnellauswahl
- Click on day returns ISO date `YYYY-MM-DD`
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

Search-history dropdown with substring filtering and match highlighting. `SearchInputWithHistory` is the prewired variant with an optional permanent icon prefix.

Such-Verlauf-Dropdown mit Substring-Filter und Treffer-Hervorhebung. `SearchInputWithHistory` ist die fertig verdrahtete Variante mit optionalem permanentem Icon-Präfix.

| Widget | Description / Beschreibung |
|--------|--------------------------|
| `SearchHistoryDropdown` | OptionList with filter + highlighting / OptionList mit Filter und Hervorhebung |
| `SearchInputWithHistory` | Input + dropdown wired together, optional icon / Input und Dropdown verdrahtet, optional mit Icon |

**Features:**
- Live substring filter (case-insensitive) while typing
- Substring-Filter (case-insensitive) während des Tippens
- Matches highlighted in accent + bold
- Treffer hervorgehoben in Akzentfarbe und fett
- Arrow keys / mouse to pick, Enter selects and submits
- Pfeil-Tasten oder Maus zur Auswahl, `Enter` übernimmt und sendet
- Delete removes an entry from the history
- `Entf` löscht einen Eintrag aus dem Verlauf
- Optional permanent icon prefix (`icon="🔍"`) — like the Textual command palette
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
        # ... start search ...
```

### ContextMenu

Reusable context menu modal screen. Items are declared as a list of `ContextMenuItem`; the widget handles layout, cursor positioning, keyboard navigation, and theme colours.

Wiederverwendbares Kontextmenü als ModalScreen. Items werden als Liste von `ContextMenuItem` deklariert; das Widget übernimmt Layout, Cursor-Positionierung, Tastatur-Navigation und Theme-Farben.

| Widget | Description / Beschreibung |
|--------|--------------------------|
| `ContextMenuItem` | Dataclass with `id`, `label`, optional `icon`, `shortcut`, `enabled` / Dataclass mit `id`, `label`, optional `icon`, `shortcut`, `enabled` |
| `ContextMenuScreen` | Modal dialog with OptionList / Modaler Dialog mit OptionList |

**Features:**
- Positioned at the mouse cursor (`at=(event.screen_x, event.screen_y)`)
- Positionierung am Maus-Cursor (`at=(event.screen_x, event.screen_y)`)
- Off-screen guard pins the menu to the terminal edge if necessary
- Off-Screen-Schutz pinnt das Menü bei Bedarf an den Terminal-Rand
- Optional centered fallback for keyboard-triggered menus
- Optional zentriert als Fallback für Tastatur-Trigger
- Icons as prefix (emoji or unicode), shortcuts right-aligned in dim (display only)
- Icons als Präfix (Emoji oder Unicode), Shortcuts rechtsbündig in dim (reine Anzeige)
- Disabled items rendered greyed out, not selectable
- Deaktivierte Items werden ausgegraut und sind nicht wählbar
- Separators via `ContextMenuItem.separator()`
- Trennlinien über `ContextMenuItem.separator()`
- ESC or click outside dismisses with `None`
- ESC oder Klick außerhalb schließt mit `None`

```python
from textual.events import Click
from textual_widgets import ContextMenuItem, ContextMenuScreen

class FolderBrowser(Tree):
    def on_click(self, event: Click) -> None:
        if event.button != 3:  # right-click only
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
            return  # ESC or outside-click
        # ... handle action ...
```

The `shortcut` field is **display-only** — the consumer wires the keypress via Textual `Bindings`.

Das `shortcut`-Feld ist **reine Anzeige** — den Tastendruck verdrahtet der Konsument selbst über Textual-`Bindings`.

### HamburgerMenu

Collapsible side menu in the DevExpress / Outlook style. Click the hamburger icon at the top to expand or collapse — width animates smoothly. When collapsed, items show only their icons; tooltips reveal their labels on hover. Group headers visually separate sections, and bottom items dock at the bottom (e.g. for Settings).

Klappbares Seitenmenü im DevExpress/Outlook-Stil. Klick auf das Hamburger-Symbol oben blendet das Menü ein oder aus — die Breite wird sanft animiert. Im eingeklappten Zustand zeigen die Items nur Icons; Tooltips beim Hover blenden die Labels ein. Group-Header trennen Abschnitte visuell, Bottom-Items docken unten an (z.B. für Settings).

| Widget | Description / Beschreibung |
|--------|--------------------------|
| `HamburgerItem` | Dataclass with `id`, `label`, optional `icon`. Factories `HamburgerItem.group(label)` and `HamburgerItem.separator()`. |
| `HamburgerMenu` | Widget — list of items + optional bottom items. Posts `ItemSelected` and `Toggled` messages. |

**Features:**
- Animated collapse / expand (width animates with `styles.animate`)
- Animiertes Ein- / Ausklappen
- Click on hamburger icon **or** call `menu.toggle()` programmatically
- Klick auf Hamburger-Symbol **oder** programmatisch via `menu.toggle()`
- Group headers via `HamburgerItem.group("Accounts")` and separators via `HamburgerItem.separator()`
- Group-Header über `HamburgerItem.group("Accounts")`, Trenner über `HamburgerItem.separator()`
- Optional bottom-docked items (Settings, profile, etc.)
- Optional Bottom-Items (Settings, Profil etc.)
- `selected_id` reactive — programmatically highlight the active item
- Reactive `selected_id` für programmatische Hervorhebung
- Tooltips on collapsed items reveal labels on hover
- Tooltips zeigen im eingeklappten Zustand die Labels
- Optional JSON config via `HamburgerMenu.from_json("menu.json")`
- Optional über JSON konfigurierbar (`HamburgerMenu.from_json(...)`)

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

**JSON config / JSON-Konfiguration:**

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

The JSON only describes the structure — selection events still need to be wired up in Python (`on_hamburger_menu_item_selected`), since JSON cannot carry callbacks.

Die JSON-Datei beschreibt nur die Struktur — die Selection-Events werden weiterhin in Python verdrahtet (`on_hamburger_menu_item_selected`), da JSON keine Callbacks transportieren kann.

### Splitter (VerticalSplitter / HorizontalSplitter)

1-cell-wide / -tall dividers between two panels — drag with the mouse to resize the adjacent panel. Comparable to the splitters in IDEs / VS Code. A centered drag handle (`┊` vertical, `┄` horizontal) marks the grab zone visually.

1-Zellen-breite / -hohe Trennlinien zwischen zwei Panels — per Maus-Drag lässt sich die Größe des angrenzenden Panels ändern. Vergleichbar mit den Splittern in IDEs / VS Code. Ein zentrierter Drag-Handle (`┊` vertikal, `┄` horizontal) markiert die Greifzone visuell.

| Widget | Description / Beschreibung |
|--------|--------------------------|
| `VerticalSplitter` | Vertical line in a `Horizontal` container — adjusts the width of the left panel / Vertikale Linie in `Horizontal` — ändert die Breite des linken Panels |
| `HorizontalSplitter` | Horizontal line in a `Vertical` container — adjusts the height of the top panel / Horizontale Linie in `Vertical` — ändert die Höhe des oberen Panels |

**Features:**
- Centered drag-handle glyph
- Zentrierter Drag-Handle-Glyph
- Hover and active drag colour the splitter in `$accent`
- Hover und aktiver Drag färben den Splitter in `$accent`
- `min_size` / `max_size` constraints
- `min_size`- und `max_size`-Beschränkungen
- Target via `target_id` or as the previous DOM sibling
- Target über `target_id` oder als vorhergehendes Geschwister im DOM
- `Resized` message after drag — consumer persists the new size
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

**CSS requirement:** the target panel needs a size the splitter can override (a percent or cells default both work; `1fr` is too flexible).

**CSS-Voraussetzung:** Das Target-Panel braucht eine Größe, die der Splitter überschreiben kann (Prozent- oder Zellen-Default sind beide in Ordnung, `1fr` wäre zu flexibel).

## Installation

```bash
pip install "textual-widgets @ git+https://github.com/michaelblaess/textual-widgets.git"
```

With storybook and retro themes / Mit Storybook und Retro-Themes:

```bash
pip install "textual-widgets[storybook] @ git+https://github.com/michaelblaess/textual-widgets.git"
```

Or in `pyproject.toml` / Oder in `pyproject.toml`:

```toml
dependencies = [
    "textual-widgets @ git+https://github.com/michaelblaess/textual-widgets.git@v0.6.0",
]
```

## Dependencies / Abhängigkeiten

- Python ≥ 3.12
- textual ≥ 0.40
- rich ≥ 13.0
- *(optional, for / für `[storybook]`)* `textual-themes`

## Used by / Verwendet von

- **[retro-amp](https://github.com/michaelblaess/retro-amp)** — Terminal music player with retro charm. Uses `SearchInputWithHistory` for global search, `ContextMenuScreen` for the visualizer mode switch, and the splitter widgets for the resizable panel layout.

  Terminal-Musikplayer mit Retro-Charme. Nutzt `SearchInputWithHistory` für die globale Suche, `ContextMenuScreen` für den Visualizer-Mode-Switch und die Splitter-Widgets für anpassbare Panel-Größen.

## License / Lizenz

Apache License 2.0
