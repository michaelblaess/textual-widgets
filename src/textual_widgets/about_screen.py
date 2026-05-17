"""Standardisierter About-Dialog fuer Textual-Apps.

Public API:
    - `Quote` — Dataclass fuer ein Zitat (text, author).
    - `load_quotes(lang)` — laedt den mitgelieferten Zitatpool (de/en).
    - `AboutScreen` — ModalScreen mit einheitlichem Aufbau:

        Headline
        version - Autor - Release-Datum
        Beschreibung
        --- (Trenner, passt sich automatisch der Dialogbreite an)
        Zitat
        URL (optional, anklickbar)
        ESC = Close

Usage:
    from textual_widgets import AboutScreen

    def action_show_about(self) -> None:
        self.push_screen(AboutScreen(
            app_name="my-tool",
            version=__version__,
            author=__author__,
            release=__year__,
            description="Beschreibung.\\nZweite Zeile.",
            lang="de",
        ))

Das Zitat wird bei jedem Oeffnen zufaellig aus dem Pool gewaehlt. Apps koennen
mit `quote=` ein festes Zitat oder mit `quotes=` eine eigene Liste vorgeben.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from importlib import resources

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.events import Click
from textual.screen import ModalScreen
from textual.widgets import Rule, Static

# Default-Footer pro Sprache. Andere Sprachen fallen auf Englisch zurueck.
_FOOTER_TEXT = {
    "de": "ESC = Schliessen",
    "en": "ESC = Close",
}

# Breiten-Schranken des Dialogs (Inhaltsbreite + Border + Padding).
_MIN_WIDTH = 44
_MAX_WIDTH = 92


@dataclass(frozen=True)
class Quote:
    """Ein Zitat mit Urheber.

    Attributes:
        text:
            Der Zitattext. Darf Zeilenumbrueche enthalten.
        author:
            Name des Urhebers (z.B. "Emily Dickinson").
    """

    text: str
    author: str


def load_quotes(lang: str = "en") -> list[Quote]:
    """Laedt den mitgelieferten Zitatpool fuer eine Sprache.

    Args:
        lang:
            Sprachkuerzel ('de' oder 'en'). Bei unbekannter Sprache wird
            der englische Pool zurueckgegeben.

    Returns:
        Liste der Zitate. Leer, wenn die quotes.json fehlt oder unlesbar ist.
    """
    try:
        raw = (resources.files("textual_widgets") / "quotes" / "quotes.json").read_text(encoding="utf-8")
        data = json.loads(raw)
    except Exception:
        return []

    pool = data.get(lang) or data.get("en") or []
    return [
        Quote(text=str(entry["text"]), author=str(entry["author"]))
        for entry in pool
        if "text" in entry and "author" in entry
    ]


class AboutScreen(ModalScreen[None]):
    """Standardisierter About-Dialog als ModalScreen.

    Schliessen ueber ESC oder Klick ausserhalb des Dialogs. Die Dialogbreite
    wird beim Mount aus der laengsten Inhaltszeile berechnet, sodass der
    Trenner exakt buendig sitzt und kein Whitespace entsteht.
    """

    DEFAULT_CSS = """
    AboutScreen {
        align: center middle;
    }

    AboutScreen > VerticalScroll {
        height: auto;
        max-height: 90%;
        background: $surface;
        border: thick $accent;
        padding: 1 2;
    }

    AboutScreen #about-title {
        width: 1fr;
        height: 3;
        content-align: center middle;
        text-style: bold;
        background: $accent;
        color: auto;
        margin-bottom: 1;
    }

    AboutScreen #about-meta {
        width: 1fr;
        margin-bottom: 1;
    }

    AboutScreen #about-description {
        width: 1fr;
    }

    /* Rule fuellt mit width: 1fr exakt die (explizit gesetzte) Dialogbreite */
    AboutScreen Rule {
        width: 1fr;
        color: $text-muted;
        margin: 1 0;
    }

    AboutScreen #about-quote {
        width: 1fr;
    }

    AboutScreen #about-url {
        width: 1fr;
        content-align: center middle;
        color: $accent;
        margin-top: 1;
    }

    AboutScreen #about-footer {
        width: 1fr;
        content-align: center middle;
        color: $text-muted;
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "close", "ESC"),
    ]

    def __init__(
        self,
        *,
        app_name: str,
        version: str,
        author: str,
        release: str,
        description: str,
        lang: str = "en",
        quote: Quote | None = None,
        quotes: list[Quote] | None = None,
        url: str | None = None,
        footer: str | None = None,
    ) -> None:
        """Erstellt den About-Dialog.

        Args:
            app_name:
                Name der Anwendung (Headline-Balken).
            version:
                Versionsnummer ohne fuehrendes 'v' (z.B. "1.2.0"). Der Dialog
                stellt das 'v' selbst voran.
            author:
                Name des Autors.
            release:
                Release-Datum oder -Jahr (z.B. "2026").
            description:
                Beschreibungstext. Darf Zeilenumbrueche enthalten.
            lang:
                Sprachkuerzel ('de' oder 'en') fuer Footer und Zitatpool.
            quote:
                Optionales festes Zitat. Wenn gesetzt, wird kein zufaelliges
                Zitat aus dem Pool gewaehlt.
            quotes:
                Optionale eigene Zitatliste. Wird statt des mitgelieferten
                Pools verwendet (zufaellige Auswahl).
            url:
                Optionale Projekt-/Repo-URL. Wird unter dem Zitat als
                anklickbarer Link angezeigt (CTRL+Klick oeffnet im Browser).
            footer:
                Optionaler Footer-Text. Default ist das sprachabhaengige
                "ESC = Schliessen" / "ESC = Close".
        """
        super().__init__()
        self._app_name = app_name
        self._version = version.lstrip("v")
        self._author = author
        self._release = release
        self._description = description.rstrip("\n")
        self._url = url
        self._lang = lang if lang in _FOOTER_TEXT else "en"
        self._footer = footer if footer is not None else _FOOTER_TEXT[self._lang]

        # Zitat bestimmen: explizit > eigene Liste > mitgelieferter Pool
        if quote is not None:
            self._quote: Quote | None = quote
        else:
            pool = quotes if quotes else load_quotes(self._lang)
            self._quote = random.choice(pool) if pool else None

    def compose(self) -> ComposeResult:
        """Erstellt das Modal-Layout."""
        with VerticalScroll(id="about-dialog"):
            yield Static(self._app_name, id="about-title")
            yield Static(self._build_meta(), id="about-meta")
            yield Static(self._description, id="about-description")
            if self._quote is not None:
                yield Rule(line_style="solid")
                yield Static(self._build_quote(self._quote), id="about-quote")
            if self._url:
                yield Static(self._build_url(self._url), id="about-url")
            yield Static(self._footer, id="about-footer")

    def on_mount(self) -> None:
        """Setzt die Dialogbreite anhand der laengsten Inhaltszeile.

        Ohne explizite Breite blaeht ein `width: 1fr`-Kind (Rule) den
        `width: auto`-Container bis zur Bildschirmbreite auf.
        """
        self.query_one("#about-dialog").styles.width = self._dialog_width()

    def _build_meta(self) -> Text:
        """Baut die Meta-Zeile 'version - Autor - Release'."""
        text = Text()
        text.append(f"v{self._version}", style="bold")
        text.append("   ·   ", style="dim")
        text.append(self._author, style="bold")
        text.append("   ·   ", style="dim")
        text.append(self._release, style="bold")
        return text

    @staticmethod
    def _build_quote(quote: Quote) -> Text:
        """Baut das Zitat samt Urheber als Rich Text."""
        text = Text()
        text.append(quote.text, style="italic")
        text.append("\n\n")
        text.append(f"- {quote.author}", style="bold")
        return text

    @staticmethod
    def _build_url(url: str) -> Text:
        """Baut die URL als anklickbaren Link (OSC-8, CTRL+Klick)."""
        return Text(url, style=f"underline link {url}")

    def _dialog_width(self) -> int:
        """Berechnet die Dialogbreite aus der laengsten Inhaltszeile."""
        lines: list[str] = [self._app_name, self._build_meta().plain]
        lines += self._description.split("\n")
        if self._quote is not None:
            lines += self._quote.text.split("\n")
            lines.append(f"- {self._quote.author}")
        if self._url:
            lines.append(self._url)
        lines.append(self._footer)

        content = max((len(line) for line in lines), default=0)
        # + 2 Border (thick) + 4 Container-Padding (padding: 1 2)
        return max(_MIN_WIDTH, min(_MAX_WIDTH, content + 6))

    def on_click(self, event: Click) -> None:
        """Klick ausserhalb des Dialogs schliesst ihn."""
        widget, _ = self.get_widget_at(event.screen_x, event.screen_y)
        if widget is self:
            self.dismiss(None)

    def action_close(self) -> None:
        """Schliesst den Dialog."""
        self.dismiss(None)
