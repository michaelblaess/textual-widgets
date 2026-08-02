"""Bilder im Terminal anzeigen - mit Grafikprotokoll, sonst als Halbbloecke.

WARUM HIER UND NICHT JE ANWENDUNG: retro-amp zeigt Cover-Art, sanctuary
Bildschirmfotos ferner Rechner. Beide brauchen dieselben drei Dinge - die
Erkennung des Grafikprotokolls, den Rueckfall auf Halbbloecke und die
Vorab-Initialisierung. Dreimal geschrieben liefe das auseinander.

DIE WICHTIGSTE FALLE STEHT IN ``vorab_initialisieren``: textual-image schickt
beim Import Steuersequenzen ans Terminal. Wer das erst nach ``App.run()`` tut,
findet die Antworten des Terminals als Muell in seinen Eingabefeldern wieder.
"""

from __future__ import annotations

import io
import os
from pathlib import Path
from typing import Any

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Container
from textual.widget import Widget
from textual.widgets import Static

OBERER_HALBBLOCK = "▀"
"""Ein Zeichen traegt zwei Bildpunkte: oben die Vorder-, unten die Hintergrundfarbe."""

AUTO = "auto"
HALBBLOCK = "halfblock"
GRAFIK = "graphics"


def erkenne_protokoll() -> str | None:
    """Ermittelt das Grafikprotokoll des Terminals.

    Ausgewertet werden Umgebungsvariablen, weil eine Abfrage am Terminal
    selbst eine Antwort erzeugt, die im falschen Moment in der Eingabe landet.

    :returns: ``"tgp"`` (Kitty-Protokoll), ``"sixel"`` oder None.
    """
    term = os.environ.get("TERM", "").lower()
    programm = os.environ.get("TERM_PROGRAM", "").lower()

    if os.environ.get("KITTY_WINDOW_ID") or "kitty" in term or "ghostty" in term:
        return "tgp"
    if programm in ("wezterm", "ghostty") or os.environ.get("KONSOLE_VERSION"):
        return "tgp"

    # Windows Terminal kann Sixel, aber kein Kitty-Protokoll.
    if os.environ.get("WT_SESSION"):
        return "sixel"
    if term in ("foot", "xterm", "mlterm", "mintty") or "foot" in term:
        return "sixel"
    if programm in ("mintty", "iterm.app"):
        return "sixel"
    return None


def vorab_initialisieren() -> None:
    """Weckt das Grafik-Backend, BEVOR die App das Terminal uebernimmt.

    textual-image sendet beim ersten Import DA1- und Zellgroessen-Abfragen an
    das Terminal. Laeuft das erst waehrend der App, landen die Antworten als
    Zeichenmuell in Eingabefeldern. Deshalb einmal vor ``App.run()`` aufrufen.
    """
    try:
        import textual_image.renderable  # noqa: F401
        import textual_image.widget  # noqa: F401
        from textual_image._terminal import get_cell_size

        get_cell_size()
    except Exception:  # noqa: BLE001 - ohne Backend laeuft der Rueckfall
        pass


def _grafik_klasse(protokoll: str) -> type[Widget] | None:
    """Laedt die Widget-Klasse zum Protokoll, oder None."""
    try:
        if protokoll == "tgp":
            from textual_image.widget import TGPImage

            return TGPImage
        if protokoll == "sixel":
            from textual_image.widget import SixelImage

            return SixelImage
    except ImportError:
        return None
    return None


def als_halbbloecke(daten: bytes, breite: int, hoehe: int) -> list[Text]:
    """Rechnet Bilddaten in farbige Terminalzeilen um.

    :param breite: verfuegbare Spalten.
    :param hoehe: verfuegbare Zeilen - entspricht der doppelten Punktzahl,
        weil jedes Zeichen zwei Bildpunkte uebereinander traegt.
    """
    try:
        from PIL import Image
    except ImportError:
        return [Text("(Pillow nicht installiert)", style="dim")]

    try:
        bild = Image.open(io.BytesIO(daten)).convert("RGB")
    except Exception:  # noqa: BLE001 - defekte Datei ist kein Absturzgrund
        return [Text("(Bild nicht lesbar)", style="dim")]

    quelle_b, quelle_h = bild.size
    if quelle_b <= 0 or quelle_h <= 0 or breite <= 0 or hoehe <= 0:
        return []

    faktor = min(breite / quelle_b, (hoehe * 2) / quelle_h)
    neu_b = max(1, int(quelle_b * faktor))
    neu_h = max(2, int(quelle_h * faktor))
    if neu_h % 2:
        neu_h += 1  # ungerade Punktzahl haette eine halbe Zeile uebrig
    # Resampling.LANCZOS statt Image.LANCZOS: letzteres ist seit Pillow 10 nur
    # noch ein Alias und in den Typstubs nicht mehr enthalten.
    bild = bild.resize((neu_b, neu_h), Image.Resampling.LANCZOS)

    # tobytes() statt getdata(): getdata ist ab Pillow 14 abgekuendigt, und
    # der Nachfolger get_flattened_data gibt es in aelteren Fassungen noch
    # nicht. Rohe Bytes kann jede Version, und sie sind zudem schneller.
    roh = bild.tobytes()
    schritt = neu_b * 3
    zeilen: list[Text] = []
    for y in range(0, neu_h, 2):
        zeile = Text()
        oben = y * schritt
        unten = (y + 1) * schritt
        for x in range(0, schritt, 3):
            zeile.append(
                OBERER_HALBBLOCK,
                style=(
                    f"rgb({roh[oben + x]},{roh[oben + x + 1]},{roh[oben + x + 2]})"
                    f" on rgb({roh[unten + x]},{roh[unten + x + 1]},{roh[unten + x + 2]})"
                ),
            )
        zeilen.append(zeile)
    return zeilen


