"""Story-Widgets — pro textual-widgets-Komponente eine Showcase-Page.

Jede Story zeigt:
- Eine kurze Beschreibung
- Das Widget live, mit echten Beispiel-Daten
- Ein Code-Snippet (raw, markup=False) fuer den Einsatz

Wichtig zum Markup: Code-Snippets enthalten viele eckige Klammern (Listen,
Type-Hints, ...) die Textual sonst als Markup-Tags interpretiert und
Crashes ausloesen. Daher haben alle Code-Static-Widgets `markup=False`.
"""
from __future__ import annotations

from datetime import date

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widget import Widget
from textual.widgets import Button, Input, Static

from textual_widgets.context_menu import ContextMenuItem, ContextMenuScreen
from textual_widgets.date_picker import DatePicker, DatePickerScreen
from textual_widgets.search_history_dropdown import SearchInputWithHistory
from textual_widgets.splitter import HorizontalSplitter, VerticalSplitter


# ----------------------------------------------------------------------
# DatePicker
# ----------------------------------------------------------------------


_DATEPICKER_CODE = """\
from textual_widgets import DatePicker, DatePickerScreen

# Inline:
yield DatePicker(year=2024, month=5, selected_day=21)

# Modal:
self.push_screen(DatePickerScreen(initial_date='2024-05-21'),
                 callback=self._on_date)
"""


class DatePickerStory(Widget):
    """Zeigt eingebettete DatePicker + Modal-Button."""

    DEFAULT_CSS = """
    DatePickerStory {
        layout: vertical;
        height: 1fr;
    }
    DatePickerStory .demo-row {
        layout: horizontal;
        height: auto;
        margin-bottom: 1;
    }
    DatePickerStory DatePicker {
        width: 32;
        height: 12;
        border: round $primary;
        margin-right: 2;
    }
    DatePickerStory Button {
        height: 3;
    }
    """

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Static("DatePicker / DatePickerScreen", classes="story-heading")
            yield Static(
                "Kalender-basierter Datums-Picker — eingebettet als Widget oder "
                "modal als Screen. Beide liefern ein ISO-Datum (YYYY-MM-DD) "
                "an einen Callback.",
                classes="story-description",
            )
            yield Static(
                f"Letztes Auswahl-Ergebnis: {date.today().isoformat()}",
                id="dp-result", classes="story-result",
            )
            with Horizontal(classes="demo-row"):
                yield DatePicker(
                    year=date.today().year,
                    month=date.today().month,
                    selected_day=date.today().day,
                    id="dp-embedded",
                )
                yield Button("Open modal picker", id="dp-open-modal", variant="primary")
            yield Static(_DATEPICKER_CODE, markup=False, classes="story-code")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "dp-open-modal":
            self.app.push_screen(
                DatePickerScreen(initial_date=date.today().isoformat()),
                callback=self._on_picked,
            )

    def on_date_picker_date_selected(self, event: DatePicker.DateSelected) -> None:
        self._show_picked(event.date_str)

    def _on_picked(self, date_str: str | None) -> None:
        if date_str:
            self._show_picked(date_str)

    def _show_picked(self, date_str: str) -> None:
        try:
            self.query_one("#dp-result", Static).update(
                f"Letztes Auswahl-Ergebnis: {date_str}"
            )
        except Exception:
            pass


# ----------------------------------------------------------------------
# Search
# ----------------------------------------------------------------------


_SEARCH_CODE = """\
from textual_widgets import SearchInputWithHistory

yield SearchInputWithHistory(
    icon='\U0001f50d',
    placeholder='Search ...',
    entries=history.list_recent(20),
    id='global-search',
)

def on_input_submitted(self, event):
    query = event.value.strip()
    if query:
        history.add(query)
        self.query_one('#global-search').set_entries(history.list_recent(20))
"""


