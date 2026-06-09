"""Nachschlage-Dialog fuer HTTP-Statuscodes.

Zeigt die gaengigen HTTP-Statuscodes tabellarisch und nach Klasse gruppiert
(2xx Erfolg, 3xx Weiterleitung, 4xx Client-Fehler, 5xx Server-Fehler) mit einer
kurzen, faktenbasierten Bewertung und Erklaerung. Gedacht als schnelle
Referenz, z. B. um einen 301 von einem 307 zu unterscheiden.

Die Bewertung beschreibt die standardisierte Bedeutung des Codes (RFC-Semantik),
KEINE geratene Risikoeinschaetzung.

Usage:
    from textual_widgets import HttpStatusScreen

    def action_show_http_codes(self) -> None:
        self.push_screen(HttpStatusScreen(lang="de"))
"""

from __future__ import annotations

from dataclasses import dataclass

from rich import box
from rich.console import Group, RenderableType
from rich.table import Table
from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Static


@dataclass(frozen=True)
class _Code:
    """Ein HTTP-Statuscode mit zweisprachiger Bewertung und Erklaerung."""

    code: int
    rating_de: str
    rating_en: str
    expl_de: str
    expl_en: str


# Kuratierte, praxisrelevante Codes (kein Exoten-Rauschen wie 418).
_CODES: tuple[_Code, ...] = (
    # --- 2xx Erfolg ---
    _Code(200, "Erfolg", "Success", "Anfrage erfolgreich, Inhalt wird geliefert.", "Request succeeded, content is returned."),
    _Code(201, "Erfolg", "Success", "Erfolgreich - eine neue Ressource wurde angelegt.", "Succeeded - a new resource was created."),
    _Code(202, "Angenommen", "Accepted", "Angenommen, aber noch nicht fertig verarbeitet.", "Accepted but not yet fully processed."),
    _Code(204, "Erfolg", "Success", "Erfolgreich, aber kein Inhalt im Body.", "Succeeded, but no content in the body."),
    _Code(206, "Teilantwort", "Partial", "Teilantwort (Range-Anfrage, z. B. Download/Streaming).", "Partial response (range request, e.g. download/streaming)."),
    # --- 3xx Weiterleitung ---
    _Code(301, "Weiterleitung (dauerhaft)", "Redirect (permanent)", "Ressource dauerhaft unter neuer URL - Links aktualisieren.", "Resource permanently at a new URL - update links."),
    _Code(302, "Weiterleitung (temporär)", "Redirect (temporary)", "Temporär woanders; Clients wechseln die Methode oft zu GET.", "Temporarily elsewhere; clients often switch the method to GET."),
    _Code(303, "Weiterleitung", "Redirect", "Antwort per GET unter anderer URL holen (oft nach POST).", "Fetch the response via GET at another URL (often after POST)."),
    _Code(304, "Cache (unverändert)", "Cache (unchanged)", "Unverändert seit letztem Abruf - der Client nutzt seinen Cache.", "Unchanged since last fetch - the client uses its cache."),
    _Code(307, "Weiterleitung (temporär)", "Redirect (temporary)", "Temporär woanders; Methode und Body bleiben erhalten.", "Temporarily elsewhere; method and body are preserved."),
    _Code(308, "Weiterleitung (dauerhaft)", "Redirect (permanent)", "Dauerhaft woanders; Methode und Body bleiben erhalten.", "Permanently elsewhere; method and body are preserved."),
    # --- 4xx Client-Fehler ---
    _Code(400, "Client-Fehler", "Client error", "Ungültige Anfrage (z. B. fehlerhafte Syntax).", "Invalid request (e.g. malformed syntax)."),
    _Code(401, "Anmeldung nötig", "Login required", "Authentifizierung fehlt oder ist ungültig.", "Authentication is missing or invalid."),
    _Code(403, "Zugriff verweigert", "Access denied", "Server kennt die Anfrage, verweigert aber den Zugriff.", "Server understood the request but refuses access."),
    _Code(404, "Nicht gefunden", "Not found", "Ressource existiert nicht (mehr) unter dieser URL.", "Resource does not (or no longer) exist at this URL."),
    _Code(405, "Methode unzulässig", "Method not allowed", "HTTP-Methode für diese Ressource nicht erlaubt.", "HTTP method not allowed for this resource."),
    _Code(408, "Timeout", "Timeout", "Server hat zu lange auf die Anfrage gewartet.", "Server timed out waiting for the request."),
    _Code(409, "Konflikt", "Conflict", "Konflikt mit dem aktuellen Zustand der Ressource.", "Conflict with the current state of the resource."),
    _Code(410, "Entfernt", "Gone", "Ressource dauerhaft entfernt (bewusst, anders als 404).", "Resource permanently removed (deliberate, unlike 404)."),
    _Code(413, "Zu groß", "Too large", "Anfrage-Body ist zu groß.", "Request body is too large."),
    _Code(415, "Format nicht unterstützt", "Unsupported type", "Format des Anfrage-Bodys wird nicht unterstützt.", "Request body media type is not supported."),
    _Code(422, "Validierung fehlgeschlagen", "Validation failed", "Syntaktisch ok, aber inhaltlich nicht verarbeitbar.", "Syntactically ok but semantically invalid."),
    _Code(429, "Rate-Limit", "Rate limit", "Zu viele Anfragen in kurzer Zeit - bitte drosseln.", "Too many requests in a short time - slow down."),
    _Code(451, "Rechtlich gesperrt", "Legal block", "Aus rechtlichen Gründen nicht verfügbar.", "Unavailable for legal reasons."),
    # --- 5xx Server-Fehler ---
    _Code(500, "Server-Fehler", "Server error", "Unerwarteter interner Fehler auf dem Server.", "Unexpected internal error on the server."),
    _Code(501, "Nicht implementiert", "Not implemented", "Server unterstützt die nötige Funktion nicht.", "Server does not support the required functionality."),
    _Code(502, "Bad Gateway", "Bad gateway", "Vorgelagerter Server lieferte eine ungültige Antwort.", "Upstream server returned an invalid response."),
    _Code(503, "Server-Fehler (temporär)", "Server error (temporary)", "Dienst momentan nicht verfügbar (Überlast/Wartung).", "Service temporarily unavailable (overload/maintenance)."),
    _Code(504, "Gateway-Timeout", "Gateway timeout", "Vorgelagerter Server antwortete nicht rechtzeitig.", "Upstream server did not respond in time."),
    _Code(505, "Version nicht unterstützt", "Version unsupported", "Die HTTP-Version wird nicht unterstützt.", "The HTTP version is not supported."),
    _Code(507, "Speicher voll", "Insufficient storage", "Server hat nicht genug Speicher für die Anfrage.", "Server has insufficient storage for the request."),
    _Code(511, "Anmeldung erforderlich", "Auth required", "Netzwerk verlangt Authentifizierung (Proxy/Captive Portal).", "Network requires authentication (proxy/captive portal)."),
)

