"""Story widgets — one showcase page per textual-widgets component.

Each story contains:
- A short description
- The widget live, with sample data
- A code snippet (raw, markup=False) showing how to use it

Note on markup: code snippets contain a lot of square brackets (lists,
type hints, ...) which Textual otherwise interprets as markup tags and
crashes on. All code Static widgets therefore use markup=False; the
"dim code" look comes from the .story-code CSS class.
"""

from __future__ import annotations

import contextlib
import traceback
from datetime import date

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widget import Widget
from textual.widgets import Button, Checkbox, Input, Label, Select, Static, TabPane

from textual_widgets import __author__, __version__
from textual_widgets.about_screen import AboutScreen
from textual_widgets.context_menu import ContextMenuItem, ContextMenuScreen
from textual_widgets.crash_guard import ErrorScreen
from textual_widgets.date_picker import DatePicker, DatePickerScreen
from textual_widgets.hamburger_menu import HamburgerItem, HamburgerMenu
from textual_widgets.info_header import InfoAction, InfoHeader, InfoItem
from textual_widgets.log_panel import LogMessage, LogPanel
from textual_widgets.search_history_dropdown import SearchInputWithHistory
from textual_widgets.settings_screen import BaseSettingsScreen
from textual_widgets.splitter import HorizontalSplitter, VerticalSplitter
from textual_widgets.url_input_screen import UrlInputScreen

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
    """Embedded DatePicker + button to open the modal version."""

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
                "Calendar-based date picker — embedded as a widget or used as a "
                "modal screen. Both deliver an ISO date (YYYY-MM-DD) to a callback.",
                classes="story-description",
            )
            yield Static(
                f"Last picked: {date.today().isoformat()}",
                id="dp-result",
                classes="story-result",
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
        with contextlib.suppress(Exception):
            self.query_one("#dp-result", Static).update(f"Last picked: {date_str}")


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
    """SearchInputWithHistory with sample entries."""

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
                "Search input with a permanent magnifying-glass icon and history "
                "dropdown. While typing, the dropdown filters by substring; matches "
                "are highlighted. Try 'lana', 'kraf' or 'amiga' — and Delete inside "
                "the dropdown removes an entry.",
                classes="story-description",
            )
            yield SearchInputWithHistory(
                icon="\U0001f50d",
                placeholder="Sample search ...",
                entries=self._entries,
                input_id="search-story-input",
                dropdown_id="search-story-dropdown",
                id="search-story-wrapper",
            )
            yield Static(
                "Last submit: —",
                id="search-result",
                classes="story-result",
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
            self.query_one("#search-result", Static).update(f"Last submit: {query}")
        except Exception:
            pass

    def on_search_input_with_history_history_entry_delete_requested(
        self,
        event: SearchInputWithHistory.HistoryEntryDeleteRequested,
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
    ContextMenuItem('rename', 'Rename', icon='~', shortcut='Ctrl+R'),
    ContextMenuItem.separator(),
    ContextMenuItem('delete', 'Delete', icon='x'),
]
self.app.push_screen(
    ContextMenuScreen(items, at=(event.screen_x, event.screen_y)),
    callback=self._on_action,
)
"""


class ContextMenuStory(Widget):
    """ContextMenuScreen triggered by right-click."""

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
                "Reusable context menu. Right-click into the area below to open the menu at the cursor position.",
                classes="story-description",
            )
            yield Static("RIGHT-CLICK HERE", id="cm-click-area")
            yield Static(
                "Last action: —",
                id="cm-result",
                classes="story-result",
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
        # Plain-text icons (no emoji presentation) so labels don't get coloured
        # tofu blocks on terminals that promote certain Unicode chars to emoji.
        items = [
            ContextMenuItem("open", "Open", icon="\U0001f4c2", shortcut="Enter"),
            ContextMenuItem("rename", "Rename", icon="~", shortcut="Ctrl+R"),
            ContextMenuItem.separator(),
            ContextMenuItem("delete", "Delete", icon="x", shortcut="Del"),
            ContextMenuItem.separator(),
            ContextMenuItem("info", "Properties", icon="?", shortcut="Alt+Enter"),
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
            label.update("Last action: cancelled (ESC / outside-click)")
        else:
            label.update(f"Last action: {action_id}")


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
    """VerticalSplitter + HorizontalSplitter in a live three-panel layout."""

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
                "Drag-resizable panels with a centered drag handle. Hover colours "
                "the splitter, drag changes the size of the target panel. After "
                "every drag a Resized message is posted (see below).",
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
                "Last resize: —",
                id="sp-result",
                classes="story-result",
            )
            yield Static(_SPLITTER_CODE, markup=False, classes="story-code")

    def on_vertical_splitter_resized(
        self,
        event: VerticalSplitter.Resized,
    ) -> None:
        self._show_resize(event.target_id, event.size, axis="width")

    def on_horizontal_splitter_resized(
        self,
        event: HorizontalSplitter.Resized,
    ) -> None:
        self._show_resize(event.target_id, event.size, axis="height")

    def _show_resize(self, target: str, size: int, axis: str) -> None:
        with contextlib.suppress(Exception):
            self.query_one("#sp-result", Static).update(f"Last resize: {target}.{axis} = {size} cells")


# ----------------------------------------------------------------------
# Hamburger Menu
# ----------------------------------------------------------------------


_HAMBURGER_CODE = """\
from textual_widgets import HamburgerMenu, HamburgerItem

class MyApp(App):
    def compose(self) -> ComposeResult:
        with Horizontal():
            yield HamburgerMenu(
                items=[
                    HamburgerItem('new', 'New mail', icon='✚'),
                    HamburgerItem.group('Accounts'),
                    HamburgerItem('inbox', 'Inbox', icon='▽'),
                    HamburgerItem('sent', 'Sent', icon='△'),
                ],
                bottom_items=[
                    HamburgerItem('settings', 'Settings', icon='⚙'),
                ],
            )
            yield Container(id='main')

    def on_hamburger_menu_item_selected(self, event):
        self.notify(f'Selected: {event.item_id}')
"""


class HamburgerStory(Widget):
    """HamburgerMenu in a 2-pane layout — sidebar + main content."""

    DEFAULT_CSS = """
    HamburgerStory {
        layout: vertical;
        height: 1fr;
    }
    HamburgerStory #hb-demo {
        layout: horizontal;
        height: 18;
        margin-bottom: 1;
        border: round $primary;
    }
    HamburgerStory #hb-content {
        width: 1fr;
        padding: 1 2;
        background: $surface-darken-1;
        content-align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Static("HamburgerMenu", classes="story-heading")
            yield Static(
                "Collapsible side menu in DevExpress style. Click the hamburger "
                "icon at the top to expand or collapse — width animates smoothly. "
                "Group headers visually separate sections; bottom items dock at "
                "the bottom (e.g. for Settings). When collapsed, items show only "
                "their icons; tooltips reveal labels on hover.",
                classes="story-description",
            )
            with Container(id="hb-demo"):
                yield HamburgerMenu(
                    items=[
                        # Alle Icons aus "Geometric Shapes" / einfachen
                        # Mathematical-Operators — gleiche Strichstaerke,
                        # 1 Zelle breit, keine Ambiguous-Width-Surprises.
                        HamburgerItem("new", "New mail", icon="✚"),
                        HamburgerItem.group("Accounts"),
                        HamburgerItem("inbox", "Inbox", icon="▽"),
                        HamburgerItem("sent", "Sent", icon="△"),
                        HamburgerItem("drafts", "Drafts", icon="◇"),
                        HamburgerItem.group("Folders"),
                        HamburgerItem("archive", "Archive", icon="□"),
                        HamburgerItem("trash", "Trash", icon="✕"),
                    ],
                    bottom_items=[
                        HamburgerItem("settings", "Settings", icon="⚙"),
                    ],
                    id="hb-menu",
                )
                yield Static("← Click an item", id="hb-content")
            yield Static(
                "Last selection: —",
                id="hb-result",
                classes="story-result",
            )
            yield Static(_HAMBURGER_CODE, markup=False, classes="story-code")

    def on_hamburger_menu_item_selected(
        self,
        event: HamburgerMenu.ItemSelected,
    ) -> None:
        try:
            self.query_one("#hb-result", Static).update(f"Last selection: {event.item_id}")
            self.query_one("#hb-content", Static).update(f"You selected:\n[bold]{event.item_id}[/bold]")
        except Exception:
            pass

    def on_hamburger_menu_toggled(
        self,
        event: HamburgerMenu.Toggled,
    ) -> None:
        state = "expanded" if event.expanded else "collapsed"
        with contextlib.suppress(Exception):
            self.query_one("#hb-result", Static).update(f"Menu {state}")