class SearchStory(Widget):
    """Zeigt SearchInputWithHistory mit Beispiel-Eintraegen."""

    DEFAULT_CSS = """
    SearchStory {
        layout: vertical;
        height: 1fr;
    }
    """

    SAMPLE_HISTORY = [
        "lana del rey",
        "best of mylene",
        "kraftwerk",
        "amiga modules",
        "c64 sid",
        "depeche mode",
        "joy division",
        "the cure",
        "talk talk",
        "bowie",
    ]

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._entries = list(self.SAMPLE_HISTORY)

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Static("SearchInputWithHistory", classes="story-heading")
            yield Static(
                "Such-Input mit permanentem Lupen-Icon und Verlauf-Dropdown. "
                "Beim Tippen filtert das Dropdown nach Substrings; Treffer werden "
                "hervorgehoben. Probiere 'lana', 'kraf' oder 'amiga' — und Delete im "
                "Dropdown loescht den Eintrag.",
                classes="story-description",
            )
            yield SearchInputWithHistory(
                icon="\U0001f50d",
                placeholder="Beispielsuche / Sample search ...",
                entries=self._entries,
                input_id="search-story-input",
                dropdown_id="search-story-dropdown",
                id="search-story-wrapper",
            )
            yield Static(
                "Letzter Submit: —",
                id="search-result", classes="story-result",
            )
            yield Static(_SEARCH_CODE, markup=False, classes="story-code")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "search-story-input":
            return
        query = event.value.strip()
        if not query:
            return
        if query in self._entries:
            self._entries.remove(query)
        self._entries.insert(0, query)
        self._entries = self._entries[:20]
        try:
            wrapper = self.query_one("#search-story-wrapper", SearchInputWithHistory)
            wrapper.set_entries(self._entries)
            wrapper.hide_dropdown()
            self.query_one("#search-result", Static).update(f"Letzter Submit: {query}")
        except Exception:
            pass

    def on_search_input_with_history_history_entry_delete_requested(
        self, event: SearchInputWithHistory.HistoryEntryDeleteRequested,
    ) -> None:
        if event.entry in self._entries:
            self._entries.remove(event.entry)
        try:
            wrapper = self.query_one("#search-story-wrapper", SearchInputWithHistory)
            wrapper.set_entries(self._entries)
        except Exception:
            pass


# ----------------------------------------------------------------------
# ContextMenu
# ----------------------------------------------------------------------


_CONTEXTMENU_CODE = """\
from textual_widgets import ContextMenuItem, ContextMenuScreen

items = [
    ContextMenuItem('open', 'Open', icon='\U0001f4c2', shortcut='Enter'),
    ContextMenuItem('rename', 'Rename', icon='✎', shortcut='Ctrl+R'),
    ContextMenuItem.separator(),
    ContextMenuItem('delete', 'Delete', icon='✕'),
]
self.app.push_screen(
    ContextMenuScreen(items, at=(event.screen_x, event.screen_y)),
    callback=self._on_action,
)
"""


class ContextMenuStory(Widget):
    """Zeigt ContextMenuScreen mit Right-Click-Trigger."""

    DEFAULT_CSS = """
    ContextMenuStory {
        layout: vertical;
        height: 1fr;
    }
    ContextMenuStory #cm-click-area {
        height: 12;
        background: $surface-darken-1;
        border: round $primary;
        content-align: center middle;
        text-style: bold;
        color: $text-muted;
        margin-bottom: 1;
    }
    ContextMenuStory #cm-click-area:hover {
        border: round $accent;
        color: $accent;
    }
    """

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Static("ContextMenuScreen", classes="story-heading")
            yield Static(
                "Wiederverwendbares Kontext-Menue. Rechtsklick in den Bereich "
                "unten oeffnet das Menue an der Cursor-Position.",
                classes="story-description",
            )
            yield Static("RIGHT-CLICK HERE", id="cm-click-area")
            yield Static(
                "Letzte Aktion: —",
                id="cm-result", classes="story-result",
            )
            yield Static(_CONTEXTMENU_CODE, markup=False, classes="story-code")

    def on_click(self, event) -> None:
        if event.button != 3:
            return
        try:
            target = self.query_one("#cm-click-area", Static)
        except Exception:
            return
        if not target.region.contains(event.screen_x, event.screen_y):
            return
        items = [
            ContextMenuItem("open", "Open", icon="\U0001f4c2", shortcut="Enter"),
            ContextMenuItem("rename", "Rename", icon="✎", shortcut="Ctrl+R"),
            ContextMenuItem.separator(),
            ContextMenuItem("delete", "Delete", icon="✕", shortcut="Del"),
            ContextMenuItem.separator(),
            ContextMenuItem("info", "Properties", icon="ℹ", shortcut="Alt+Enter"),
            ContextMenuItem("disabled-demo", "Disabled item", enabled=False),
        ]
        self.app.push_screen(
            ContextMenuScreen(items, at=(event.screen_x, event.screen_y)),
            callback=self._on_action,
        )

    def _on_action(self, action_id: str | None) -> None:
        try:
            label = self.query_one("#cm-result", Static)
        except Exception:
            return
        if action_id is None:
            label.update("Letzte Aktion: cancelled (ESC / outside-click)")
        else:
            label.update(f"Letzte Aktion: {action_id}")


