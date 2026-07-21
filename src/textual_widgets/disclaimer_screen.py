"""Bestaetigungspflichtiger Haftungs- und Nutzungshinweis beim Programmstart.

Gedacht fuer Werkzeuge, die auf fremde Systeme einwirken - Scanner und Crawler,
die Last erzeugen, ebenso wie Werkzeuge, die in einem Fremdsystem Daten anlegen
oder aendern. Der Dialog blockiert die Anwendung, bis der Hinweis ausdruecklich
bestaetigt wurde; wird er abgelehnt, beendet sich die Anwendung.

Ueberschrift, Einleitung und die Zusicherungen lassen sich je Anwendung
ersetzen; der Haftungsabsatz bleibt bewusst fest, damit er ueber alle Werkzeuge
hinweg gleich lautet.

Public API:
    - `DisclaimerScreen`   - ModalScreen[bool], liefert True bei Zustimmung.
    - `DisclaimerStore`    - merkt die Zustimmung samt Textfassung in einer JSON-Datei.
    - `DISCLAIMER_VERSION` - Fassung des Textes; aendert sie sich, wird erneut gefragt.
    - `disclaimer_text`   - derselbe Wortlaut als Fliesstext (Kommandozeile, README).

Usage:
    from textual_widgets import DISCLAIMER_VERSION, DisclaimerScreen, DisclaimerStore

    def on_mount(self) -> None:
        self._disclaimer = DisclaimerStore(Path.home() / ".my-tool" / "disclaimer.json")
        if self._disclaimer.accepted_version == DISCLAIMER_VERSION:
            return
        self.push_screen(
            DisclaimerScreen(app_name="my-tool", lang="de"),
            callback=self._on_disclaimer,
        )

    def _on_disclaimer(self, accepted: bool | None) -> None:
        if not accepted:
            self.exit()
            return
        self._disclaimer.record()

Rechtlicher Hinweis an den Verwender dieses Widgets: Der mitgelieferte Text
orientiert sich an gaengiger Praxis in Open-Source-Projekten und laesst die nach
deutschem Recht zwingenden Haftungstatbestaende ausdruecklich unberuehrt (eine
Klausel, die auch diese ausschliesst, riskiert insgesamt unwirksam zu sein). Er
ersetzt keine Rechtsberatung.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Label, Rule, Static

# Fassung des Hinweistextes. Bei inhaltlichen Aenderungen hochzaehlen - dann
# wird die Zustimmung erneut eingeholt, statt eine alte Fassung fortzuschreiben.
DISCLAIMER_VERSION = "2026-07-21"

_TEXT: dict[str, dict[str, str]] = {
    "de": {
        "title": "Nutzung auf eigene Verantwortung",
        "intro": (
            "Dieses Programm ruft Webseiten automatisiert ab und erzeugt dabei Last auf den "
            "Zielsystemen. Je nach Einstellung kann diese Last die eines normalen Besuchers um "
            "ein Vielfaches übersteigen und die Erreichbarkeit des Zielsystems beeinträchtigen."
        ),
        "duties_title": "Mit Ihrer Bestätigung erklären Sie:",
        # Drei getrennte Aussagen - Gewaehrleistung, Haftung, gesetzliche Grenze -
        # bewusst als eigene Absaetze, sonst liest sich der Block als Textwand.
        "liability": (
            "Die Software wird unentgeltlich und ohne jede Gewährleistung bereitgestellt "
            '("as is"), wie in Abschnitt 7 der Apache-Lizenz 2.0 beschrieben.\n\n'
            "Eine Haftung des Autors{author} für Schäden, die aus der Nutzung entstehen, ist "
            "ausgeschlossen, soweit dies gesetzlich zulässig ist.\n\n"
            "Unberührt bleibt die Haftung für Vorsatz und grobe Fahrlässigkeit, für Schäden aus "
            "der Verletzung des Lebens, des Körpers oder der Gesundheit sowie nach dem "
            "Produkthaftungsgesetz."
        ),
        "checkbox": "Ich habe den Hinweis gelesen und stimme zu",
        "accept": "Bestätigen",
        "quit": "Beenden (Esc)",
        "hint": "Ohne Zustimmung kann das Programm nicht verwendet werden!",
    },
    "en": {
        "title": "Use at your own risk",
        "intro": (
            "This program retrieves web pages automatically and thereby places load on the "
            "target systems. Depending on its settings, that load can exceed the load of an "
            "ordinary visitor many times over and can impair the availability of the target "
            "system."
        ),
        "duties_title": "By confirming, you declare that:",
        "liability": (
            'The software is provided free of charge and without warranty of any kind ("as '
            'is"), as set out in section 7 of the Apache License 2.0.\n\n'
            "The liability of the author{author} for damages arising from its use is excluded "
            "to the extent permitted by applicable law.\n\n"
            "Liability for intent and gross negligence, for injury to life, body or health, and "
            "under mandatory product liability law remains unaffected."
        ),
        "checkbox": "I have read this notice and accept it",
        "accept": "Confirm",
        "quit": "Quit (Esc)",
        "hint": "The program cannot be used without your consent!",
    },
}

# Zusicherungen des Nutzers, je Sprache. Getrennt von _TEXT, weil es eine
# Liste ist - und weil Anwendungen sie ersetzen koennen (siehe DisclaimerScreen).
_DUTIES: dict[str, tuple[str, ...]] = {
    "de": (
        "Sie setzen das Programm ausschließlich gegen Systeme ein, für die Ihnen eine "
        "ausdrückliche Berechtigung des Betreibers vorliegt.",
        "Sie tragen die alleinige Verantwortung für den Einsatz, die gewählten "
        "Einstellungen und alle daraus entstehenden Folgen.",
        "Vor einem Lauf gegen ein Produktivsystem prüfen Sie, ob die eingestellten "
        "Grenzwerte für dieses System angemessen sind.",
    ),
    "en": (
        "You will use this program only against systems for which you hold explicit authorisation from their operator.",
        "You bear sole responsibility for its use, for the settings you choose and for "
        "all consequences arising from them.",
        "Before running it against a production system, you will verify that the "
        "configured limits are appropriate for that system.",
    ),
}


def _liability(text: dict[str, str], author: str) -> str:
    """Setzt den Rechteinhaber in den Haftungsabsatz ein.

    Ohne Angabe bleibt es beim unbestimmten "des Autors"; mit Angabe wird er in
    Klammern benannt, damit erkennbar ist, wer die Haftung ausschliesst.

    Args:
        text:
        Textblock der gewaehlten Sprache.
        author:
        Name des Rechteinhabers, oder leer.

    Returns:
        Haftungsabsatz mit eingesetztem Namen.
    """
    return text["liability"].format(author=f" ({author})" if author.strip() else "")


def disclaimer_text(
    lang: str = "en",
    extra_notice: str = "",
    author: str = "",
    title: str = "",
    intro: str = "",
    duties: tuple[str, ...] | None = None,
) -> str:
    """Liefert den Hinweistext als Fliesstext.

    Gedacht fuer Zusammenhaenge ohne Oberflaeche - Kommandozeilenbetrieb, README
    oder Projektseite -, damit dort derselbe Wortlaut steht wie im Dialog.

    Args:
        lang:
        Sprachkuerzel ("de"/"en"); andere Werte fallen auf Englisch zurueck.
        extra_notice:
        Optionaler zusaetzlicher Absatz (siehe DisclaimerScreen).
        author:
        Rechteinhaber, der im Haftungsabsatz benannt wird.
        title:
        Abweichende Ueberschrift; leer = Standardtext der Sprache.
        intro:
        Abweichender Einleitungsabsatz; leer = Standardtext der Sprache.
        duties:
        Abweichende Zusicherungen (ohne Nummerierung); None = Standardliste.

    Returns:
        Mehrzeiliger Text mit Leerzeile zwischen den Absaetzen.
    """
    key = lang if lang in _TEXT else "en"
    text = _TEXT[key]
    blocks = [title or text["title"], intro or text["intro"]]
    if extra_notice:
        blocks.append(extra_notice)
    items = duties if duties is not None else _DUTIES[key]
    numbered = [f"{number}. {duty}" for number, duty in enumerate(items, start=1)]
    blocks.append("\n".join([text["duties_title"], *numbered]))
    blocks.append(_liability(text, author))
    return "\n\n".join(blocks)


class DisclaimerStore:
    """Merkt die erteilte Zustimmung samt Textfassung in einer JSON-Datei."""

    def __init__(self, path: Path) -> None:
        self._path = path

    @property
    def path(self) -> Path:
        """Speicherort der Zustimmung (fuer den Speicherort-Tab der Einstellungen)."""
        return self._path

    @property
    def accepted_version(self) -> str | None:
        """Fassung, der zugestimmt wurde - oder None, wenn keine Zustimmung vorliegt."""
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        version = data.get("accepted_version")
        return version if isinstance(version, str) else None

    def record(self, version: str = DISCLAIMER_VERSION) -> None:
        """Schreibt die Zustimmung mit Zeitstempel fest."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "accepted_version": version,
            "accepted_at": datetime.now(UTC).isoformat(timespec="seconds"),
        }
        self._path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


