# textual-widgets

Wiederverwendbare [Textual](https://textual.textualize.io/) Widgets fuer TUI-Anwendungen.

Reusable [Textual](https://textual.textualize.io/) widgets for terminal user interfaces.

## Storybook

```bash
python -m textual_widgets.storybook
```

Startet eine interaktive Showcase-App mit allen Widgets — wechselbare Themes (Ctrl+P), Live-Beispiele, Code-Snippets. Ideal zum Ausprobieren vor der Integration.

Launches an interactive showcase app with every widget — switchable themes (Ctrl+P), live examples, code snippets. Perfect for trying things out before wiring them into your app.

## Widgets / Widgets

### DatePicker

Kalender-basierter Datums-Picker mit deutschen Monatsnamen, Wochenend-Hervorhebung und Klick-Auswahl.

Calendar-based date picker with German month names, weekend highlighting and click-to-select.

Drei Abstraktionsstufen / Three abstraction levels:

| Widget | Beschreibung / Description |
|--------|--------------------------|
| `CalendarGrid` | Reines Kalender-Grid (Rich Text) zum Einbetten / Pure calendar grid for embedding |
| `DatePicker` | Grid + Monats-/Jahresnavigation / Grid + month/year navigation |
| `DatePickerScreen` | Modaler Dialog / Modal dialog |

**Features:**
- Deutsche Monatsnamen und Wochentage (Mo-So) / German month names and weekdays
- Wochenenden farblich hervorgehoben / Weekends colour-highlighted
- Heutiges Datum unterstrichen / Today's date underlined
- Ausgewaehltes Datum invers / Selected date inversed
- Monats- und Jahresnavigation `<` `>` `<<` `>>` / Month and year navigation
- "Heute"-Schnellauswahl / "Today" shortcut
- Klick auf Tag gibt `YYYY-MM-DD` zurueck / Click returns ISO date

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

Such-Verlauf-Dropdown mit Substring-Filter und Treffer-Hervorhebung.
`SearchInputWithHistory` ist die fertig verdrahtete Variante mit optionalem permanentem Icon-Praefix.

Search-history dropdown with substring filtering and match highlighting.
`SearchInputWithHistory` is the prewired variant with an optional permanent icon prefix.

| Widget | Beschreibung / Description |
|--------|--------------------------|
| `SearchHistoryDropdown` | OptionList mit Filter + Highlighting / OptionList with filter + highlighting |
| `SearchInputWithHistory` | Input + Dropdown verdrahtet, optional mit Icon / Input + dropdown wired together, optional icon |

**Features:**
- Substring-Filter (case-insensitive) waehrend des Tippens / Live substring filter while typing
- Treffer hervorgehoben (Accent, fett) / Matches highlighted in accent + bold
- Pfeile/Maus zur Auswahl, `Enter` uebernimmt + submitet / Arrows/mouse to pick, Enter selects and submits
- `Delete` loescht Eintrag aus dem Verlauf / Delete removes an entry
- `Escape` schliesst Dropdown / Escape closes dropdown
- Optional: permanentes Icon-Praefix (`icon="🔍"`) — wie Textual Command-Palette / Optional permanent icon prefix like the command palette

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
        # Refresh dropdown:
        wrapper = self.query_one("#global-search", SearchInputWithHistory)
        wrapper.set_entries(self._history.list_recent(20))
        # ... start search ...
```

### ContextMenu

Wiederverwendbares Kontextmenue als ModalScreen. Items werden als Liste von `ContextMenuItem` deklariert; das Widget uebernimmt Layout, Cursor-Positionierung, Tastatur-Navigation und Theme-Farben.

Reusable context menu modal screen. Items are declared as a list of `ContextMenuItem`; the widget handles layout, cursor positioning, keyboard navigation, and theme colours.

| Widget | Beschreibung / Description |
|--------|--------------------------|
| `ContextMenuItem` | Dataclass: `id`, `label`, optional `icon`, `shortcut`, `enabled` |
| `ContextMenuScreen` | Modaler Dialog mit OptionList / Modal dialog with OptionList |

**Features:**
- Positionierung am Maus-Cursor / Positioned at the mouse cursor
- Off-Screen-Schutz: Menue wird an den Terminal-Rand gepinnt / Off-screen guard pins the menu to the terminal edge
- Optional zentriert (Tastatur-Trigger) / Optional centered (keyboard trigger)
- Icons als Praefix (Emoji oder Unicode) / Icons as prefix (emoji or unicode)
- Shortcuts rechtsbuendig in `dim` (reine Anzeige) / Shortcuts right-aligned in dim — display only
- Disabled Items werden ausgegraut / Disabled items rendered greyed
- Separator-Trennlinien via `ContextMenuItem.separator()` / Separator lines via factory
- ESC oder Click ausserhalb → `None` / ESC or click outside → `None`

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
            return
        # ... handle action ...
```

**Hinweis zu Shortcuts / About shortcuts:** Das `shortcut`-Feld wird nur angezeigt — den Tastendruck muss der Konsument selbst ueber Bindings binden.
The `shortcut` field is display-only — the consumer wires the keypress via Bindings.

### Splitter (VerticalSplitter / HorizontalSplitter)

1-Zellen-breite/-hohe Trennlinien zwischen zwei Panels — per Maus-Drag laesst sich die Groesse des angrenzenden Panels veraendern. Vergleichbar mit den Splittern in IDEs / VS Code. Ein zentrierter Drag-Handle (gestrichelt: `┊` vertikal, `┄` horizontal) markiert die Greifzone visuell.

1-cell-wide/tall dividers between two panels — drag with the mouse to resize the adjacent panel. Comparable to the splitters in IDEs / VS Code. A centered drag handle (`┊` vertical, `┄` horizontal) marks the grab zone visually.

| Widget | Beschreibung / Description |
|--------|--------------------------|
| `VerticalSplitter` | Vertikale Linie in `Horizontal` — aendert die Breite des linken Panels / Vertical line in a Horizontal container — adjusts the width of the left panel |
| `HorizontalSplitter` | Horizontale Linie in `Vertical` — aendert die Hoehe des oberen Panels / Horizontal line in a Vertical container — adjusts the height of the top panel |

**Features:**
- Drag-Handle-Glyph zentriert auf dem Splitter / Centered drag-handle glyph
- Hover/Drag-State faerbt den Splitter in `$accent` / Hover/drag state colours the splitter in accent
- `min_size` / `max_size`-Constraints / Min/max size constraints
- Target via `target_id` oder vorhergehender Sibling / Target via id or previous sibling
- `Resized`-Message fuer Persistenz beim Konsumenten / Resized message for the consumer to persist sizes

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

**CSS-Voraussetzung / CSS requirement:** Das Target-Panel braucht eine vom Splitter ueberschreibbare Groesse (Prozent-Default oder Cells-Default sind beide OK, `1fr` waere zu flexibel).
The target panel needs a size the splitter can override (percent or cells default; `1fr` is too flexible).

## Installation

```bash
pip install "textual-widgets @ git+https://github.com/michaelblaess/textual-widgets.git"
```

Mit Storybook und Retro-Themes / With storybook and retro themes:

```bash
pip install "textual-widgets[storybook] @ git+https://github.com/michaelblaess/textual-widgets.git"
```

Oder in `pyproject.toml` / Or in `pyproject.toml`:

```toml
dependencies = [
    "textual-widgets @ git+https://github.com/michaelblaess/textual-widgets.git@v0.6.0",
]
```

## Abhaengigkeiten / Dependencies

- Python >= 3.12
- textual >= 0.40
- rich >= 13.0
- *(optional, fuer / for `[storybook]`)* `textual-themes`

## Verwendet von / Used by

- **[retro-amp](https://github.com/michaelblaess/retro-amp)** — Terminal-Musikplayer mit Retro-Charme.
  Nutzt `SearchInputWithHistory` (globale Suche mit Lupen-Icon und Verlauf),
  `ContextMenuScreen` (Right-Click auf den Spektral-Visualizer fuer Mode-Switch)
  und `VerticalSplitter` / `HorizontalSplitter` (Maus-Drag zum Anpassen der
  Panel-Groessen). /
  Terminal music player with retro charm. Uses `SearchInputWithHistory` for
  global search, `ContextMenuScreen` for the visualizer mode switch, and the
  `Splitter` widgets for the resizable panel layout.

## Lizenz / License

Apache License 2.0