# ----------------------------------------------------------------------
# AboutScreen
# ----------------------------------------------------------------------


_ABOUT_CODE = """\
from textual_widgets import AboutScreen

from . import __author__, __version__, __year__

def action_show_about(self) -> None:
    self.push_screen(AboutScreen(
        app_name='my-tool',
        version=__version__,        # without leading 'v'
        author=__author__,
        release='2026',
        description='One-line summary.\\nSecond line.',
        lang='en',
        license='Apache 2.0',
        url='https://github.com/me/my-tool',
    ))
"""


class AboutStory(Widget):
    """Button that opens the standardized AboutScreen modal."""

    DEFAULT_CSS = """
    AboutStory {
        layout: vertical;
        height: 1fr;
    }
    AboutStory Button {
        height: 3;
        margin-bottom: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Static("AboutScreen", classes="story-heading")
            yield Static(
                "Standardized About dialog: headline bar, a meta line "
                "(version - author - release - license), description, a "
                "divider, a random quote from the bundled de/en pool, an "
                "optional clickable URL, and a close button. The width is "
                "computed from the longest content line. Close with ESC, "
                "the button, or a click outside.",
                classes="story-description",
            )
            yield Button("Open About dialog", id="about-open", variant="primary")
            yield Static(
                "Status: not opened yet",
                id="about-result",
                classes="story-result",
            )
            yield Static(_ABOUT_CODE, markup=False, classes="story-code")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "about-open":
            return
        self.app.push_screen(
            AboutScreen(
                app_name="textual-widgets",
                version=__version__,
                author=__author__,
                release="2026",
                description=(
                    "Reusable Textual widgets for terminal user interfaces.\nThis dialog is itself one of them."
                ),
                lang="en",
                license="Apache 2.0",
                url="https://github.com/michaelblaess/textual-widgets",
            ),
            callback=self._on_closed,
        )
        with contextlib.suppress(Exception):
            self.query_one("#about-result", Static).update("Status: dialog open")

    def _on_closed(self, _result: None) -> None:
        with contextlib.suppress(Exception):
            self.query_one("#about-result", Static).update("Status: dialog closed")


# ----------------------------------------------------------------------
# BaseSettingsScreen
# ----------------------------------------------------------------------


_SETTINGS_CODE = """\
from textual.widgets import Checkbox, TabPane
from textual_widgets import BaseSettingsScreen

