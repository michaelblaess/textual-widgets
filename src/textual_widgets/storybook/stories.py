"""Story-Widgets — pro textual-widgets-Komponente eine Showcase-Page.

Jede Story zeigt:
- Eine kurze Beschreibung
- Das Widget live, mit echten Beispiel-Daten
- Ein Code-Snippet fuer den Einsatz
"""
from __future__ import annotations

from datetime import date

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widget import Widget
from textual.widgets import Button, Input, Label, Static

from textual_widgets.context_menu import ContextMenuItem, ContextMenuScreen
from textual_widgets.date_picker import DatePicker, DatePickerScreen
from textual_widgets.search_history_dropdown import SearchInputWithHistory
from textual_widgets.splitter import HorizontalSplitter, VerticalSplitter


# ----------------------------------------------------------------------
# DatePicker Story
# ----------------------------------------------------------------------


class DatePickerStory(Widget):
    """Zeigt eingebettete DatePicker + Modal-Button."""

    DEFAULT_CSS = """
    DatePickerStory {
        layout: vertical;
        height: 1fr;
        padding: 1 2;
    }
    DatePickerStory .demo-row {
        layout: horizontal;
        height: auto;
        margin-bottom: 1;
    }
    DatePickerStory #picked-date {
        background: $surface-darken-1;
        color: $accent;
        padding: 0 2;
        border: round $accent;
        margin-bottom: 1;
        height: 3;
        content-align: left middle;
    }
    DatePickerStory DatePicker {
        width: 32;
        height: 12;
        border: round $primary;
        margin-right: 2;
    }
    """

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Static(
                "[bold]DatePicker / DatePickerScreen[/bold]",
                classes="story-heading", markup=True,
            )
            yield Static(
                "Kalender-basierter Datums-Picker — eingebettet als Widget oder modal als Screen.",
                classes="story-description",
            )
            yield Static(
                f"[dim]Letztes Auswahl-Ergebnis:[/dim] [bold]{date.today().isoformat()}[/bold]",
                id="picked-date", markup=True,
            )
            with Horizontal(classes="demo-row"):
                yield DatePicker(
                    year=date.today().year,
                    month=date.today().month,
                    selected_day=date.today().day,
                    id="embedded-picker",
                )
                yield Button("Open modal picker", id="open-modal", variant="primary")
            yield Static(
                "[dim]```python\n"
                "from textual_widgets import DatePicker, DatePickerScreen\n\n"
                "# Inline:\n"
                "yield DatePicker(year=2024, month=5, selected_day=21)\n\n"
                "# Modal:\n"
                "self.push_screen(DatePickerScreen(initial_date='2024-05-21'),\n"
                "                 callback=self._on_date)\n"
                "```[/dim]",
                classes="story-code", markup=True,
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "open-modal":
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
            self.query_one("#picked-date", Static).update(
                f"[dim]Letztes Auswahl-Ergebnis:[/dim] [bold]{date_str}[/bold]"
            )
        except Exception:
            pass


# ----------------------------------------------------------------------
# Search Story
# ----------------------------------------------------------------------


class SearchStory(Widget):
    """Zeigt SearchInputWithHistory mit Beispiel-Eintraegen."""

    DEFAULT_CSS = """
    SearchStory {
        layout: vertical;
        height: 1fr;
        padding: 1 2;
    }
    SearchStory #search-result {
        background: $surface-darken-1;
        color: $accent;
        padding: 1 2;
        border: round $accent;
        margin-top: 1;
        height: auto;
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
            yield Static(
                "[bold]SearchInputWithHistory[/bold]",
                classes="story-heading", markup=True,
            )
            yield Static(
                "Such-Input mit permanentem Lupen-Icon und Verlauf-Dropdown. "
                "Beim Tippen filtert das Dropdown nach Substrings; Treffer werden hervorgehoben. "
                "Probiere 'lana', 'kraf' oder 'amiga' — und Delete im Dropdown loescht den Eintrag.",
                classes="story-description",
            )
            yield SearchInputWithHistory(
                icon="🔍",
                placeholder="Beispielsuche / Sample search ...",
                entries=self._entries,
                input_id="story-search-input",
                dropdown_id="story-search-dropdown",
                id="story-search",
            )
            yield Static(
                "[dim]Submit (Enter) zeigt die Query unten an.[/dim]",
                classes="story-description", markup=True,
            )
            yield Static(
                "[dim]Letzter Submit:[/dim] —",
                id="search-result", markup=True,
            )
            yield Static(
                "[dim]```python\n"
                "from textual_widgets import SearchInputWithHistory\n\n"
                "yield SearchInputWithHistory(\n"
                "    icon='🔍',\n"
                "    placeholder='Search ...',\n"
                "    entries=history.list_recent(20),\n"
                "    id='global-search',\n"
                ")\n"
                "```[/dim]",
                classes="story-code", markup=True,
            )

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "story-search-input":
            return
        query = event.value.strip()
        if not query:
            return
        # Verlauf simulieren — Eintrag oben aufnehmen
        if query in self._entries:
            self._entries.remove(query)
        self._entries.insert(0, query)
        self._entries = self._entries[:20]
        try:
            wrapper = self.query_one("#story-search", SearchInputWithHistory)
            wrapper.set_entries(self._entries)
            wrapper.hide_dropdown()
            self.query_one("#search-result", Static).update(
                f"[dim]Letzter Submit:[/dim] [bold]{query}[/bold]"
            )
        except Exception:
            pass

    def on_search_input_with_history_history_entry_delete_requested(
        self, event: SearchInputWithHistory.HistoryEntryDeleteRequested,
    ) -> None:
        if event.entry in self._entries:
            self._entries.remove(event.entry)
        try:
            wrapper = self.query_one("#story-search", SearchInputWithHistory)
            wrapper.set_entries(self._entries)
        except Exception:
            pass


# ----------------------------------------------------------------------
# ContextMenu Story
# ----------------------------------------------------------------------


class ContextMenuStory(Widget):
    """Zeigt ContextMenuScreen mit Right-Click-Trigger."""

    DEFAULT_CSS = """
    ContextMenuStory {
        layout: vertical;
        height: 1fr;
        padding: 1 2;
    }
    ContextMenuStory #click-area {
        height: 12;
        background: $surface-darken-1;
        border: round $primary;
        content-align: center middle;
        text-style: bold;
        color: $text-muted;
        margin-bottom: 1;
    }
    ContextMenuStory #click-area:hover {
        border: round $accent;
        color: $accent;
    }
    ContextMenuStory #last-action {
        background: $surface-darken-1;
        color: $accent;
        padding: 1 2;
        border: round $accent;
        height: auto;
    }
    """

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Static(
                "[bold]ContextMenuScreen[/bold]",
                classes="story-heading", markup=True,
            )
            yield Static(
                "Wiederverwendbares Kontext-Menue. Right-Click in den Bereich "
                "unten, um das Menue an der Cursor-Position zu oeffnen.",
                classes="story-description",
            )
            yield Static(
                "RIGHT-CLICK HERE",
                id="click-area",
            )
            yield Static(
                "[dim]Letzte Aktion:[/dim] —",
                id="last-action", markup=True,
            )
            yield Static(
                "[dim]```python\n"
                "from textual_widgets import ContextMenuItem, ContextMenuScreen\n\n"
                "items = [\n"
                "    ContextMenuItem('open', 'Open', icon='📂', shortcut='Enter'),\n"
                "    ContextMenuItem('rename', 'Rename', icon='✎', shortcut='Ctrl+R'),\n"
                "    ContextMenuItem.separator(),\n"
                "    ContextMenuItem('delete', 'Delete', icon='✕'),\n"
                "]\n"
                "self.app.push_screen(\n"
                "    ContextMenuScreen(items, at=(event.screen_x, event.screen_y)),\n"
                "    callback=self._on_action,\n"
                ")\n"
                "```[/dim]",
                classes="story-code", markup=True,
            )

    def on_click(self, event) -> None:
        # Nur Right-Click in der Click-Area
        if event.button != 3:
            return
        target = self.query_one("#click-area", Static)
        if not target.region.contains(event.screen_x, event.screen_y):
            return
        items = [
            ContextMenuItem("open", "Open", icon="📂", shortcut="Enter"),
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
            label = self.query_one("#last-action", Static)
        except Exception:
            return
        if action_id is None:
            label.update("[dim]Letzte Aktion:[/dim] [italic]ESC / outside-click → cancelled[/italic]")
        else:
            label.update(f"[dim]Letzte Aktion:[/dim] [bold]{action_id}[/bold]")


# ----------------------------------------------------------------------
# Splitter Story
# ----------------------------------------------------------------------


class SplitterStory(Widget):
    """Zeigt VerticalSplitter + HorizontalSplitter im Live-Layout."""

    DEFAULT_CSS = """
    SplitterStory {
        layout: vertical;
        height: 1fr;
        padding: 1 2;
    }
    SplitterStory #splitter-demo {
        layout: horizontal;
        height: 18;
        margin-bottom: 1;
    }
    SplitterStory #demo-left {
        width: 30%;
        min-width: 15;
        background: $surface-darken-1;
        border: round $primary;
        content-align: center middle;
    }
    SplitterStory #demo-right {
        width: 1fr;
        layout: vertical;
    }
    SplitterStory #demo-top {
        height: 50%;
        min-height: 3;
        background: $surface-darken-1;
        border: round $primary;
        content-align: center middle;
    }
    SplitterStory #demo-bottom {
        height: 1fr;
        background: $surface-darken-1;
        border: round $primary;
        content-align: center middle;
    }
    SplitterStory #last-resize {
        background: $surface-darken-1;
        color: $accent;
        padding: 1 2;
        border: round $accent;
        height: auto;
    }
    """

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Static(
                "[bold]VerticalSplitter / HorizontalSplitter[/bold]",
                classes="story-heading", markup=True,
            )
            yield Static(
                "Drag-resizable Panels. Splitter haben einen zentrierten "
                "Drag-Handle (┊ / ┄). Hover faerbt sie, Drag passt die "
                "Groesse des Targets an.",
                classes="story-description",
            )
            with Container(id="splitter-demo"):
                yield Static("Left panel\n(width: 30%)", id="demo-left")
                yield VerticalSplitter(target_id="demo-left", min_size=15)
                with Vertical(id="demo-right"):
                    yield Static("Top panel\n(height: 50%)", id="demo-top")
                    yield HorizontalSplitter(target_id="demo-top", min_size=3)
                    yield Static("Bottom panel\n(height: 1fr)", id="demo-bottom")
            yield Static(
                "[dim]Letzte Aenderung:[/dim] —",
                id="last-resize", markup=True,
            )
            yield Static(
                "[dim]```python\n"
                "from textual_widgets import VerticalSplitter, HorizontalSplitter\n\n"
                "with Horizontal():\n"
                "    yield Panel(id='left', classes='left-pane')   # width: 30%\n"
                "    yield VerticalSplitter(target_id='left', min_size=15)\n"
                "    with Vertical():\n"
                "        yield Panel(id='top', classes='top-pane') # height: 50%\n"
                "        yield HorizontalSplitter(target_id='top', min_size=3)\n"
                "        yield Panel(classes='bottom-pane')        # height: 1fr\n"
                "```[/dim]",
                classes="story-code", markup=True,
            )

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
            self.query_one("#last-resize", Static).update(
                f"[dim]Letzte Aenderung:[/dim] "
                f"[bold]{target}[/bold].{axis} = [bold]{size}[/bold] cells"
            )
        except Exception:
            pass
