"""StorybookApp — interaktive Showcase fuer alle textual-widgets-Widgets.

Layout:
- Header: App-Titel
- TabbedContent: ein Tab pro Widget mit Live-Demo + Code-Snippet
- Footer: Key-Bindings + Theme-Switch-Hinweis

Theme-Integration: Wenn das optionale `textual-themes`-Paket installiert
ist, werden alle Retro-Themes registriert (Ctrl+P → "theme" zum Wechseln).
Sonst nur die Textual-eingebauten Themes (textual-dark / textual-light).
"""
from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header, TabbedContent, TabPane

from textual_widgets.storybook.stories import (
    ContextMenuStory,
    DatePickerStory,
    SearchStory,
    SplitterStory,
)


class StorybookApp(App):
    """Showcase-App fuer alle Widgets der Library."""

    TITLE = "textual-widgets — Storybook"
    SUB_TITLE = "Live-Demos + Code-Snippets"

    CSS = """
    Screen {
        layout: vertical;
    }
    TabbedContent {
        height: 1fr;
    }
    .story-section {
        padding: 1 2;
        height: auto;
    }
    .story-heading {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    .story-description {
        color: $text-muted;
        margin-bottom: 1;
    }
    .story-code {
        background: $surface-darken-1;
        color: $text;
        padding: 1 2;
        border: round $surface-lighten-1;
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        # Optional: textual-themes registrieren (falls installiert).
        # Mit `pip install "textual-widgets[storybook]"` automatisch dabei.
        try:
            from textual_themes import register_all
            register_all(self)
        except ImportError:
            pass

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(initial="tab-datepicker"):
            with TabPane("DatePicker", id="tab-datepicker"):
                yield DatePickerStory()
            with TabPane("Search", id="tab-search"):
                yield SearchStory()
            with TabPane("ContextMenu", id="tab-contextmenu"):
                yield ContextMenuStory()
            with TabPane("Splitter", id="tab-splitter"):
                yield SplitterStory()
        yield Footer()
