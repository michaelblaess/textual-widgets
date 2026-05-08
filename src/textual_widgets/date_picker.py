"""Kalender-basierter Datums-Picker mit deutschen Monatsnamen.

Drei Komponenten mit unterschiedlichem Abstraktionsgrad:

- ``CalendarGrid`` — reines Kalender-Grid (klickbar, kein Chrome)
- ``DatePicker`` — kompletter Picker mit Navigation (einbettbar)
- ``DatePickerScreen`` — modaler Dialog (gibt ``str | None`` zurueck)
"""

import calendar
from datetime import date

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.events import Click
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, Static

_MONTH_NAMES = [
    "Januar", "Februar", "Maerz", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
]


# ------------------------------------------------------------------
# CalendarGrid — reines Kalender-Grid
# ------------------------------------------------------------------


class CalendarGrid(Static):
    """Kalender-Grid fuer einen Monat, gerendert als Rich Text.

    Klick auf einen Tag sendet ``CalendarGrid.DayClicked``.
    Wochenenden (Sa/So) werden farblich hervorgehoben.
    Der heutige Tag wird unterstrichen dargestellt.
    """

    CELL_WIDTH = 4

    DEFAULT_CSS = """
    CalendarGrid {
        height: auto;
    }
    """

    class DayClicked(Message):
        """Wird gesendet wenn ein Tag angeklickt wird."""

        def __init__(self, day: int) -> None:
            super().__init__()
            self.day = day

    def __init__(
        self,
        year: int | None = None,
        month: int | None = None,
        selected_day: int = 0,
        weekend_style: str = "#cc8800",
        today_style: str = "bold underline #00cccc",
        selected_style: str = "bold reverse",
        header_style: str = "bold dim",
        weekend_header_style: str = "bold #cc8800",
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)
        today = date.today()
        self._year = year or today.year
        self._month = month or today.month
        self._today = today
        self._selected_day = selected_day
        self._selected_year = self._year
        self._selected_month = self._month
        self._weeks: list[list[int]] = []
        self._weekend_style = weekend_style
        self._today_style = today_style
        self._selected_style = selected_style
        self._header_style = header_style
        self._weekend_header_style = weekend_header_style
        self._rebuild_weeks()

    @property
    def year(self) -> int:
        return self._year

    @property
    def month(self) -> int:
        return self._month

    def _rebuild_weeks(self) -> None:
        """Berechnet die Wochen-Matrix fuer den aktuellen Monat."""
        cal = calendar.Calendar(firstweekday=0)
        self._weeks = cal.monthdayscalendar(self._year, self._month)

    def set_month(self, year: int, month: int) -> None:
        """Setzt Monat und Jahr und aktualisiert die Anzeige."""
        self._year = year
        self._month = month
        self._rebuild_weeks()
        self.refresh()

    def render(self) -> Text:
        """Rendert den Kalender als Rich Text."""
        text = Text()
        headers = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
        for i, wd in enumerate(headers):
            style = self._weekend_header_style if i >= 5 else self._header_style
            text.append(f" {wd} ", style=style)
        text.append("\n")

        is_today_month = (self._year == self._today.year
                         and self._month == self._today.month)
        show_selected = (self._selected_day > 0
                         and self._year == self._selected_year
                         and self._month == self._selected_month)
        for week in self._weeks:
            for i, day in enumerate(week):
                if day == 0:
                    text.append("    ")
                else:
                    if show_selected and day == self._selected_day:
                        style = self._selected_style
                    elif is_today_month and day == self._today.day:
                        style = self._today_style
                    elif i >= 5:
                        style = self._weekend_style
                    else:
                        style = ""
                    text.append(f" {day:>2} ", style=style)
            text.append("\n")

        return text

    def on_click(self, event: Click) -> None:
        """Erkennt welcher Tag angeklickt wurde."""
        col = event.x // self.CELL_WIDTH
        row = event.y - 1
        if 0 <= col < 7 and 0 <= row < len(self._weeks):
            day = self._weeks[row][col]
            if day > 0:
                self.post_message(self.DayClicked(day))


# ------------------------------------------------------------------
# DatePicker — kompletter Picker mit Navigation
# ------------------------------------------------------------------


