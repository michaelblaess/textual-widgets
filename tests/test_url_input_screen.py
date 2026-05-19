"""Tests fuer UrlInputScreen."""

from __future__ import annotations

import pytest

from textual_widgets import UrlInputScreen


class TestValidate:
    def test_valid_https_unchanged(self) -> None:
        assert UrlInputScreen._validate("https://example.com") == "https://example.com"

    def test_valid_http_unchanged(self) -> None:
        assert UrlInputScreen._validate("http://example.com") == "http://example.com"

    def test_path_and_query_preserved(self) -> None:
        url = "https://example.com/path?q=1"
        assert UrlInputScreen._validate(url) == url

    def test_missing_scheme_gets_https(self) -> None:
        assert UrlInputScreen._validate("example.com") == "https://example.com"

    def test_surrounding_whitespace_stripped(self) -> None:
        assert UrlInputScreen._validate("  https://example.com  ") == "https://example.com"

    def test_empty_returns_none(self) -> None:
        assert UrlInputScreen._validate("") is None

    def test_whitespace_only_returns_none(self) -> None:
        assert UrlInputScreen._validate("   ") is None

    def test_non_http_scheme_rejected(self) -> None:
        assert UrlInputScreen._validate("ftp://example.com") is None

    def test_scheme_without_host_rejected(self) -> None:
        assert UrlInputScreen._validate("https://") is None

    def test_host_without_dot_rejected(self) -> None:
        assert UrlInputScreen._validate("foo") is None

    def test_localhost_accepted(self) -> None:
        assert UrlInputScreen._validate("localhost") == "https://localhost"

    def test_localhost_with_port_accepted(self) -> None:
        assert UrlInputScreen._validate("http://localhost:8000") == "http://localhost:8000"


class TestUrlInputScreen:
    def test_default_lang_is_english(self) -> None:
        assert UrlInputScreen()._title == "Enter URL"

    def test_german_title(self) -> None:
        assert UrlInputScreen(lang="de")._title == "URL eingeben"

    def test_unknown_lang_falls_back_to_english(self) -> None:
        screen = UrlInputScreen(lang="xx")
        assert screen._lang == "en"
        assert screen._title == "Enter URL"

    def test_initial_value_stored(self) -> None:
        assert UrlInputScreen(initial="https://x.io")._initial == "https://x.io"

    def test_initial_empty_by_default(self) -> None:
        assert UrlInputScreen()._initial == ""

    def test_custom_title(self) -> None:
        assert UrlInputScreen(title="Pick a site")._title == "Pick a site"

    def test_custom_prompt(self) -> None:
        assert UrlInputScreen(prompt="Where to?")._prompt == "Where to?"

    def test_custom_placeholder(self) -> None:
        assert UrlInputScreen(placeholder="https://foo")._placeholder == "https://foo"

    def test_default_prompt_localized(self) -> None:
        assert "http" in UrlInputScreen(lang="de")._prompt
        assert "http" in UrlInputScreen(lang="en")._prompt


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("https://www.michaelblaess.de", "https://www.michaelblaess.de"),
        ("www.michaelblaess.de", "https://www.michaelblaess.de"),
        ("HTTP://Example.COM", "HTTP://Example.COM"),
        ("not a url", None),
        ("javascript:alert(1)", None),
    ],
)
def test_validate_examples(raw: str, expected: str | None) -> None:
    assert UrlInputScreen._validate(raw) == expected
