"""Standardisiertes Log-Panel mit entkoppeltem Logging-Event.

Public API:
    - `LogMessage` — Message-Klasse zum Loggen ohne direkte Widget-Referenz.
      Komfort-Konstruktoren: `LogMessage.info/.success/.warning/.error/.debug`.
    - `LogPanel` — RichLog-basiertes Panel mit Zeitstempel, Level-Farben,
      Plain-Text-Spiegel und eingebautem Rechtsklick-Kontextmenue
      (Kopieren / Exportieren / Ausblenden).
    - `LogRouter` — Mixin fuer `App`. Faengt `LogMessage` ab und schreibt sie
      ins erste `LogPanel` im DOM.

Usage:
    from textual.app import App
    from textual_widgets import LogMessage, LogPanel, LogRouter

    class MyApp(LogRouter, App):
        def compose(self) -> ComposeResult:
            yield LogPanel(lang="de", export_name="my-tool", id="log")

    # Irgendein Widget, irgendwo — kennt das LogPanel NICHT:
    self.post_message(LogMessage.success("Datei gespeichert"))

Textual-Messages bubbeln nach OBEN (Kind -> Eltern -> App), nicht nach unten zu
einem Geschwister-Widget. Ein `LogMessage` landet daher bei der App; der
`LogRouter`-Mixin leitet es von dort ans `LogPanel` weiter. Das ist die einzige
Stelle, die das Panel kennt — und sie lebt in der App (Composition Root).
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from rich.text import Text
from textual.events import Click
from textual.message import Message
from textual.widgets import RichLog

from textual_widgets.context_menu import ContextMenuItem, ContextMenuScreen

if TYPE_CHECKING:
    from textual.app import App

    # Unter mypy ist die Basis App[object] — damit `query`/`on_log_message`
    # typgeprueft werden. Zur Laufzeit ist die Basis `object`; `super()` und
    # `self.query` folgen der echten MRO der konkreten App-Klasse.
    _LogRouterBase = App[object]
else:
    _LogRouterBase = object

# Gueltige Log-Level. Unbekannte Level fallen auf "info" zurueck.
_LEVELS = ("info", "success", "warning", "error", "debug")

# Rich-Style pro Level. "info" bleibt ungestylt (Theme-Standardfarbe).
_LEVEL_STYLE = {
    "info": "",
    "success": "green",
    "warning": "yellow",
    "error": "bold red",
    "debug": "dim",
}

# Kontextmenue- und Notify-Texte pro Sprache.
_PANEL_TEXT: dict[str, dict[str, str]] = {
    "de": {
        "copy": "Log kopieren",
        "export": "Log exportieren",
        "hide": "Log ausblenden",
        "copied": "Log in die Zwischenablage kopiert",
        "empty": "Log ist leer",
        "exported": "Log gespeichert: {path}",
        "export_error": "Log-Export fehlgeschlagen: {error}",
    },
    "en": {
        "copy": "Copy log",
        "export": "Export log",
        "hide": "Hide log",
        "copied": "Log copied to clipboard",
        "empty": "Log is empty",
        "exported": "Log saved: {path}",
        "export_error": "Log export failed: {error}",
    },
}


class LogMessage(Message):
    """Eine Log-Nachricht. Bubbelt zur App, wird vom `LogRouter` weitergeleitet.

    Attributes:
        text:
            Der Nachrichtentext (darf Rich-Markup enthalten).
        level:
            Log-Level: 'info', 'success', 'warning', 'error' oder 'debug'.
    """

    def __init__(self, text: str, level: str = "info") -> None:
        """Erstellt eine Log-Nachricht.

        Args:
            text:
                Der Nachrichtentext.
            level:
                Log-Level. Unbekannte Werte fallen auf 'info' zurueck.
        """
        super().__init__()
        self.text = text
        self.level = level if level in _LEVELS else "info"

    @classmethod
    def info(cls, text: str) -> LogMessage:
        """Erstellt eine Nachricht mit Level 'info'."""
        return cls(text, "info")

    @classmethod
    def success(cls, text: str) -> LogMessage:
        """Erstellt eine Nachricht mit Level 'success'."""
        return cls(text, "success")

    @classmethod
    def warning(cls, text: str) -> LogMessage:
        """Erstellt eine Nachricht mit Level 'warning'."""
        return cls(text, "warning")

    @classmethod
    def error(cls, text: str) -> LogMessage:
        """Erstellt eine Nachricht mit Level 'error'."""
        return cls(text, "error")

    @classmethod
    def debug(cls, text: str) -> LogMessage:
        """Erstellt eine Nachricht mit Level 'debug'."""
        return cls(text, "debug")


class LogPanel(RichLog):
    """RichLog-basiertes Log-Panel mit Kontextmenue und Plain-Text-Spiegel.

    Schreibt Zeilen mit Zeitstempel und Level-Farbe. Rechtsklick oeffnet ein
    Kontextmenue mit Kopieren / Exportieren / Ausblenden. Fuer Copy/Export
    wird ein paralleler Plain-Text-Spiegel gefuehrt (RichLog selbst speichert
    nur gerenderte Strips).
    """

    DEFAULT_CSS = """
    LogPanel {
        height: 10;
        min-height: 3;
        background: $surface;
        border-top: solid $accent;
        padding: 0 1;
    }

    LogPanel.-log-hidden {
        display: none;
    }
    """

    class Hidden(Message):
        """Wird gepostet, wenn das Panel per Kontextmenue ausgeblendet wird.

        Apps mit einem Splitter ueber dem Log koennen darauf reagieren und
        den Splitter mit ausblenden.
        """

    def __init__(
        self,
        *,
        lang: str = "en",
        export_name: str = "app",
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Erstellt das Log-Panel.

        Args:
            lang:
                Sprachkuerzel ('de' oder 'en') fuer Kontextmenue und Hinweise.
            export_name:
                Dateinamen-Praefix fuer den Log-Export (z.B. 'my-tool' ->
                'my-tool-log-JJJJMMTT-HHMMSS.txt' im Home-Verzeichnis).
            id:
                Optionale Widget-ID.
            classes:
                Optionale CSS-Klassen.
        """
        super().__init__(markup=True, highlight=True, id=id, classes=classes)
        self._lang = lang if lang in _PANEL_TEXT else "en"
        self._export_name = export_name
        self._lines: list[str] = []

    def write_log(self, text: str, level: str = "info") -> None:
        """Schreibt eine Zeile mit Zeitstempel und Level-Farbe ins Panel.

        Args:
            text:
                Der Nachrichtentext (darf Rich-Markup enthalten).
            level:
                Log-Level. Unbekannte Werte werden wie 'info' behandelt.
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        plain = Text.from_markup(text).plain
        self._lines.append(f"{timestamp} {plain}")

        style = _LEVEL_STYLE.get(level, "")
        if style:
            self.write(f"[dim]{timestamp}[/dim] [{style}]{text}[/{style}]")
        else:
            self.write(f"[dim]{timestamp}[/dim] {text}")

    def clear_log(self) -> None:
        """Leert Panel und Plain-Text-Spiegel."""
        self._lines.clear()
        self.clear()

    def copy_log(self) -> None:
        """Kopiert den gesamten Log-Inhalt in die Zwischenablage."""
        if not self._lines:
            self.app.notify(self._t("empty"), severity="warning")
            return
        self.app.copy_to_clipboard("\n".join(self._lines))
        self.app.notify(self._t("copied"))

    def export_log(self) -> None:
        """Speichert den Log-Inhalt als Textdatei im Home-Verzeichnis."""
        if not self._lines:
            self.app.notify(self._t("empty"), severity="warning")
            return
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        out_path = Path.home() / f"{self._export_name}-log-{stamp}.txt"
        try:
            out_path.write_text("\n".join(self._lines) + "\n", encoding="utf-8")
        except OSError as exc:
            self.app.notify(self._t("export_error", error=str(exc)), severity="error")
            return
        self.app.notify(self._t("exported", path=str(out_path)))

    def hide(self) -> None:
        """Blendet das Panel aus und postet `LogPanel.Hidden`."""
        self.add_class("-log-hidden")
        self.post_message(self.Hidden())

    def show(self) -> None:
        """Blendet das Panel wieder ein."""
        self.remove_class("-log-hidden")

    def toggle(self) -> None:
        """Schaltet die Sichtbarkeit des Panels um."""
        if self.has_class("-log-hidden"):
            self.show()
        else:
            self.hide()

    def on_click(self, event: Click) -> None:
        """Oeffnet bei Rechtsklick das Kontextmenue."""
        if event.button != 3:
            return
        items = [
            ContextMenuItem("copy", self._t("copy")),
            ContextMenuItem("export", self._t("export")),
            ContextMenuItem.separator(),
            ContextMenuItem("hide", self._t("hide")),
        ]
        self.app.push_screen(
            ContextMenuScreen(items, at=(event.screen_x, event.screen_y)),
            callback=self._on_menu_action,
        )

    def _on_menu_action(self, action_id: str | None) -> None:
        """Verarbeitet die im Kontextmenue gewaehlte Aktion."""
        if action_id == "copy":
            self.copy_log()
        elif action_id == "export":
            self.export_log()
        elif action_id == "hide":
            self.hide()

    def _t(self, key: str, **kwargs: object) -> str:
        """Uebersetzt einen Text-Schluessel mit optionalen Platzhaltern."""
        template = _PANEL_TEXT[self._lang].get(key, key)
        return template.format(**kwargs) if kwargs else template


class LogRouter(_LogRouterBase):
    """Mixin fuer `App`: leitet `LogMessage` ans erste `LogPanel` weiter.

    Damit kann jedes Widget per `post_message(LogMessage(...))` loggen, ohne
    das `LogPanel` zu kennen. Als Basisklasse vor `App` angeben:
    `class MyApp(LogRouter, App)`.
    """

    def on_log_message(self, message: LogMessage) -> None:
        """Schreibt eine eingehende `LogMessage` ins erste `LogPanel`.

        Args:
            message:
                Die von einem beliebigen Widget gepostete Log-Nachricht.
        """
        message.stop()
        panels = self.query(LogPanel)
        if panels:
            panels.first().write_log(message.text, message.level)
