"""Tests fuer TerminalImage.

WAS SICH HIER NICHT PRUEFEN LAESST: ob TGP oder Sixel im echten Terminal
sichtbar werden. Das haengt am Terminal, nicht am Code - headless gibt es
keins. Geprueft wird deshalb die Protokollerkennung (reine Funktion der
Umgebungsvariablen) und der Halbblock-Weg, der ueberall traegt.
"""

from __future__ import annotations

import io

import pytest
from textual.app import App, ComposeResult

from textual_widgets import TerminalImage, als_halbbloecke, erkenne_protokoll
from textual_widgets.terminal_image import HALBBLOCK

PIL = pytest.importorskip("PIL.Image", reason="Extra 'images' nicht installiert")


def _bild(breite: int = 40, hoehe: int = 20, farbe: tuple[int, int, int] = (200, 30, 30)) -> bytes:
    puffer = io.BytesIO()
    PIL.new("RGB", (breite, hoehe), farbe).save(puffer, format="PNG")
    return puffer.getvalue()


class TestProtokollerkennung:
    def test_windows_terminal_bekommt_sixel(self, monkeypatch: pytest.MonkeyPatch) -> None:
        for name in ("KITTY_WINDOW_ID", "KONSOLE_VERSION", "TERM", "TERM_PROGRAM"):
            monkeypatch.delenv(name, raising=False)
        monkeypatch.setenv("WT_SESSION", "irgendeine-kennung")
        assert erkenne_protokoll() == "sixel"

    def test_kitty_bekommt_tgp(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("KITTY_WINDOW_ID", "1")
        assert erkenne_protokoll() == "tgp"

    def test_unbekanntes_terminal_bekommt_nichts(self, monkeypatch: pytest.MonkeyPatch) -> None:
        for name in ("KITTY_WINDOW_ID", "KONSOLE_VERSION", "WT_SESSION", "TERM_PROGRAM"):
            monkeypatch.delenv(name, raising=False)
        monkeypatch.setenv("TERM", "dumb")
        assert erkenne_protokoll() is None


class TestHalbbloecke:
    def test_zwei_bildpunkte_je_zeile(self) -> None:
        """20 Punkte hoch ergeben 10 Zeilen - jedes Zeichen traegt zwei."""
        zeilen = als_halbbloecke(_bild(40, 20), breite=40, hoehe=10)
        assert len(zeilen) == 10
        assert len(zeilen[0].plain) == 40

    def test_passt_sich_der_breite_an(self) -> None:
        schmal = als_halbbloecke(_bild(40, 20), breite=10, hoehe=10)
        assert all(len(z.plain) <= 10 for z in schmal)

    def test_farbe_landet_im_stil(self) -> None:
        zeilen = als_halbbloecke(_bild(4, 4, (200, 30, 30)), breite=4, hoehe=2)
        stile = str(zeilen[0].spans[0].style)
        assert "200,30,30" in stile.replace(" ", "")

    def test_defekte_daten_stuerzen_nicht_ab(self) -> None:
        zeilen = als_halbbloecke(b"kein Bild", breite=20, hoehe=10)
        assert len(zeilen) == 1
        assert "nicht lesbar" in zeilen[0].plain


class _Testapp(App[None]):
    def __init__(self, daten: bytes | None) -> None:
        super().__init__()
        self._daten = daten

    def compose(self) -> ComposeResult:
        yield TerminalImage(self._daten, modus=HALBBLOCK, id="bild")


class TestWidget:
    async def test_zeigt_ein_bild_an(self) -> None:
        async with _Testapp(_bild()).run_test(size=(60, 24)) as pilot:
            await pilot.pause()
            bild = pilot.app.query_one("#bild", TerminalImage)
            # Im erzwungenen Halbblock-Modus darf kein Protokoll gesetzt sein.
            assert bild.protokoll is None

    async def test_ohne_bild_kein_absturz(self) -> None:
        async with _Testapp(None).run_test(size=(60, 24)) as pilot:
            await pilot.pause()
            assert pilot.app.query_one("#bild", TerminalImage) is not None
