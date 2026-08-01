"""Tests des ClearableInput."""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.widgets import Input

from textual_widgets import ClearableInput


class _Host(App[None]):
    def compose(self) -> ComposeResult:
        yield ClearableInput(placeholder="Suche", value="Hallo", symbol="X", id="feld")


class TestClearableInput:
    async def test_wert_kommt_durch(self) -> None:
        app = _Host()
        async with app.run_test() as pilot:
            await pilot.pause()
            assert app.query_one("#feld", ClearableInput).value == "Hallo"

    async def test_knopf_leert_das_feld(self) -> None:
        app = _Host()
        async with app.run_test() as pilot:
            await pilot.pause()
            feld = app.query_one("#feld", ClearableInput)
            await pilot.click("#clearable-clear")
            await pilot.pause()
            assert feld.value == ""

    async def test_knopf_meldet_das_leeren(self) -> None:
        gemeldet: list[str] = []

        class _Melder(_Host):
            def on_clearable_input_cleared(self, _e: ClearableInput.Cleared) -> None:
                gemeldet.append("x")

        app = _Melder()
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.click("#clearable-clear")
            for _ in range(10):
                await pilot.pause()
            assert gemeldet == ["x"]

    async def test_clear_meldet_nicht(self) -> None:
        """Der programmatische Weg loest keine Nachricht aus."""
        gemeldet: list[str] = []

        class _Melder(_Host):
            def on_clearable_input_cleared(self, _e: ClearableInput.Cleared) -> None:
                gemeldet.append("x")

        app = _Melder()
        async with app.run_test() as pilot:
            await pilot.pause()
            app.query_one("#feld", ClearableInput).clear()
            for _ in range(10):
                await pilot.pause()
            assert gemeldet == []

    async def test_symbol_ist_austauschbar(self) -> None:
        from textual.widgets import Button

        class _Anderes(App[None]):
            def compose(self) -> ComposeResult:
                yield ClearableInput(symbol="⌫", id="feld")

        app = _Anderes()
        async with app.run_test() as pilot:
            await pilot.pause()
            assert app.query_one("#clearable-clear", Button).label.plain == "⌫"

    async def test_sperren_gilt_fuer_beide(self) -> None:
        from textual.widgets import Button

        app = _Host()
        async with app.run_test() as pilot:
            await pilot.pause()
            feld = app.query_one("#feld", ClearableInput)
            feld.set_disabled(True)
            await pilot.pause()
            assert app.query_one("#clearable-input", Input).disabled
            assert app.query_one("#clearable-clear", Button).disabled
