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

## Lizenz

Apache License 2.0
