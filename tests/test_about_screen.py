"""Tests fuer AboutScreen, Quote und load_quotes."""

from __future__ import annotations

import pytest

from textual_widgets import AboutScreen, Quote, load_quotes


class TestQuote:
    def test_fields(self) -> None:
        quote = Quote(text="Hello", author="Someone")
        assert quote.text == "Hello"
        assert quote.author == "Someone"

    def test_is_frozen(self) -> None:
        quote = Quote(text="X", author="Y")
        with pytest.raises(Exception):  # FrozenInstanceError
            quote.text = "Z"  # type: ignore[misc]


class TestLoadQuotes:
    def test_german_pool_not_empty(self) -> None:
        quotes = load_quotes("de")
        assert len(quotes) > 0
        assert all(isinstance(q, Quote) for q in quotes)

    def test_english_pool_not_empty(self) -> None:
        quotes = load_quotes("en")
        assert len(quotes) > 0

    def test_unknown_language_falls_back_to_english(self) -> None:
        assert load_quotes("xx") == load_quotes("en")

    def test_quotes_have_text_and_author(self) -> None:
        for quote in load_quotes("de"):
            assert quote.text
            assert quote.author


class TestAboutScreen:
    def _screen(self, **overrides: object) -> AboutScreen:
        params: dict[str, object] = {
            "app_name": "my-tool",
            "version": "1.2.0",
            "author": "Michael Blaess",
            "release": "2026",
            "description": "A tool.",
            "lang": "en",
        }
        params.update(overrides)
        return AboutScreen(**params)  # type: ignore[arg-type]

    def test_version_v_prefix_stripped(self) -> None:
        screen = self._screen(version="v3.4.5")
        assert screen._version == "3.4.5"

    def test_explicit_quote_used(self) -> None:
        quote = Quote(text="fixed", author="me")
        screen = self._screen(quote=quote)
        assert screen._quote == quote

    def test_custom_quote_pool_used(self) -> None:
        pool = [Quote(text="only", author="one")]
        screen = self._screen(quotes=pool)
        assert screen._quote == pool[0]

    def test_default_quote_from_pool(self) -> None:
        screen = self._screen(lang="de")
        assert screen._quote is not None
        assert screen._quote in load_quotes("de")

    def test_default_footer_localized(self) -> None:
        assert self._screen(lang="de")._footer == "ESC = Schliessen"
        assert self._screen(lang="en")._footer == "ESC = Close"

    def test_custom_footer(self) -> None:
        assert self._screen(footer="Bye")._footer == "Bye"

    def test_unknown_lang_falls_back_to_english_footer(self) -> None:
        assert self._screen(lang="xx")._footer == "ESC = Close"

    def test_no_url_by_default(self) -> None:
        assert self._screen()._url is None

    def test_url_stored(self) -> None:
        url = "https://github.com/michaelblaess/my-tool"
        assert self._screen(url=url)._url == url

    def test_url_widens_dialog(self) -> None:
        short = "https://x.io"
        long = "https://github.com/michaelblaess/some-very-long-repo-name-here"
        assert self._screen(url=long)._dialog_width() >= self._screen(url=short)._dialog_width()

    def test_dialog_width_within_bounds(self) -> None:
        narrow = self._screen(description="hi", quote=Quote("x", "y"))
        assert 44 <= narrow._dialog_width() <= 92

    def test_dialog_width_caps_long_content(self) -> None:
        wide = self._screen(description="x" * 200, quote=Quote("x", "y"))
        assert wide._dialog_width() == 92

    def test_dialog_width_scales_with_content(self) -> None:
        short = self._screen(description="short", quote=Quote("q", "a"))
        long = self._screen(description="a much longer description line here", quote=Quote("q", "a"))
        assert long._dialog_width() >= short._dialog_width()
