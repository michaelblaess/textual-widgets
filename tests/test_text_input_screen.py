"""Tests fuer TextInputScreen."""

from __future__ import annotations

import pytest

from textual_widgets import TextInputScreen


class TestConstruction:
    def test_title_stored(self) -> None:
        assert TextInputScreen(title="Pick a name")._title == "Pick a name"

    def test_prompt_default_empty(self) -> None:
        assert TextInputScreen(title="X")._prompt == ""

    def test_prompt_stored(self) -> None:
        assert TextInputScreen(title="X", prompt="Hint:")._prompt == "Hint:"

    def test_initial_default_empty(self) -> None:
        assert TextInputScreen(title="X")._initial == ""

    def test_initial_stored(self) -> None:
        assert TextInputScreen(title="X", initial="seed")._initial == "seed"

    def test_placeholder_stored(self) -> None:
        assert TextInputScreen(title="X", placeholder="ph")._placeholder == "ph"

    def test_validator_stored(self) -> None:
        v = lambda s: None  # noqa: E731
        assert TextInputScreen(title="X", validator=v)._validator is v

    def test_default_lang_english(self) -> None:
        assert TextInputScreen(title="X")._lang == "en"

    def test_german_lang(self) -> None:
        assert TextInputScreen(title="X", lang="de")._lang == "de"

    def test_unknown_lang_falls_back(self) -> None:
        assert TextInputScreen(title="X", lang="xx")._lang == "en"


class TestCheck:
    def test_no_validator_empty_rejected_english(self) -> None:
        screen = TextInputScreen(title="X")
        assert screen._check("") == "Please enter a value."

    def test_no_validator_empty_rejected_german(self) -> None:
        screen = TextInputScreen(title="X", lang="de")
        assert screen._check("") == "Bitte einen Text eingeben."

    def test_no_validator_text_accepted(self) -> None:
        assert TextInputScreen(title="X")._check("hello") is None

    def test_validator_called_with_text(self) -> None:
        received: list[str] = []

        def validator(s: str) -> str | None:
            received.append(s)
            return None

        TextInputScreen(title="X", validator=validator)._check("input")
        assert received == ["input"]

    def test_validator_error_propagated(self) -> None:
        screen = TextInputScreen(title="X", validator=lambda s: "no good")
        assert screen._check("anything") == "no good"

    def test_validator_overrides_default_empty_check(self) -> None:
        """Mit Validator wird Leerstring nicht mehr automatisch abgelehnt."""
        screen = TextInputScreen(title="X", validator=lambda s: None)
        assert screen._check("") is None


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("name", None),
        ("  ", "empty"),
        ("", "empty"),
    ],
)
def test_custom_validator_signals_emptiness(text: str, expected: str | None) -> None:
    screen = TextInputScreen(
        title="X",
        validator=lambda s: "empty" if not s.strip() else None,
    )
    assert screen._check(text.strip()) == expected
