"""Modaler Dialog zur Eingabe einer http/https-URL.

Public API:
    - `UrlInputScreen` — ModalScreen, das eine validierte URL abfragt.

Usage:
    from textual_widgets import UrlInputScreen

    def action_enter_url(self) -> None:
        self.push_screen(
            UrlInputScreen(lang="de"),
            callback=self._on_url_entered,
        )

    def _on_url_entered(self, url: str | None) -> None:
        if url is None:
            return  # Abbruch
        self.start_url = url

Der Dialog gibt die eingegebene URL (inklusive http/https-Schema) zurueck
oder `None` bei Abbruch. Eingaben ohne Schema werden automatisch mit
'https://' ergaenzt. Ungueltige Eingaben zeigen eine Inline-Fehlermeldung
und schliessen den Dialog nicht.
"""

from __future__ import annotations

from urllib.parse import urlparse

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static

# Dialog-Texte pro Sprache. Andere Sprachen fallen auf Englisch zurueck.
_TEXT: dict[str, dict[str, str]] = {
    "de": {
        "title": "URL eingeben",
        "prompt": "Adresse der Website (http:// oder https://):",
        "placeholder": "https://example.com",
        "ok": "OK",
        "cancel": "Abbrechen (Esc)",
        "error": "Bitte eine gültige http(s)-URL eingeben.",
    },
    "en": {
        "title": "Enter URL",
        "prompt": "Website address (http:// or https://):",
        "placeholder": "https://example.com",
        "ok": "OK",
        "cancel": "Cancel (Esc)",
        "error": "Please enter a valid http(s) URL.",
    },
}


class UrlInputScreen(ModalScreen[str | None]):
    """Modaler Dialog zur Eingabe einer http/https-URL.

    Zeigt ein Eingabefeld, einen OK- und einen Abbrechen-Button. Bei OK
    (oder Enter im Eingabefeld) wird die Eingabe validiert: fehlt das
    Schema, wird 'https://' ergaenzt; ist die URL ungueltig, erscheint eine
    Inline-Fehlermeldung und der Dialog bleibt offen. Bei gueltiger Eingabe
    schliesst der Dialog und liefert die URL an den Callback. ESC oder
    Abbrechen liefern `None`.
    """

    DEFAULT_CSS = """
    UrlInputScreen {
        align: center middle;
    }

    UrlInputScreen > Vertical {
        width: 72;
        max-width: 90%;
        height: auto;
        background: $surface;
        border: thick $accent;
        padding: 1 2;
    }

    UrlInputScreen #url-title {
        width: 1fr;
        height: 3;
        content-align: center middle;
        text-style: bold;
        background: $accent;
        color: auto;
        margin-bottom: 1;
    }

    UrlInputScreen #url-prompt {
        width: 1fr;
        margin-bottom: 1;
    }

    UrlInputScreen #url-input {
        width: 1fr;
    }

    UrlInputScreen #url-error {
        width: 1fr;
        height: auto;
        color: $error;
        text-style: bold;
        margin-top: 1;
        display: none;
    }

    UrlInputScreen #url-error.visible {
        display: block;
    }

    UrlInputScreen #url-buttons {
        height: 3;
        align: center middle;
        margin-top: 1;
    }

    UrlInputScreen #url-buttons Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Esc"),
    ]

    def __init__(
        self,
        *,
        initial: str = "",
        lang: str = "en",
        title: str | None = None,
        prompt: str | None = None,
        placeholder: str | None = None,
    ) -> None:
        """Erstellt den URL-Eingabedialog.

        Args:
            initial:
                Vorbelegung des Eingabefelds (z.B. eine zuletzt verwendete
                URL). Default ist leer.
            lang:
                Sprachkuerzel ('de' oder 'en') fuer die Dialogtexte.
            title:
                Optionaler eigener Titel. Default ist der sprachabhaengige
                Text ("URL eingeben" / "Enter URL").
            prompt:
                Optionaler eigener Hinweistext ueber dem Eingabefeld.
            placeholder:
                Optionaler eigener Platzhaltertext im Eingabefeld.
        """
        super().__init__()
        self._lang = lang if lang in _TEXT else "en"
        self._initial = initial
        self._title = title if title is not None else self._t("title")
        self._prompt = prompt if prompt is not None else self._t("prompt")
        self._placeholder = placeholder if placeholder is not None else self._t("placeholder")

    def compose(self) -> ComposeResult:
        """Erstellt das Dialog-Layout: Titel, Hinweis, Eingabe, Buttons."""
        with Vertical():
            yield Static(self._title, id="url-title")
            yield Label(self._prompt, id="url-prompt")
            yield Input(
                value=self._initial,
                placeholder=self._placeholder,
                id="url-input",
            )
            yield Static("", id="url-error")
            with Horizontal(id="url-buttons"):
                yield Button(self._t("ok"), variant="primary", id="url-ok")
                yield Button(self._t("cancel"), id="url-cancel")

    def on_mount(self) -> None:
        """Setzt den Fokus auf das Eingabefeld."""
        self.query_one("#url-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Enter im Eingabefeld loest das Absenden aus."""
        event.stop()
        self.action_submit()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Blendet die Fehlermeldung aus, sobald der Text geaendert wird."""
        self.query_one("#url-error", Static).remove_class("visible")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Verarbeitet Klicks auf OK / Abbrechen."""
        if event.button.id == "url-ok":
            self.action_submit()
        else:
            self.action_cancel()

    def action_submit(self) -> None:
        """Validiert die Eingabe und schliesst den Dialog bei Erfolg."""
        raw = self.query_one("#url-input", Input).value
        url = self._validate(raw)
        if url is None:
            error = self.query_one("#url-error", Static)
            error.update(self._t("error"))
            error.add_class("visible")
            return
        self.dismiss(url)

    def action_cancel(self) -> None:
        """Schliesst den Dialog ohne Ergebnis (ESC / Abbrechen)."""
        self.dismiss(None)

    @staticmethod
    def _validate(raw: str) -> str | None:
        """Prueft und normalisiert eine eingegebene URL.

        Args:
            raw:
                Der rohe Eingabetext.

        Returns:
            Die normalisierte URL mit http/https-Schema, oder `None`, wenn
            die Eingabe keine gueltige http(s)-URL ergibt.
        """
        text = raw.strip()
        if not text:
            return None

        # Fehlt das Schema, https:// voranstellen.
        candidate = text if "://" in text else f"https://{text}"

        parsed = urlparse(candidate)
        if parsed.scheme not in ("http", "https"):
            return None

        host = parsed.hostname or ""
        if not host:
            return None

        # Ein Host ohne Punkt ist nur als 'localhost' sinnvoll.
        if "." not in host and host != "localhost":
            return None

        return candidate

    def _t(self, key: str) -> str:
        """Uebersetzt einen Text-Schluessel in die gewaehlte Sprache."""
        return _TEXT[self._lang].get(key, key)