class DisclaimerScreen(ModalScreen[bool]):
    """Modaler Hinweis, der ohne ausdrueckliche Zustimmung nicht verlassen wird.

    Liefert True bei Zustimmung und False bei Ablehnung (Esc, Beenden-Knopf).
    Die aufrufende Anwendung ist dafuer zustaendig, sich bei False zu beenden.
    """

    BINDINGS = [Binding("escape", "refuse", "Beenden", show=False)]

    DEFAULT_CSS = """
    DisclaimerScreen {
        align: center middle;
        background: $background 70%;
    }
    DisclaimerScreen #disclaimer-box {
        width: 84;
        max-width: 96%;
        height: auto;
        max-height: 94%;
        scrollbar-size-vertical: 1;
        border: thick $warning;
        background: $surface;
        padding: 1 2;
    }
    DisclaimerScreen #disclaimer-title {
        text-style: bold;
        color: $warning;
        background: $warning 15%;
        width: 100%;
        text-align: center;
        margin-bottom: 1;
    }
    DisclaimerScreen #disclaimer-body {
        height: auto;
    }
    DisclaimerScreen .disclaimer-para {
        padding-bottom: 1;
    }
    DisclaimerScreen .disclaimer-duty {
        padding: 0 0 0 2;
    }
    DisclaimerScreen #disclaimer-app {
        color: $text-muted;
    }
    DisclaimerScreen #disclaimer-hint {
        color: $text-muted;
        text-style: bold;
        padding-top: 1;
    }
    DisclaimerScreen #disclaimer-footer {
        color: $text-disabled;
        width: 100%;
        text-align: center;
        padding-top: 1;
    }
    DisclaimerScreen Rule {
        margin: 1 0;
    }
    /* Ohne eigenen Rahmen: der Kasten hat bereits einen, und die zwei
       gesparten Zeilen entscheiden darueber, ob Hinweis und Fusszeile ohne
       Scrollen sichtbar bleiben. */
    DisclaimerScreen #disclaimer-agree {
        border: none;
        padding: 0;
        margin-top: 1;
    }
    DisclaimerScreen #disclaimer-buttons {
        height: auto;
        width: 100%;
        padding-top: 1;
        align-horizontal: center;
    }
    DisclaimerScreen #disclaimer-buttons Button {
        margin-left: 2;
    }
    """

    def __init__(
        self,
        app_name: str = "",
        lang: str = "en",
        extra_notice: str = "",
        author: str = "",
        footer: str = "",
        title: str = "",
        intro: str = "",
        duties: tuple[str, ...] | None = None,
    ) -> None:
        """Baut den Hinweis auf.

        Args:
            app_name:
            Name des Programms; erscheint als Zeile ueber dem Hinweis.
            lang:
            Sprachkuerzel ("de"/"en"); andere Werte fallen auf Englisch zurueck.
            extra_notice:
            Optionaler zusaetzlicher Absatz fuer Werkzeuge mit weitergehenden
            Risiken (z.B. solche, die Formulare tatsaechlich absenden).
            author:
            Rechteinhaber; wird im Haftungsabsatz benannt, damit erkennbar ist,
            wer die Haftung ausschliesst.
            footer:
            Herkunftszeile am Fuss des Dialogs (z.B. Version, Copyright, Repo).
            title:
            Abweichende Ueberschrift; leer = Standardtext der Sprache.
            intro:
            Abweichender Einleitungsabsatz. Der Standardtext beschreibt Last
            durch automatisierte Seitenabrufe - fuer Werkzeuge, die etwas
            anderes tun (z.B. Datensaetze in einem Fremdsystem anlegen), gehoert
            hier eine passende Beschreibung hin.
            duties:
            Abweichende Zusicherungen ohne Nummerierung; die Nummern setzt der
            Dialog. None = Standardliste der Sprache.

        Nicht austauschbar ist bewusst der Haftungsabsatz: er ist der
        rechtlich durchdachte Teil und soll ueber alle Werkzeuge hinweg
        gleich lauten.
        """
        super().__init__()
        self._app_name = app_name
        self._lang = lang if lang in _TEXT else "en"
        self._extra_notice = extra_notice
        self._author = author
        self._footer = footer
        self._title = title
        self._intro = intro
        self._duties = duties if duties is not None else _DUTIES[self._lang]

    def _t(self, key: str) -> str:
        """Liefert den Text zum Schluessel in der gewaehlten Sprache."""
        return _TEXT[self._lang][key]

    def compose(self) -> ComposeResult:
        # Der ganze Kasten scrollt, nicht nur der Textteil: so entsteht bei viel
        # Platz kein Leerraum ueber den Bedienelementen, und bei wenig Platz
        # bleiben Haken und Schaltflaechen trotzdem erreichbar.
        with VerticalScroll(id="disclaimer-box"):
            # Versalien statt Schriftgroesse: das Terminal kennt nur eine Zellgroesse,
            # Gewicht und Sperrung sind die einzigen Mittel fuer Rangfolge.
            yield Label((self._title or self._t("title")).upper(), id="disclaimer-title")
            if self._app_name:
                yield Static(self._app_name, id="disclaimer-app")
            with Vertical(id="disclaimer-body"):
                yield Static(self._intro or self._t("intro"), classes="disclaimer-para")
                if self._extra_notice:
                    yield Static(self._extra_notice, classes="disclaimer-para")
                yield Static(self._t("duties_title"))
                for number, duty in enumerate(self._duties, start=1):
                    yield Static(f"{number}. {duty}", classes="disclaimer-duty")
                # Trennt die Zusicherungen des Nutzers vom Haftungsausschluss des
                # Autors - zwei verschiedene Aussagen, die nicht ineinander laufen sollen.
                yield Rule(line_style="heavy")
                yield Static(_liability(_TEXT[self._lang], self._author), classes="disclaimer-para")
            yield Checkbox(self._t("checkbox"), value=False, id="disclaimer-agree")
            with Horizontal(id="disclaimer-buttons"):
                yield Button(self._t("quit"), variant="default", id="disclaimer-quit")
                yield Button(
                    self._t("accept"),
                    variant="primary",
                    id="disclaimer-accept",
                    disabled=True,
                )
            yield Static(self._t("hint"), id="disclaimer-hint")
            if self._footer:
                yield Static(self._footer, id="disclaimer-footer")

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Gibt den Bestaetigen-Knopf erst nach dem Setzen des Hakens frei."""
        self.query_one("#disclaimer-accept", Button).disabled = not event.value

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Wertet Bestaetigen/Beenden aus."""
        self.dismiss(event.button.id == "disclaimer-accept")

    def action_refuse(self) -> None:
        """Esc gilt als Ablehnung - Zustimmung muss aktiv erfolgen."""
        self.dismiss(False)
