"""Generischer modaler Dialog zur Eingabe einer Zeile Text.

Public API:
    - `TextInputScreen` - ModalScreen[str | None] mit optionalem Validator.

Usage:
    from textual_widgets import TextInputScreen

    def action_enter_name(self) -> None:
        self.push_screen(
            TextInputScreen(
                title="Eigene Idee hinzufuegen",
                prompt="Name fuer den Favoriten:",
                placeholder="z.B. Sitemap Pioneer",
                validator=lambda s: None if s.strip() else "Name darf nicht leer sein",
                lang="de",
            ),
            callback=self._on_name_entered,
        )

    def _on_name_entered(self, name: str | None) -> None:
        if name is None:
            return  # Abbruch
        ...

Der Dialog liefert den getrimmten Eingabetext oder `None` bei Abbruch
(ESC / Cancel-Button). Ein optionaler `validator` bekommt den getrimmten
Text und gibt `None` zurueck, wenn die Eingabe gueltig ist, oder einen
Fehlertext, der inline angezeigt wird (Dialog bleibt offen).
"""

from __future__ import annotations

from collections.abc import Callable

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static

# Validator-Signatur: bekommt den getrimmten Text, gibt None bei OK
# oder einen Fehlertext zur Inline-Anzeige zurueck.
Validator = Callable[[str], str | None]

# Dialog-Texte pro Sprache. Andere Sprachen fallen auf Englisch zurueck.
_TEXT: dict[str, dict[str, str]] = {
    "de": {
        "ok": "OK",
        "cancel": "Abbrechen (Esc)",
        "empty_error": "Bitte einen Text eingeben.",
    },
    "en": {
        "ok": "OK",
        "cancel": "Cancel (Esc)",
        "empty_error": "Please enter a value.",
    },
}


class TextInputScreen(ModalScreen[str | None]):
    """Generischer modaler Dialog fuer eine einzeilige Texteingabe.

    Zeigt Titel, optionalen Hinweis, Eingabefeld, OK- und Abbrechen-Button.
    Bei OK (oder Enter im Eingabefeld) wird der Text getrimmt und - falls
    angegeben - durch den Validator geschickt. Gibt der Validator einen
    Fehlertext zurueck, erscheint dieser inline und der Dialog bleibt offen.
    Bei gueltiger Eingabe schliesst der Dialog und liefert den Text an den
    Callback. ESC oder Abbrechen liefern `None`.

    Ohne Validator gilt: leerer Text wird mit einem Default-Fehlertext
    abgelehnt - ein leerer String waere als Ergebnis kaum brauchbar. Wer
    leere Eingaben akzeptieren will, uebergibt `validator=lambda s: None`.
    """

    DEFAULT_CSS = """
    TextInputScreen {
        align: center middle;
    }

    TextInputScreen > Vertical {
        width: 72;
        max-width: 90%;
        height: auto;
        background: $surface;
        border: thick $accent;
        padding: 1 2;
    }

    TextInputScreen #text-title {
        width: 1fr;
        height: 3;
        content-align: center middle;
        text-style: bold;
        background: $accent;
        color: auto;
        margin-bottom: 1;
    }

    TextInputScreen #text-prompt {
        width: 1fr;
        margin-bottom: 1;
    }

    TextInputScreen #text-prompt.hidden {
        display: none;
    }

    TextInputScreen #text-input {
        width: 1fr;
    }

    TextInputScreen #text-error {
        width: 1fr;
        height: auto;
        color: $error;
        text-style: bold;
        margin-top: 1;
        display: none;
    }

    TextInputScreen #text-error.visible {
        display: block;
    }

    TextInputScreen #text-buttons {
        height: 3;
        align: center middle;
        margin-top: 1;
    }

    TextInputScreen #text-buttons Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Esc"),
    ]

    def __init__(
        self,
        *,
        title: str,
        prompt: str = "",
        initial: str = "",
        placeholder: str = "",
        validator: Validator | None = None,
        lang: str = "en",
    ) -> None:
        """Erstellt den Text-Eingabedialog.

        Args:
            title:
                Titel im farbigen Kopfbalken des Dialogs.
            prompt:
                Hinweistext oberhalb des Eingabefelds. Leer = ausgeblendet.
            initial:
                Vorbelegung des Eingabefelds.
            placeholder:
                Platzhaltertext im Eingabefeld, wenn leer.
            validator:
                Optionale Validierungsfunktion. Bekommt den getrimmten Text
                und gibt `None` zurueck, wenn er gueltig ist, oder einen
                Fehlertext, der inline angezeigt wird.
            lang:
                Sprachkuerzel ('de' oder 'en') fuer Button-Beschriftungen
                und den Default-Fehlertext "leere Eingabe".
        """
        super().__init__()
        self._title = title
        self._prompt = prompt
        self._initial = initial
        self._placeholder = placeholder
        self._validator = validator
        self._lang = lang if lang in _TEXT else "en"

    def compose(self) -> ComposeResult:
        """Erstellt das Dialog-Layout: Titel, Hinweis, Eingabe, Buttons."""
        with Vertical():
            yield Static(self._title, id="text-title")
            prompt_label = Label(self._prompt, id="text-prompt")
            if not self._prompt:
                prompt_label.add_class("hidden")
            yield prompt_label
            yield Input(
                value=self._initial,
                placeholder=self._placeholder,
                id="text-input",
            )
            yield Static("", id="text-error")
            with Horizontal(id="text-buttons"):
                yield Button(self._t("ok"), variant="primary", id="text-ok")
                yield Button(self._t("cancel"), id="text-cancel")

    def on_mount(self) -> None:
        """Setzt den Fokus auf das Eingabefeld."""
        self.query_one("#text-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Enter im Eingabefeld loest das Absenden aus."""
        event.stop()
        self.action_submit()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Blendet die Fehlermeldung aus, sobald der Text geaendert wird."""
        self.query_one("#text-error", Static).remove_class("visible")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Verarbeitet Klicks auf OK / Abbrechen."""
        if event.button.id == "text-ok":
            self.action_submit()
        else:
            self.action_cancel()

    def action_submit(self) -> None:
        """Validiert die Eingabe und schliesst den Dialog bei Erfolg."""
        text = self.query_one("#text-input", Input).value.strip()
        error = self._check(text)
        if error is not None:
            error_widget = self.query_one("#text-error", Static)
            error_widget.update(error)
            error_widget.add_class("visible")
            return
        self.dismiss(text)

    def action_cancel(self) -> None:
        """Schliesst den Dialog ohne Ergebnis (ESC / Abbrechen)."""
        self.dismiss(None)

    def _check(self, text: str) -> str | None:
        """Wendet den Validator an oder verwendet die Default-Leer-Pruefung."""
        if self._validator is not None:
            return self._validator(text)
        if not text:
            return self._t("empty_error")
        return None

    def _t(self, key: str) -> str:
        """Uebersetzt einen Text-Schluessel in die gewaehlte Sprache."""
        return _TEXT[self._lang].get(key, key)
