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