# Farbe pro Statusklasse.
_CLASS_STYLE: dict[int, str] = {2: "green", 3: "cyan", 4: "yellow", 5: "bold red"}

# Gruppen-Ueberschriften je Sprache.
_GROUP_LABEL: dict[str, dict[int, str]] = {
    "de": {2: "2xx - Erfolg", 3: "3xx - Weiterleitung", 4: "4xx - Client-Fehler", 5: "5xx - Server-Fehler"},
    "en": {2: "2xx - Success", 3: "3xx - Redirection", 4: "4xx - Client error", 5: "5xx - Server error"},
}

# Spaltenkoepfe und sonstige UI-Texte je Sprache.
_TEXT: dict[str, dict[str, str]] = {
    "de": {"title": "HTTP-Statuscodes", "col_code": "Code", "col_rating": "Bewertung", "col_expl": "Erklärung", "close": "Schließen"},
    "en": {"title": "HTTP status codes", "col_code": "Code", "col_rating": "Rating", "col_expl": "Explanation", "close": "Close"},
}


class HttpStatusScreen(ModalScreen[None]):
    """Modaler Nachschlage-Dialog fuer HTTP-Statuscodes."""

    DEFAULT_CSS = """
    HttpStatusScreen {
        align: center middle;
    }

    HttpStatusScreen > Vertical {
        width: 90%;
        max-width: 100;
        height: auto;
        max-height: 90%;
        background: $surface;
        border: thick $accent;
        padding: 1 2;
    }

    HttpStatusScreen #http-title {
        height: auto;
        max-height: 5;
        content-align: center middle;
        text-style: bold;
        background: $accent;
        color: auto;
        margin-bottom: 1;
        padding: 1 2;
    }

    HttpStatusScreen #http-scroll {
        height: auto;
        max-height: 90%;
    }

    HttpStatusScreen #http-content {
        height: auto;
        padding: 0 1;
    }

    HttpStatusScreen #http-buttons {
        dock: bottom;
        height: 3;
        align: center middle;
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("q,Q", "close", "Close"),
        Binding("question_mark", "close", "Close"),
    ]

    def __init__(self, lang: str = "de", **kwargs: object) -> None:
        """Erstellt den HTTP-Statuscode-Dialog.

        Args:
            lang:
                Sprachkuerzel ('de' oder 'en'). Unbekannt faellt auf 'en'.
        """
        super().__init__(**kwargs)  # type: ignore[arg-type]
        self._lang = lang if lang in _TEXT else "en"

    def _txt(self, key: str) -> str:
        return _TEXT[self._lang][key]

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(self._txt("title"), id="http-title")
            with VerticalScroll(id="http-scroll"):
                yield Static(self._build_table(), id="http-content")
            with Horizontal(id="http-buttons"):
                close_button = Button(self._txt("close"), variant="primary", id="http-close")
                close_button.can_focus = False
                with Center():
                    yield close_button

    def _build_table(self) -> RenderableType:
        """Baut pro Statusklasse eine eigene, buendig ausgerichtete Tabelle.

        Eine Tabelle pro Gruppe (mit farbiger Titelzeile darueber) statt einer
        einzigen mit eingebetteten Header-Zeilen: So landet die Gruppen-
        Ueberschrift nicht in der schmalen Code-Spalte. Identische Spalten-
        breiten sorgen dafuer, dass die Gruppen untereinander fluchten.
        """
        de = self._lang == "de"
        renderables: list[RenderableType] = []

        for cls in (2, 3, 4, 5):
            style = _CLASS_STYLE[cls]
            if renderables:
                renderables.append(Text(""))  # Leerzeile zwischen den Gruppen
            renderables.append(Text(_GROUP_LABEL[self._lang][cls], style=f"bold {style}"))

            table: Table = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="bold dim", pad_edge=False, expand=True)
            table.add_column(self._txt("col_code"), justify="right", width=5, no_wrap=True)
            table.add_column(self._txt("col_rating"), width=28, no_wrap=True)
            table.add_column(self._txt("col_expl"), ratio=1)
            for c in (x for x in _CODES if x.code // 100 == cls):
                table.add_row(
                    Text(str(c.code), style=style),
                    Text(c.rating_de if de else c.rating_en, style=style),
                    c.expl_de if de else c.expl_en,
                )
            renderables.append(table)

        return Group(*renderables)

    @on(Button.Pressed, "#http-close")
    def _on_close_button(self) -> None:
        self.dismiss(None)

    def action_close(self) -> None:
        self.dismiss(None)