class MySettingsScreen(BaseSettingsScreen):
    def app_tabs(self) -> ComposeResult:           # Hook 1: own tabs
        with TabPane('Display', id='tab-display'):
            yield Checkbox('Line numbers', id='set-lines')

    def collect_app_settings(self, settings):      # Hook 2: read values
        settings['line_numbers'] = self.query_one('#set-lines', Checkbox).value

self.push_screen(MySettingsScreen(current_settings, lang='en'),
                 callback=self._on_settings_closed)
"""


class _DemoSettingsScreen(BaseSettingsScreen):
    """Concrete BaseSettingsScreen subclass for the storybook."""

    def app_tabs(self) -> ComposeResult:
        with TabPane("Display", id="settings-tab-display"):
            with Horizontal(classes="settings-row"):
                yield Label("Theme variant:")
                yield Select[str](
                    [("Dark", "dark"), ("Light", "light")],
                    value=str(self._settings.get("variant", "dark")),
                    allow_blank=False,
                    id="demo-variant",
                )
            yield Checkbox(
                "Show line numbers",
                value=bool(self._settings.get("line_numbers", True)),
                id="demo-linenumbers",
            )
            yield Static(
                "The Language tab above ships with BaseSettingsScreen — "
                "this Display tab comes from the app_tabs() hook.",
                classes="settings-hint",
            )

    def collect_app_settings(self, settings: dict[str, object]) -> None:
        variant = self.query_one("#demo-variant", Select).value
        if isinstance(variant, str):
            settings["variant"] = variant
        settings["line_numbers"] = self.query_one("#demo-linenumbers", Checkbox).value


class SettingsStory(Widget):
    """Button that opens a BaseSettingsScreen subclass."""

    DEFAULT_CSS = """
    SettingsStory {
        layout: vertical;
        height: 1fr;
    }
    SettingsStory Button {
        height: 3;
        margin-bottom: 1;
    }
    """

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        # Persisted between openings — mimics the app's settings store.
        self._settings: dict[str, object] = {
            "language": "en",
            "variant": "dark",
            "line_numbers": True,
        }

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Static("BaseSettingsScreen", classes="story-heading")
            yield Static(
                "Base class for app settings dialogs. It ships a Language "
                "tab, Save/Cancel buttons and Esc/Ctrl+S bindings; the app "
                "subclasses it and overrides two hooks — app_tabs() for its "
                "own TabPanes and collect_app_settings() to harvest the "
                "values. Returns the changed settings dict, or None on cancel.",
                classes="story-description",
            )
            yield Button("Open Settings dialog", id="settings-open", variant="primary")
            yield Static(
                "Current settings: language=en, variant=dark, line_numbers=True",
                id="settings-result",
                classes="story-result",
            )
            yield Static(_SETTINGS_CODE, markup=False, classes="story-code")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "settings-open":
            return
        lang = str(self._settings.get("language", "en"))
        self.app.push_screen(
            _DemoSettingsScreen(self._settings, lang=lang),
            callback=self._on_settings_closed,
        )

    def _on_settings_closed(self, result: dict[str, object] | None) -> None:
        if result is None:
            self._update_result("cancelled — settings unchanged")
            return
        self._settings = result
        summary = ", ".join(f"{k}={v}" for k, v in result.items())
        self._update_result(f"saved — {summary}")

    def _update_result(self, text: str) -> None:
        with contextlib.suppress(Exception):
            self.query_one("#settings-result", Static).update(f"Current settings: {text}")


# ----------------------------------------------------------------------
# LogPanel
# ----------------------------------------------------------------------


_LOGPANEL_CODE = """\
from textual_widgets import LogMessage, LogPanel, LogRouter

