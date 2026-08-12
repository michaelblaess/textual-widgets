"""Tests fuer CrashGuard und ErrorScreen."""

from __future__ import annotations

import asyncio

from textual.app import App, ComposeResult
from textual.widgets import Static

from textual_widgets import CrashGuard, ErrorScreen


class _BoomApp(CrashGuard, App[None]):
    """Test-App, die kurz nach dem Mount eine Exception wirft."""

    crash_guard_lang = "de"

    def compose(self) -> ComposeResult:
        yield Static("hi")

    def on_mount(self) -> None:
        self.set_timer(0.05, self._boom)

    def _boom(self) -> None:
        raise RuntimeError("absichtlicher Testfehler")


class TestErrorScreen:
    def test_init_extracts_error_line(self) -> None:
        screen = ErrorScreen(ValueError("kaputt"), "traceback...", lang="de")
        assert screen._error_line == "ValueError: kaputt"
        assert screen._report == "traceback..."

    def test_unknown_lang_falls_back_to_english(self) -> None:
        screen = ErrorScreen(RuntimeError("x"), "tb", lang="xx")
        assert screen._t["title"] == "An error has occurred"

    def test_german_texts(self) -> None:
        screen = ErrorScreen(RuntimeError("x"), "tb", lang="de")
        assert screen._t["quit"] == "Beenden"


class TestCrashGuard:
    async def test_exception_shows_error_screen(self) -> None:
        app = _BoomApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            await asyncio.sleep(0.2)
            await pilot.pause()
            assert isinstance(app.screen, ErrorScreen)

    async def test_continue_keeps_app_running(self) -> None:
        app = _BoomApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            await asyncio.sleep(0.2)
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()
            assert not isinstance(app.screen, ErrorScreen)
            assert app._crash_guard_busy is False

    async def test_report_contains_traceback(self) -> None:
        app = _BoomApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            await asyncio.sleep(0.2)
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, ErrorScreen)
            assert "RuntimeError" in screen._report
            assert "absichtlicher Testfehler" in screen._report


class _MarkupBoomApp(CrashGuard, App[None]):
    """Wirft einen Fehler, dessen Meldung wie rich-Markup aussieht.

    Kein konstruierter Sonderfall: der Satz stammt aus einer Chat-Eingabe und
    hat am 12.08.2026 claude-sanctuary umgebracht. Anschliessend starb dieser
    Fehlerdialog am selben Text ein zweites Mal, weil er die Meldung
    ungeschuetzt in ein Static schrieb.
    """

    crash_guard_lang = "de"

    def compose(self) -> ComposeResult:
        yield Static("hi")

    def on_mount(self) -> None:
        self.set_timer(0.05, self._boom)

    def _boom(self) -> None:
        raise RuntimeError("Stats: [/usage-Screenshot] pruefen")


class TestFremdtextImDialog:
    """Fehlermeldung und Traceback sind Fremdtext, kein Markup."""

    async def test_meldung_mit_eckigen_klammern_bringt_den_dialog_nicht_um(self) -> None:
        app = _MarkupBoomApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            await asyncio.sleep(0.2)
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, ErrorScreen)
            # Erst das Rendern loest den MarkupError aus, nicht das Erzeugen:
            # Textual berechnet die Inhaltshoehe traege. Ohne diesen Aufruf
            # ist der Test gruen, obwohl die App im Terminal abstuerzt.
            for statisch in screen.query(Static):
                statisch._render()

            assert "[/usage-Screenshot]" in screen._error_line

    async def test_traceback_mit_typangaben_bringt_den_dialog_nicht_um(self) -> None:
        """Ein Traceback enthaelt fast immer list[str] oder werte[0]."""
        screen = ErrorScreen(
            ValueError("kaputt"),
            'File "x.py", line 3, in f\n    werte: list[str] = daten[0]\n',
            lang="de",
        )

        class _Huelle(App[None]):
            def on_mount(self) -> None:
                self.push_screen(screen)

        async with _Huelle().run_test() as pilot:
            await pilot.pause()

            for statisch in screen.query(Static):
                statisch._render()
