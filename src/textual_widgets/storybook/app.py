"""StorybookApp — interaktive Showcase fuer alle textual-widgets-Widgets.

Layout (orientiert an textual-themes/demo.py):
- Header: App-Titel + aktuelles Widget als Sub-Title
- Horizontal main:
  - Linke Sidebar: Tree mit allen Widget-Stories (Auswahl wechselt rechts)
  - Rechte Content-Area: ContentSwitcher mit der aktiven Story
- Footer: Bindings (n/p cycle, Ctrl+S screenshot, q quit)

Theme-Integration: Wenn das optionale `textual-themes`-Paket installiert
ist, werden alle Retro-Themes registriert — Theme-Wechsel ueber Ctrl+P
(Textual Command-Palette) oder per Theme-Picker.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.widget import Widget
from textual.widgets import ContentSwitcher, Footer, Header, Tree

from textual_widgets.crash_guard import CrashGuard
from textual_widgets.log_panel import LogRouter
from textual_widgets.storybook.stories import (
    AboutStory,
    ContextMenuStory,
    CrashGuardStory,
    DatePickerStory,
    HamburgerStory,
    LogPanelStory,
    SearchStory,
    SettingsStory,
    SplitterStory,
)

# Einzige Quelle der Wahrheit: speist sowohl den Sidebar-Tree als auch den
# ContentSwitcher. So koennen Tree-Leafs und Switcher-Kinder nicht mehr
# auseinanderdriften (sonst: NoMatches beim Story-Wechsel).
# Reihenfolge = Reihenfolge in der Sidebar = Reihenfolge fuer n/p-Cycle.
_STORIES: list[tuple[str, str, type[Widget]]] = [
    # (id, label, story-Klasse)
    ("story-datepicker", "DatePicker", DatePickerStory),
    ("story-search", "Search", SearchStory),
    ("story-contextmenu", "ContextMenu", ContextMenuStory),
    ("story-splitter", "Splitter", SplitterStory),
    ("story-hamburger", "HamburgerMenu", HamburgerStory),
    ("story-about", "AboutScreen", AboutStory),
    ("story-settings", "BaseSettingsScreen", SettingsStory),
    ("story-logpanel", "LogPanel", LogPanelStory),
    ("story-crashguard", "CrashGuard", CrashGuardStory),
]


class StorybookApp(CrashGuard, LogRouter, App[None]):
    """Showcase-App fuer alle Widgets der Library.

    Erbt `CrashGuard` und `LogRouter`: damit funktionieren die CrashGuard-
    und LogPanel-Stories als echte End-to-End-Demos — eine geworfene
    Exception landet im `ErrorScreen`, ein `LogMessage` im `LogPanel`.
    """

    TITLE = "textual-widgets — Storybook"

    CSS = """
    Screen {
        layout: vertical;
    }
    #main {
        height: 1fr;
        layout: horizontal;
    }
    #sidebar {
        width: 28;
        min-width: 20;
        background: $panel;
        border-right: solid $accent;
    }
    #widget-tree {
        height: 1fr;
        padding: 1;
    }
    #content {
        width: 1fr;
        padding: 1 2;
    }
    .story-heading {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    .story-description {
        color: $text-muted;
        margin-bottom: 1;
        height: auto;
    }
    .story-section {
        background: $boost;
        color: $foreground;
        text-style: bold;
        padding: 0 1;
        margin-top: 1;
        margin-bottom: 1;
    }
    .story-code {
        background: $surface-darken-1;
        color: $text;
        padding: 1 2;
        border: round $surface-lighten-1;
        margin-top: 1;
        height: auto;
    }
    .story-result {
        background: $surface-darken-1;
        color: $accent;
        padding: 0 2;
        border: round $accent;
        margin-bottom: 1;
        height: auto;
    }
    """

    BINDINGS = [
        Binding("n,N", "next_story", "Next", key_display="n"),
        Binding("p,P", "prev_story", "Prev", key_display="p"),
        Binding("t,T", "cycle_theme", "Theme", key_display="t"),
        Binding("ctrl+s", "screenshot", "Screenshot"),
        Binding("q,Q", "quit", "Quit", key_display="q"),
    ]

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.crash_guard_lang = "en"
        # Optional: textual-themes registrieren (mit `[storybook]`-Extra dabei)
        try:
            from textual_themes import register_all

            register_all(self)
        except ImportError:
            pass

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Horizontal(id="main"):
            with VerticalScroll(id="sidebar"):
                yield self._build_sidebar()
            with ContentSwitcher(initial=_STORIES[0][0], id="content"):
                for story_id, _label, story_cls in _STORIES:
                    yield story_cls(id=story_id)
        yield Footer()

    def _build_sidebar(self) -> Tree[str]:
        """Tree mit allen Stories in der linken Sidebar."""
        tree: Tree[str] = Tree("Widgets", id="widget-tree")
        tree.show_root = False
        tree.guide_depth = 2
        for story_id, label, _cls in _STORIES:
            tree.root.add_leaf(label, data=story_id)
        tree.root.expand()
        return tree

    def on_mount(self) -> None:
        self._update_subtitle()
        # Ersten Eintrag in der Sidebar markieren
        try:
            tree = self.query_one("#widget-tree", Tree)
            if tree.root.children:
                tree.select_node(tree.root.children[0])
        except Exception:
            pass

    def on_tree_node_selected(self, event: Tree.NodeSelected[str]) -> None:
        """Sidebar-Auswahl wechselt die aktive Story."""
        if event.control.id != "widget-tree":
            return
        story_id = event.node.data
        # Defensiv: nur zu Stories wechseln, die in _STORIES registriert sind.
        # Mit der Single-Source koennen Tree und Switcher nicht mehr driften —
        # der Guard faengt kuenftige Fehlbedienung trotzdem ab (sonst NoMatches).
        if not story_id or story_id not in {sid for sid, _, _ in _STORIES}:
            return
        switcher = self.query_one("#content", ContentSwitcher)
        switcher.current = story_id
        self._update_subtitle()

    def action_next_story(self) -> None:
        self._cycle_story(+1)

    def action_prev_story(self) -> None:
        self._cycle_story(-1)

    def _cycle_story(self, step: int) -> None:
        ids = [sid for sid, _, _ in _STORIES]
        switcher = self.query_one("#content", ContentSwitcher)
        current = switcher.current or ids[0]
        try:
            idx = ids.index(current)
        except ValueError:
            idx = 0
        next_id = ids[(idx + step) % len(ids)]
        switcher.current = next_id
        # Auch die Sidebar-Markierung mitziehen
        try:
            tree = self.query_one("#widget-tree", Tree)
            for leaf in tree.root.children:
                if leaf.data == next_id:
                    tree.select_node(leaf)
                    break
        except Exception:
            pass
        self._update_subtitle()

    def _update_subtitle(self) -> None:
        """Setzt den Sub-Title im Header auf den Namen der aktiven Story."""
        try:
            switcher = self.query_one("#content", ContentSwitcher)
        except Exception:
            return
        current = switcher.current
        for story_id, label, _cls in _STORIES:
            if story_id == current:
                self.sub_title = label
                return
        self.sub_title = ""

    def action_screenshot(self) -> None:
        """Save an SVG screenshot of the current view."""
        story_slug = (self.sub_title or "screenshot").lower().replace(" ", "-")
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"storybook-{story_slug}-{timestamp}.svg"
        self.save_screenshot(str(Path.cwd() / filename))
        self.notify(f"Saved {filename}", title="Screenshot")

    def action_cycle_theme(self) -> None:
        """Cycle to the next registered theme. Falls back to Textual built-ins
        if `textual-themes` is not installed."""
        # `App.themes` is the public dict of registered themes (Textual >= 0.85).
        # Fall back to the private attribute for older versions.
        themes = getattr(self, "themes", None) or getattr(self, "_registered_themes", {})
        names = sorted(themes.keys())
        if not names:
            return
        try:
            idx = names.index(self.theme)
        except ValueError:
            idx = -1
        next_theme = names[(idx + 1) % len(names)]
        self.theme = next_theme
        self.notify(f"Theme: {next_theme}")