class MyApp(LogRouter, App):          # LogRouter BEFORE App
    def compose(self) -> ComposeResult:
        yield LogPanel(lang='en', export_name='my-tool', id='log')

# Any widget, anywhere — does NOT know the LogPanel:
self.post_message(LogMessage.success('File saved'))

# LogMessage bubbles up to the App, where LogRouter routes it
# into the first LogPanel in the DOM.
"""


class LogPanelStory(Widget):
    """Embedded LogPanel + buttons posting LogMessages at each level."""

    DEFAULT_CSS = """
    LogPanelStory {
        layout: vertical;
        height: 1fr;
    }
    LogPanelStory .log-buttons {
        layout: grid;
        grid-size: 3;
        grid-gutter: 1;
        grid-rows: 3;
        height: auto;
        margin-bottom: 1;
    }
    LogPanelStory .log-buttons Button {
        width: 1fr;
        height: 3;
    }
    LogPanelStory LogPanel {
        height: 12;
        margin-bottom: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Static("LogPanel / LogMessage / LogRouter", classes="story-heading")
            yield Static(
                "Decoupled logging. The buttons post a LogMessage; it bubbles "
                "up to the app, the LogRouter mixin routes it into the LogPanel "
                "below. The panel adds a timestamp and level colour, keeps a "
                "plain-text mirror for copy/export, and offers a right-click "
                "context menu (copy / export / hide). Try right-clicking it.",
                classes="story-description",
            )
            with Horizontal(classes="log-buttons"):
                yield Button("info", id="log-info")
                yield Button("success", id="log-success", variant="success")
                yield Button("warning", id="log-warning", variant="warning")
                yield Button("error", id="log-error", variant="error")
                yield Button("debug", id="log-debug")
                yield Button("clear", id="log-clear")
            yield LogPanel(lang="en", export_name="storybook", id="story-log-panel")
            yield Static(_LOGPANEL_CODE, markup=False, classes="story-code")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""
        if not button_id.startswith("log-"):
            return
        level = button_id.removeprefix("log-")
        if level == "clear":
            with contextlib.suppress(Exception):
                self.query_one("#story-log-panel", LogPanel).clear_log()
            return
        self.post_message(LogMessage(f"This is a {level}-level message.", level))


# ----------------------------------------------------------------------
# CrashGuard / ErrorScreen
# ----------------------------------------------------------------------


_CRASHGUARD_CODE = """\
from textual_widgets import CrashGuard

class MyApp(CrashGuard, App):         # CrashGuard BEFORE App
    def __init__(self) -> None:
        super().__init__()
        self.crash_guard_lang = 'en'  # 'de' | 'en'

# An unhandled exception in a handler, timer or worker now
# shows the ErrorScreen (copyable traceback + Continue / Quit)
# instead of crashing the whole app.
"""


class CrashGuardStory(Widget):
    """Demonstrates the CrashGuard mixin and the ErrorScreen dialog."""

    DEFAULT_CSS = """
    CrashGuardStory {
        layout: vertical;
        height: 1fr;
    }
    CrashGuardStory Button {
        height: 3;
        margin-bottom: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Static("CrashGuard / ErrorScreen", classes="story-heading")
            yield Static(
                "The CrashGuard mixin catches unhandled exceptions instead of "
                "letting Textual tear the app down. It shows the ErrorScreen: "
                "an apology, the error line, a scrollable copyable traceback "
                "and Copy / Continue / Quit buttons. 'Raise an exception' "
                "triggers a real crash caught by the guard; 'Show ErrorScreen' "
                "opens the dialog directly with a sample traceback.",
                classes="story-description",
            )
            yield Button("Raise an exception (caught by CrashGuard)", id="cg-raise", variant="error")
            yield Button("Show ErrorScreen directly", id="cg-show", variant="primary")
            yield Static(_CRASHGUARD_CODE, markup=False, classes="story-code")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cg-raise":
            raise RuntimeError("Demo exception raised from the storybook button handler.")
        if event.button.id == "cg-show":
            try:
                _ = 1 / 0
            except ZeroDivisionError as exc:
                report = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
                self.app.push_screen(ErrorScreen(exc, report, lang="en"))


# ----------------------------------------------------------------------
# UrlInputScreen
# ----------------------------------------------------------------------


_URLINPUT_CODE = """\
from textual_widgets import UrlInputScreen

def action_enter_url(self) -> None:
    self.push_screen(
        UrlInputScreen(lang='en'),
        callback=self._on_url_entered,
    )

def _on_url_entered(self, url: str | None) -> None:
    if url is None:
        return                  # cancelled
    self.start_url = url        # 'https://...' guaranteed
"""


class UrlInputStory(Widget):
    """Button that opens the UrlInputScreen modal."""

    DEFAULT_CSS = """
    UrlInputStory {
        layout: vertical;
        height: 1fr;
    }
    UrlInputStory Button {
        height: 3;
        margin-bottom: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Static("UrlInputScreen", classes="story-heading")
            yield Static(
                "Modal dialog asking for an http/https URL. Input without a "
                "scheme gets 'https://' prepended; invalid input shows an "
                "inline error and keeps the dialog open. Enter or OK submit, "
                "ESC or Cancel return None.",
                classes="story-description",
            )
            yield Button("Open URL dialog", id="url-open", variant="primary")
            yield Static(
                "Status: not opened yet",
                id="url-result",
                classes="story-result",
            )
            yield Static(_URLINPUT_CODE, markup=False, classes="story-code")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "url-open":
            return
        self.app.push_screen(UrlInputScreen(lang="en"), callback=self._on_url)

    def _on_url(self, url: str | None) -> None:
        text = "cancelled" if url is None else url
        with contextlib.suppress(Exception):
            self.query_one("#url-result", Static).update(f"Status: {text}")


# ----------------------------------------------------------------------
# InfoHeader
# ----------------------------------------------------------------------


_INFOHEADER_CODE = """\
from textual_widgets import InfoHeader, InfoItem, InfoAction

yield InfoHeader(
    [
        InfoItem('host', 'Host', 'example.com'),
        InfoItem('ok', '2xx', '128', value_style='bold green'),
        InfoItem('err', '4xx', '3', value_style='bold red'),
        InfoItem('period', 'Period', 'May 2026', navigable=True),
    ],
    columns=2,
    title='Crawl',
    actions=[InfoAction('open', 'Open report')],
    collapsible=True,
)

# runtime: header.set_value('ok', '200', value_style='bold green')
"""


class InfoHeaderStory(Widget):
    """InfoHeader demo: coloured values, a navigable item, an action, collapse."""

    DEFAULT_CSS = """
    InfoHeaderStory {
        layout: vertical;
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Static("InfoHeader", classes="story-heading")
            yield Static(
                "Bordered header panel showing label/value pairs in an "
                "N-column grid. Values can be coloured and right-aligned, "
                "items can be navigable (< value >), actions post a message, "
                "and the whole header can collapse. Click the title to "
                "collapse it.",
                classes="story-description",
            )
            yield InfoHeader(
                [
                    InfoItem("host", "Host", "example.com"),
                    InfoItem("depth", "Max depth", "3"),
                    InfoItem("ok", "2xx", "128", value_style="bold green", value_align="right"),
                    InfoItem("err", "4xx", "3", value_style="bold red", value_align="right"),
                    InfoItem("period", "Period", "May 2026", navigable=True),
                    InfoItem("dur", "Duration", "15s", value_align="right"),
                ],
                columns=2,
                title="Crawl",
                actions=[InfoAction("open", "Open report")],
                collapsible=True,
            )
            yield Static("Status: idle", id="ih-result", classes="story-result")
            yield Static(_INFOHEADER_CODE, markup=False, classes="story-code")

    def on_info_header_action_pressed(self, event: InfoHeader.ActionPressed) -> None:
        self._show(f"action '{event.key}'")

    def on_info_header_navigated(self, event: InfoHeader.Navigated) -> None:
        self._show(f"navigated '{event.key}' {event.direction}")

    def _show(self, text: str) -> None:
        with contextlib.suppress(Exception):
            self.query_one("#ih-result", Static).update(f"Status: {text}")