# ----------------------------------------------------------------------
# Splitter
# ----------------------------------------------------------------------


_SPLITTER_CODE = """\
from textual_widgets import VerticalSplitter, HorizontalSplitter

with Horizontal():
    yield Panel(id='left', classes='left-pane')      # width: 30%
    yield VerticalSplitter(target_id='left', min_size=15)
    with Vertical():
        yield Panel(id='top', classes='top-pane')    # height: 50%
        yield HorizontalSplitter(target_id='top', min_size=3)
        yield Panel(classes='bottom-pane')           # height: 1fr
"""


class SplitterStory(Widget):
    """Zeigt VerticalSplitter + HorizontalSplitter im Live-Layout."""

    DEFAULT_CSS = """
    SplitterStory {
        layout: vertical;
        height: 1fr;
    }
    SplitterStory #sp-demo {
        layout: horizontal;
        height: 18;
        margin-bottom: 1;
    }
    SplitterStory #sp-left {
        width: 30%;
        min-width: 15;
        background: $surface-darken-1;
        border: round $primary;
        content-align: center middle;
    }
    SplitterStory #sp-right {
        width: 1fr;
        layout: vertical;
    }
    SplitterStory #sp-top {
        height: 50%;
        min-height: 3;
        background: $surface-darken-1;
        border: round $primary;
        content-align: center middle;
    }
    SplitterStory #sp-bottom {
        height: 1fr;
        background: $surface-darken-1;
        border: round $primary;
        content-align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Static("VerticalSplitter / HorizontalSplitter", classes="story-heading")
            yield Static(
                "Drag-resizable Panels mit zentriertem Drag-Handle. Hover faerbt "
                "den Splitter, Drag passt die Groesse des Targets an. Nach jedem "
                "Drag wird eine Resized-Message gepostet (siehe unten).",
                classes="story-description",
            )
            with Container(id="sp-demo"):
                yield Static("Left panel\n(width: 30%)", id="sp-left")
                yield VerticalSplitter(target_id="sp-left", min_size=15)
                with Vertical(id="sp-right"):
                    yield Static("Top panel\n(height: 50%)", id="sp-top")
                    yield HorizontalSplitter(target_id="sp-top", min_size=3)
                    yield Static("Bottom panel\n(height: 1fr)", id="sp-bottom")
            yield Static(
                "Letzte Aenderung: —",
                id="sp-result", classes="story-result",
            )
            yield Static(_SPLITTER_CODE, markup=False, classes="story-code")

    def on_vertical_splitter_resized(
        self, event: VerticalSplitter.Resized,
    ) -> None:
        self._show_resize(event.target_id, event.size, axis="width")

    def on_horizontal_splitter_resized(
        self, event: HorizontalSplitter.Resized,
    ) -> None:
        self._show_resize(event.target_id, event.size, axis="height")

    def _show_resize(self, target: str, size: int, axis: str) -> None:
        try:
            self.query_one("#sp-result", Static).update(
                f"Letzte Aenderung: {target}.{axis} = {size} cells"
            )
        except Exception:
            pass