class DatePicker(Vertical):
    """Kalender-Picker mit Monats-/Jahresnavigation.

    Einbettbar in jede View oder Screen.
    Sendet ``DatePicker.DateSelected`` bei Tagesauswahl.
    """

    DEFAULT_CSS = """
    DatePicker {
        height: auto;
        width: auto;
        padding: 0;
        background: transparent;
    }
    DatePicker .dp-nav-row {
        height: 1;
        margin-bottom: 1;
        background: transparent;
    }
    DatePicker .dp-nav-btn {
        min-width: 3;
        height: 1;
        border: none;
        background: transparent;
        color: $accent;
        padding: 0;
        text-style: bold;
    }
    /* Default Button:focus setzt `text-style: bold reverse` — das `reverse`
       invertiert Vorder- und Hintergrundfarbe und erzeugt einen sichtbaren
       Block, sobald der Button (z.B. beim Oeffnen des Modal-Dialogs) Focus
       bekommt. Wir uebersteuern das explizit, damit die Nav-Buttons in jedem
       State transparent bleiben. */
    DatePicker .dp-nav-btn:focus,
    DatePicker .dp-nav-btn.-active {
        background: transparent;
        text-style: bold;
        border: none;
    }
    DatePicker .dp-nav-btn:hover {
        background: $accent 30%;
        text-style: bold;
    }
    DatePicker .dp-month-label {
        width: 1fr;
        text-align: center;
        color: $text;
        text-style: bold;
        background: transparent;
    }
    DatePicker .dp-today-hint {
        text-align: center;
        color: $text-muted;
        margin-top: 1;
        background: transparent;
    }
    """

    class DateSelected(Message):
        """Wird gesendet wenn ein Datum ausgewaehlt wird."""

        def __init__(self, date_str: str) -> None:
            super().__init__()
            self.date_str = date_str

    def __init__(
        self,
        year: int | None = None,
        month: int | None = None,
        selected_day: int = 0,
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)
        today = date.today()
        self._year = year or today.year
        self._month = month or today.month
        self._today = today
        self._selected_day = selected_day

    def compose(self) -> ComposeResult:
        with Horizontal(classes="dp-nav-row"):
            yield Button("<<", id="dp-prev-year", classes="dp-nav-btn")
            yield Button("<", id="dp-prev-month", classes="dp-nav-btn")
            yield Static(self._format_month(), id="dp-month-label", classes="dp-month-label")
            yield Button(">", id="dp-next-month", classes="dp-nav-btn")
            yield Button(">>", id="dp-next-year", classes="dp-nav-btn")
        yield CalendarGrid(
            self._year, self._month,
            selected_day=self._selected_day,
            id="dp-cal-grid",
        )
        yield Static(
            f"Today: {self._today.strftime('%Y-%m-%d')}",
            classes="dp-today-hint",
        )

    def _format_month(self) -> str:
        return f"{_MONTH_NAMES[self._month - 1]} {self._year}"

    def _update(self) -> None:
        self.query_one("#dp-month-label", Static).update(self._format_month())
        self.query_one("#dp-cal-grid", CalendarGrid).set_month(self._year, self._month)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Reagiert auf Navigations-Buttons."""
        btn_id = event.button.id or ""
        if btn_id == "dp-prev-month":
            if self._month == 1:
                self._month = 12
                self._year -= 1
            else:
                self._month -= 1
            self._update()
        elif btn_id == "dp-next-month":
            if self._month == 12:
                self._month = 1
                self._year += 1
            else:
                self._month += 1
            self._update()
        elif btn_id == "dp-prev-year":
            self._year -= 1
            self._update()
        elif btn_id == "dp-next-year":
            self._year += 1
            self._update()

    def on_calendar_grid_day_clicked(self, event: CalendarGrid.DayClicked) -> None:
        """Leitet Tagesklick als DateSelected weiter."""
        date_str = f"{self._year}-{self._month:02d}-{event.day:02d}"
        self.post_message(self.DateSelected(date_str))


# ------------------------------------------------------------------
# DatePickerScreen — modaler Dialog
# ------------------------------------------------------------------


class DatePickerScreen(ModalScreen[str | None]):
    """Kalender-Dialog zur Datumsauswahl.

    Gibt ``YYYY-MM-DD`` zurueck oder ``None`` bei Abbruch.
    """

    DEFAULT_CSS = """
    DatePickerScreen {
        align: center middle;
    }
    DatePickerScreen > Vertical {
        width: 38;
        height: auto;
        max-height: 20;
        background: $surface;
        border: double $accent;
        padding: 1 2;
    }
    DatePickerScreen #dps-title {
        text-style: bold;
        color: $accent;
        text-align: center;
    }
    DatePickerScreen .dps-button-row {
        height: auto;
        align: center middle;
    }
    DatePickerScreen .dps-button-row Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, initial_date: str = "", **kwargs: object) -> None:
        super().__init__(**kwargs)
        today = date.today()
        self._today = today
        year = today.year
        month = today.month
        self._selected_day = 0
        if initial_date:
            try:
                parts = initial_date.split("-")
                year = int(parts[0])
                month = int(parts[1])
                if len(parts) >= 3 and parts[2]:
                    self._selected_day = int(parts[2])
            except (ValueError, IndexError):
                pass
        self._year = year
        self._month = month

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Select date", id="dps-title")
            yield DatePicker(
                self._year, self._month,
                selected_day=self._selected_day,
                id="dps-picker",
            )
            with Horizontal(classes="dps-button-row"):
                yield Button("Today", variant="primary", id="dps-today")
                yield Button("Cancel", id="dps-cancel")

    def on_date_picker_date_selected(self, event: DatePicker.DateSelected) -> None:
        """Tag wurde ausgewaehlt."""
        self.dismiss(event.date_str)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Reagiert auf Buttons."""
        btn_id = event.button.id or ""
        if btn_id == "dps-today":
            self.dismiss(self._today.strftime("%Y-%m-%d"))
        elif btn_id == "dps-cancel":
            self.dismiss(None)

    def action_cancel(self) -> None:
        """Bricht ab."""
        self.dismiss(None)
