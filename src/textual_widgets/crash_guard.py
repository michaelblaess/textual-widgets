"""Crash-Guard: faengt unbehandelte Exceptions ab statt die App abstuerzen zu lassen.

Public API:
    - `ErrorScreen` — ModalScreen, der einen Fehlerbericht anzeigt (kopierbar)
      und den Anwender zwischen Weitermachen und Beenden waehlen laesst.
    - `CrashGuard` — Mixin fuer `App`. Faengt unbehandelte Exceptions ab und
      zeigt statt eines Total-Absturzes den `ErrorScreen`.

Usage:
    from textual.app import App
    from textual_widgets import CrashGuard

    class MyApp(CrashGuard, App):
        def __init__(self) -> None:
            super().__init__()
            self.crash_guard_lang = "de"   # Sprache des Fehlerdialogs

Die Reihenfolge `CrashGuard, App` ist wichtig: `super()._handle_exception()`
im Mixin muss `App._handle_exception()` treffen (regulaerer Absturzpfad als
Fallback, falls der Fehlerdialog selbst scheitert).
"""

from __future__ import annotations

import traceback
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Static

if TYPE_CHECKING:
    from textual.app import App

    # Unter mypy ist die Basis App[object] — damit `super()._handle_exception`
    # und `self.push_screen` typgeprueft werden. Zur Laufzeit ist die Basis
    # `object`; `super()` folgt der echten MRO der konkreten App-Klasse.
    _CrashGuardBase = App[object]
else:
    _CrashGuardBase = object


# Texte des Fehlerdialogs pro Sprache. Andere Sprachen fallen auf Englisch zurueck.
_TEXTS: dict[str, dict[str, str]] = {
    "de": {
        "title": "Ein Fehler ist aufgetreten",
        "apology": "Entschuldigung - in der Anwendung ist ein unerwarteter Fehler aufgetreten.",
        "hint": "Du kannst den Fehlerbericht kopieren und weiterarbeiten oder die Anwendung beenden.",
        "copy": "Kopieren",
        "continue": "Weitermachen",
        "quit": "Beenden",
        "copied": "Fehlerbericht in die Zwischenablage kopiert",
    },
    "en": {
        "title": "An error has occurred",
        "apology": "Sorry - an unexpected error occurred in the application.",
        "hint": "You can copy the error report and keep working, or quit the application.",
        "copy": "Copy",
        "continue": "Continue",
        "quit": "Quit",
        "copied": "Error report copied to clipboard",
    },
}


class ErrorScreen(ModalScreen[None]):
    """Modal-Dialog mit einem Fehlerbericht.

    Zeigt eine Entschuldigung, die Fehlerzeile, den vollstaendigen Traceback
    (scrollbar, per Button kopierbar) und ueberlaesst dem Anwender die Wahl
    zwischen Weitermachen und Beenden.
    """

    DEFAULT_CSS = """
    ErrorScreen {
        align: center middle;
    }

    ErrorScreen > Vertical {
        width: 90%;
        max-width: 120;
        height: 80%;
        background: $surface;
        border: thick $error;
        padding: 1 2;
    }

    ErrorScreen #error-title {
        width: 1fr;
        height: 3;
        content-align: center middle;
        text-style: bold;
        background: $error;
        color: auto;
        margin-bottom: 1;
    }

    ErrorScreen #error-apology {
        width: 1fr;
    }

    ErrorScreen #error-line {
        width: 1fr;
        color: $error;
        text-style: bold;
        margin: 1 0;
    }

    ErrorScreen #error-report {
        width: 1fr;
        height: 1fr;
        border: round $surface-lighten-2;
        background: $panel;
        padding: 0 1;
    }

    ErrorScreen #error-hint {
        width: 1fr;
        color: $text-muted;
        margin-top: 1;
    }

    ErrorScreen #error-buttons {
        width: 1fr;
        height: 3;
        align: center middle;
        margin-top: 1;
    }

    ErrorScreen #error-buttons Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("escape", "continue", "ESC"),
    ]

    def __init__(self, error: BaseException, report: str, lang: str = "en") -> None:
        """Erstellt den Fehlerdialog.

        Args:
            error:
                Die aufgetretene Exception (fuer die kurze Fehlerzeile).
            report:
                Der vollstaendige Traceback-Text (scrollbar und kopierbar).
            lang:
                Sprachkuerzel ('de' oder 'en') fuer die Dialogtexte.
        """
        super().__init__()
        self._report = report
        self._error_line = f"{type(error).__name__}: {error}"
        self._t = _TEXTS.get(lang, _TEXTS["en"])

    def compose(self) -> ComposeResult:
        """Erstellt das Modal-Layout."""
        with Vertical():
            yield Static(self._t["title"], id="error-title")
            yield Static(self._t["apology"], id="error-apology")
            yield Static(self._error_line, id="error-line")
            with VerticalScroll(id="error-report"):
                yield Static(self._report, id="error-report-text")
            yield Static(self._t["hint"], id="error-hint")
            with Horizontal(id="error-buttons"):
                yield Button(self._t["copy"], id="error-copy")
                yield Button(self._t["continue"], variant="primary", id="error-continue")
                yield Button(self._t["quit"], variant="error", id="error-quit")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Verarbeitet Klicks auf die drei Buttons."""
        if event.button.id == "error-copy":
            self.app.copy_to_clipboard(self._report)
            self.notify(self._t["copied"])
        elif event.button.id == "error-quit":
            self.app.exit()
        else:
            self.dismiss(None)

    def action_continue(self) -> None:
        """Schliesst den Dialog (ESC) — die App laeuft weiter."""
        self.dismiss(None)


class CrashGuard(_CrashGuardBase):
    """Mixin fuer `App`: faengt unbehandelte Exceptions ab.

    Statt die App bei einem unbehandelten Fehler abstuerzen zu lassen, wird
    der `ErrorScreen` angezeigt. Der Anwender kann den Fehlerbericht kopieren
    und weiterarbeiten oder die App beenden.

    Als erste Basisklasse VOR `App` angeben: `class MyApp(CrashGuard, App)`.

    Attributes:
        crash_guard_lang:
            Sprache des Fehlerdialogs ('de' oder 'en'). Kann pro App-Instanz
            im `__init__` gesetzt werden.
    """

    crash_guard_lang: str = "en"
    _crash_guard_busy: bool = False

    def _handle_exception(self, error: Exception) -> None:
        """Faengt unbehandelte Exceptions ab und zeigt den Fehlerdialog.

        Args:
            error:
                Die von Textual gemeldete unbehandelte Exception.
        """
        # Tritt waehrend eines bereits offenen Fehlerdialogs ein weiterer
        # Fehler auf, nicht endlos schachteln — regulaerer Absturzpfad.
        if self._crash_guard_busy:
            super()._handle_exception(error)
            return

        self._crash_guard_busy = True
        report = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        try:
            self.push_screen(
                ErrorScreen(error, report, lang=self.crash_guard_lang),
                callback=self._crash_guard_reset,
            )
        except Exception:
            # Selbst der Fehlerdialog scheitert — regulaerer Absturzpfad.
            super()._handle_exception(error)

    def _crash_guard_reset(self, _result: None) -> None:
        """Gibt den Guard nach dem Schliessen des Dialogs wieder frei."""
        self._crash_guard_busy = False