class TerminalImage(Container):
    """Zeigt ein Bild an - mit Grafikprotokoll, sonst als Halbbloecke.

    Der Modus ``auto`` nimmt das Grafikprotokoll, wenn Terminal und Bibliothek
    es hergeben, und faellt sonst auf Halbbloecke zurueck. Die beiden anderen
    Werte erzwingen den jeweiligen Weg - noetig, weil die Erkennung ueber
    Umgebungsvariablen laeuft und nicht jedes Terminal sich zu erkennen gibt.
    """

    DEFAULT_CSS = """
    TerminalImage {
        width: 100%;
        height: 100%;
        align: center middle;
    }
    TerminalImage > Static {
        width: auto;
        height: auto;
    }
    /* width: auto ist PFLICHT, nicht Geschmack: nur so leitet das
       Grafik-Widget seine Breite aus Hoehe und Seitenverhaeltnis ab. Ohne die
       Regel erbt es die volle Containerbreite, rechnet die Hoehe dazu passend
       aus und rendert zu hoch - das Bild wird unten abgeschnitten, rechts
       bleibt ein schwarzer Streifen. Genau so aufgetreten (02.08.2026). */
    TerminalImage > .terminal-image-grafik {
        width: auto;
        height: 1fr;
    }
    """

    def __init__(self, quelle: str | Path | bytes | None = None, *, modus: str = AUTO, **kwargs: Any) -> None:
        """
        :param quelle: Pfad oder Bilddaten.
        :param modus: ``auto``, ``graphics`` oder ``halfblock``.
        """
        super().__init__(**kwargs)
        self._daten = self._lade(quelle)
        self._modus = modus
        self._protokoll: str | None = None

    @staticmethod
    def _lade(quelle: str | Path | bytes | None) -> bytes | None:
        if quelle is None:
            return None
        if isinstance(quelle, bytes):
            return quelle
        try:
            return Path(quelle).read_bytes()
        except OSError:
            return None

    @property
    def protokoll(self) -> str | None:
        """Welches Grafikprotokoll benutzt wird. None heisst Halbbloecke."""
        return self._protokoll

    def compose(self) -> ComposeResult:
        yield Static(id="bild-inhalt")

    def on_mount(self) -> None:
        self.zeigen(self._daten)

    def zeigen(self, quelle: str | Path | bytes | None) -> None:
        """Tauscht das dargestellte Bild aus."""
        self._daten = self._lade(quelle)
        self._zeichnen()

    def on_resize(self) -> None:
        # Halbbloecke haengen an der Fenstergroesse und muessen neu gerechnet
        # werden. Das Grafikprotokoll skaliert selbst.
        if self._protokoll is None:
            self._zeichnen()

    def _zeichnen(self) -> None:
        ziel = self.query_one("#bild-inhalt", Static)
        if not self._daten:
            ziel.update(Text("(kein Bild)", style="dim"))
            return

        if self._modus != HALBBLOCK:
            protokoll = erkenne_protokoll()
            if protokoll and _grafik_klasse(protokoll) is not None:
                self._protokoll = protokoll
                if self._zeige_grafik(protokoll):
                    return
        self._protokoll = None

        # Zurueck auf Halbbloecke: ein zuvor eingehaengtes Grafik-Widget muss
        # weg und der Platzhalter wieder sichtbar werden.
        self.query("#bild-grafik").remove()
        ziel.display = True

        breite = max(1, self.size.width - 2)
        hoehe = max(1, self.size.height - 1)
        zeilen = als_halbbloecke(self._daten, breite, hoehe)
        inhalt = Text("\n").join(zeilen) if zeilen else Text("(Bild nicht lesbar)", style="dim")
        ziel.update(inhalt)

    def _zeige_grafik(self, protokoll: str) -> bool:
        """Haengt das Grafik-Widget ein. False, wenn es nicht geklappt hat."""
        klasse = _grafik_klasse(protokoll)
        if klasse is None or not self._daten:
            return False
        try:
            from PIL import Image

            bild = Image.open(io.BytesIO(self._daten))
            self.query("#bild-grafik").remove()
            # Den Platzhalter ausblenden statt nur zu leeren: ein leerer
            # Static beansprucht sonst weiter eine Zeile und drueckt das Bild
            # nach unten aus dem Rahmen.
            platzhalter = self.query_one("#bild-inhalt", Static)
            platzhalter.update("")
            platzhalter.display = False
            # TGPImage und SixelImage nehmen ein Bild im Konstruktor, die
            # gemeinsame Oberklasse Widget nicht - der Typ ist hier bewusst
            # weiter als die tatsaechliche Signatur.
            self.mount(
                klasse(bild, id="bild-grafik", classes="terminal-image-grafik")  # type: ignore[arg-type]
            )
            return True
        except Exception:  # noqa: BLE001 - dann eben Halbbloecke
            return False
