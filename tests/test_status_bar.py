"""Tests der StatusBar."""

from __future__ import annotations

from textual.app import App, ComposeResult

from textual_widgets import StatusBar, StatusItem


class _Host(App[None]):
    def __init__(self, **kwargs: object) -> None:
        super().__init__()
        self._kwargs = kwargs

    def compose(self) -> ComposeResult:
        yield StatusBar(id="bar", **self._kwargs)  # type: ignore[arg-type]


class TestAufbau:
    def test_hinweis_solange_keine_angaben(self) -> None:
        leiste = StatusBar(hint="Noch nichts geladen")
        assert leiste._build().plain == "Noch nichts geladen"

    def test_angaben_werden_getrennt(self) -> None:
        leiste = StatusBar([StatusItem("Agenten", "3"), StatusItem("Tokens", "412k")])
        assert leiste._build().plain == "Agenten: 3  |  Tokens: 412k"

    def test_erste_angabe_ohne_fuehrenden_trenner(self) -> None:
        leiste = StatusBar([StatusItem("A", "1")])
        assert not leiste._build().plain.startswith("|")

    def test_angabe_ohne_beschriftung(self) -> None:
        leiste = StatusBar([StatusItem("", "nur der Wert")])
        assert leiste._build().plain == "nur der Wert"

    def test_eigener_trenner(self) -> None:
        leiste = StatusBar([StatusItem("A", "1"), StatusItem("B", "2")], separator=" / ")
        assert leiste._build().plain == "A: 1 / B: 2"


class TestLaufzeit:
    async def test_set_items_ersetzt(self) -> None:
        app = _Host(hint="leer")
        async with app.run_test() as pilot:
            leiste = app.query_one("#bar", StatusBar)
            leiste.set_items([StatusItem("X", "9")])
            await pilot.pause()
            assert leiste._build().plain == "X: 9"

    async def test_clear_zeigt_wieder_den_hinweis(self) -> None:
        app = _Host(hint="leer")
        async with app.run_test() as pilot:
            leiste = app.query_one("#bar", StatusBar)
            leiste.set_items([StatusItem("X", "9")])
            await pilot.pause()
            leiste.clear()
            await pilot.pause()
            assert leiste._build().plain == "leer"

    async def test_hat_einen_rahmen(self) -> None:
        """Der Rahmen ist der Grund fuer dieses Widget - also pruefen."""
        app = _Host()
        async with app.run_test() as pilot:
            await pilot.pause()
            leiste = app.query_one("#bar", StatusBar)
            assert leiste.styles.border.top[0] == "solid"
