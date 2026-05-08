# textual-widgets

Wiederverwendbare [Textual](https://textual.textualize.io/) Widgets fuer TUI-Anwendungen.

## Widgets

### DatePicker

Kalender-basierter Datums-Picker mit deutschen Monatsnamen, Wochenend-Hervorhebung und Klick-Auswahl.

Drei Abstraktionsstufen:

| Widget | Beschreibung | Verwendung |
|--------|-------------|------------|
| `CalendarGrid` | Reines Kalender-Grid (Rich Text) | Einbetten in eigene Layouts |
| `DatePicker` | Grid + Monats-/Jahresnavigation | Einbetten in Formulare |
| `DatePickerScreen` | Modaler Dialog | `push_screen()` mit Callback |

**Features:**
- Deutsche Monatsnamen und Wochentage (Mo-So)
- Wochenenden farblich hervorgehoben
- Heutiges Datum unterstrichen
- Ausgewaehltes Datum invers dargestellt
- Monats- und Jahresnavigation (`<` `>` `<<` `>>`)
- "Heute"-Schnellauswahl
- Klick auf Tag gibt `YYYY-MM-DD` zurueck

**Beispiel — DatePickerScreen (Modal):**

```python
from textual_widgets import DatePickerScreen

def action_pick_date(self) -> None:
    self.push_screen(
        DatePickerScreen(initial_date="2024-05-21"),
        callback=self._on_date_selected,
    )

def _on_date_selected(self, selected: str | None) -> None:
    if selected:
        print(f"Ausgewaehlt: {selected}")  # z.B. "2024-05-21"
```

**Beispiel — DatePicker (eingebettet):**

```python
from textual_widgets import DatePicker

class MyScreen(Screen):
    def compose(self) -> ComposeResult:
        yield DatePicker(year=2024, month=5, selected_day=21)

    def on_date_picker_date_selected(self, event: DatePicker.DateSelected) -> None:
        print(event.date_str)
```

**Beispiel — CalendarGrid (nur Grid):**

```python
from textual_widgets import CalendarGrid

class MyWidget(Vertical):
    def compose(self) -> ComposeResult:
        yield CalendarGrid(year=2024, month=5, selected_day=21)

    def on_calendar_grid_day_clicked(self, event: CalendarGrid.DayClicked) -> None:
        print(f"Tag {event.day} geklickt")
```

### SearchHistoryDropdown

Such-Verlauf-Dropdown mit Substring-Filter und Treffer-Hervorhebung. Ideal fuer
Suchfelder, die haeufig genutzte Eingaben wieder anbieten sollen — beim Tippen
"myl" erscheinen "**myl**ene farmer", "best of **myl**ene", usw. mit
hervorgehobenem Treffer.

Zwei Abstraktionsstufen:

| Widget | Beschreibung | Verwendung |
|--------|-------------|------------|
| `SearchHistoryDropdown` | OptionList mit Filter + Highlighting | Einbetten neben einem eigenen Input |
| `SearchInputWithHistory` | Input + Dropdown verdrahtet | Drop-in fuer einzelnes `Input` |

**Features:**
- Substring-Filter (case-insensitive) waehrend des Tippens
- Treffer im Eintrag hervorgehoben (Accent-Farbe, fett)
- Pfeil-Tasten / Maus zur Auswahl, `Enter` uebernimmt + submitet automatisch
- `Delete` loescht Eintrag aus dem Verlauf (Persistenz beim Host)
- `Escape` schliesst das Dropdown
- Sendet weiterhin `Input.Submitted` — bestehende Submit-Handler bleiben
- Optional: permanentes Icon-Praefix links vom Input (`icon="🔍"`),
  bleibt auch sichtbar wenn Text eingegeben ist — analog zur Textual
  Command Palette

**Beispiel — SearchInputWithHistory (Drop-in):**

```python
from textual.widgets import Input
from textual_widgets import SearchInputWithHistory

class MyApp(App):
    def compose(self) -> ComposeResult:
        yield SearchInputWithHistory(
            icon="🔍",                   # permanent sichtbar (auch mit Text)
            placeholder="Search ...",
            entries=self._history_repo.list_recent(20),  # initiale Liste
            id="global-search",
        )

    def on_input_submitted(self, event: Input.Submitted) -> None:
        # Wird auch bei Auswahl aus dem Dropdown ausgeloest
        query = event.value.strip()
        if not query:
            return
        self._history_repo.add(query)
        # Dropdown-Liste aktualisieren:
        search = self.query_one("#global-search", SearchInputWithHistory)
        search.set_entries(self._history_repo.list_recent(20))
        # ... Suche starten ...

    def on_search_input_with_history_history_entry_delete_requested(
        self, event: SearchInputWithHistory.HistoryEntryDeleteRequested,
    ) -> None:
        self._history_repo.delete(event.entry)
        search = self.query_one("#global-search", SearchInputWithHistory)
        search.set_entries(self._history_repo.list_recent(20))
```

**Beispiel — SearchHistoryDropdown (eigenes Input):**

```python
from textual.widgets import Input
from textual_widgets import SearchHistoryDropdown

class MyScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Input(id="my-input")
        yield SearchHistoryDropdown(entries=["foo", "bar"], id="my-dropdown")

    def on_input_changed(self, event: Input.Changed) -> None:
        dd = self.query_one("#my-dropdown", SearchHistoryDropdown)
        dd.filter(event.value)
        dd.show()

    def on_search_history_dropdown_entry_selected(
        self, event: SearchHistoryDropdown.EntrySelected,
    ) -> None:
        self.query_one("#my-input", Input).value = event.entry
```

### ContextMenu

Wiederverwendbares Kontextmenue als ModalScreen. Items werden deklarativ als
Liste von `ContextMenuItem` uebergeben — der Konsument kuemmert sich um
Trigger (typisch Right-Click) und Aktion. Das Widget uebernimmt Layout,
Positionierung am Maus-Cursor, Tastatur-Navigation und Theme-Farben.

| Widget | Beschreibung | Verwendung |
|--------|-------------|------------|
| `ContextMenuItem` | Dataclass: `id`, `label`, optional `icon`, `shortcut`, `enabled` | Liste an `ContextMenuScreen` uebergeben |
| `ContextMenuScreen` | Modaler Dialog mit OptionList | `push_screen()` mit Callback |

**Features:**
- Positionierung am Maus-Cursor (`at=(event.screen_x, event.screen_y)`),
  Off-Screen-Schutz pinnt das Menue an den Terminal-Rand wenn noetig
- Optional zentriert (Fallback bei Tastatur-Trigger ohne Click-Coords)
- Icons als Praefix vor dem Label (Emoji oder Unicode-Zeichen)
- Tastatur-Shortcuts rechtsbuendig in `dim` als REINE Anzeige
  (Trigger bleibt beim Konsumenten)
- Disabled Items werden ausgegraut und sind nicht waehlbar
- Separator-Trennlinien via `ContextMenuItem.separator()`
- ESC oder Klick ausserhalb schliesst mit `None`
- Theme-Farben via `$accent` / `$surface`

**Beispiel:**

```python
from textual.events import Click
from textual_widgets import ContextMenuItem, ContextMenuScreen

class FolderBrowser(Tree):
    def on_click(self, event: Click) -> None:
        if event.button != 3:  # nur Rechtsklick
            return
        node = self.cursor_node
        if node is None:
            return
        is_dir = bool(node.data and node.data.is_dir())
        items = [
            ContextMenuItem("open", "Oeffnen", icon="📂", shortcut="Enter"),
            ContextMenuItem("rename", "Umbenennen", icon="✎", shortcut="Ctrl+R"),
            ContextMenuItem.separator(),
            ContextMenuItem(
                "delete", "Loeschen", icon="✕", shortcut="Del",
                enabled=not is_dir,  # Verzeichnisse nicht loeschbar
            ),
        ]
        self.app.push_screen(
            ContextMenuScreen(items, at=(event.screen_x, event.screen_y)),
            callback=self._on_menu_action,
        )

    def _on_menu_action(self, action_id: str | None) -> None:
        if action_id is None:
            return  # ESC oder Click-outside
        if action_id == "open":
            self.action_select_cursor()
        elif action_id == "rename":
            ...
```

**Hinweis zu Shortcuts:** Das `shortcut`-Feld wird nur **angezeigt** — den
Tastendruck musst du selbst ueber Bindings am uebergeordneten Widget
abfangen. So bleibt das Menue mit deinem bestehenden Shortcut-Schema
konsistent.

## Installation

```bash
pip install "textual-widgets @ git+https://github.com/michaelblaess/textual-widgets.git"
```

Oder in `pyproject.toml`:

```toml
dependencies = [
    "textual-widgets @ git+https://github.com/michaelblaess/textual-widgets.git",
]
```

## Abhaengigkeiten

- Python >= 3.12
- textual >= 0.40
- rich >= 13.0

### Splitter (VerticalSplitter / HorizontalSplitter)

1-Zellen-breite/-hohe Trennlinien zwischen zwei Panels — per Maus-Drag laesst
sich die Groesse des angrenzenden Panels veraendern. Vergleichbar mit den
Splittern in IDEs / VSCode.

| Widget | Beschreibung |
|--------|-------------|
| `VerticalSplitter` | Vertikale Linie in einem `Horizontal`-Container — Drag aendert die **Breite** des linken Panels |
| `HorizontalSplitter` | Horizontale Linie in einem `Vertical`-Container — Drag aendert die **Hoehe** des oberen Panels |

**Features:**
- Visuelles Feedback: Hover und aktiver Drag-State faerben den Splitter in `$accent`
- Min/Max-Constraints (`min_size`, `max_size`) verhindern unsinnige Groessen
- Target via `target_id` adressierbar oder automatisch als vorhergehendes
  Geschwister-Widget
- Persistenz beim Konsumenten: nach jedem abgeschlossenen Drag wird eine
  `Resized`-Message mit `target_id` und neuer `size` gepostet — die Library
  speichert nichts selbst

**Beispiel — IDE-aehnliches Layout:**

```python
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual_widgets import VerticalSplitter, HorizontalSplitter

class MyApp(App):
    def compose(self) -> ComposeResult:
        with Horizontal():
            yield FolderBrowser(id="folder", classes="left-pane")
            yield VerticalSplitter(target_id="folder", min_size=15, max_size=80)
            with Vertical(classes="right-side"):
                yield FileTable(id="files", classes="top-pane")
                yield HorizontalSplitter(target_id="files", min_size=5)
                yield Lyrics(classes="bottom-pane")

    def on_vertical_splitter_resized(
        self, event: VerticalSplitter.Resized,
    ) -> None:
        # Persistenz: Konsument speichert die Groesse
        self._settings.set_panel_size(event.target_id, event.size)

    def on_horizontal_splitter_resized(
        self, event: HorizontalSplitter.Resized,
    ) -> None:
        self._settings.set_panel_size(event.target_id, event.size)
```

**CSS-Voraussetzung:** Das Target-Panel braucht eine **konkrete Groesse**
(`width` bzw. `height` in Zellen oder Prozent), kein `1fr`, sonst kann das
Drag-Resize nicht wirksam werden. Das gegenueberliegende Panel kann dagegen
ruhig `1fr` haben — es nimmt den Restplatz.

**Hinweis Persistenz:** Beim App-Start kannst du die gespeicherte Groesse
einfach via `widget.styles.width = saved_size` (bzw. `height`) wieder setzen.
Die Library haelt sich vom Storage fern.

## Verwendet von / Used by

- **[retro-amp](https://github.com/michaelblaess/retro-amp)** — Terminal-Musikplayer
  mit Retro-Charme. Nutzt `SearchInputWithHistory` fuer die globale Suche
  und `ContextMenuScreen` fuer den Visualizer-Mode-Switch (Right-Click auf
  den Spektral-Visualizer).

## Lizenz

Apache License 2.0
