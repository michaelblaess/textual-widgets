"""Tests fuer DisclaimerScreen und DisclaimerStore."""

from __future__ import annotations

import json
from pathlib import Path

from textual.app import App, ComposeResult
from textual.widgets import Button, Checkbox, Static

from textual_widgets import (
    DISCLAIMER_VERSION,
    DisclaimerScreen,
    DisclaimerStore,
    disclaimer_text,
)


class _Host(App[None]):
    """Minimal-App, die den Hinweis zeigt und die Antwort festhaelt."""

    def __init__(
        self,
        lang: str = "de",
        extra_notice: str = "",
        footer: str = "",
        intro: str = "",
        duties: tuple[str, ...] | None = None,
    ) -> None:
        super().__init__()
        self.answer: bool | None = None
        self._lang = lang
        self._extra_notice = extra_notice
        self._footer = footer
        self._intro = intro
        self._duties = duties

    def compose(self) -> ComposeResult:
        return iter(())

    def on_mount(self) -> None:
        self.push_screen(
            DisclaimerScreen(
                app_name="test-tool",
                lang=self._lang,
                extra_notice=self._extra_notice,
                footer=self._footer,
                intro=self._intro,
                duties=self._duties,
            ),
            callback=self._record,
        )

    def _record(self, accepted: bool | None) -> None:
        self.answer = accepted


class TestConstruction:
    def test_default_lang_english(self) -> None:
        assert DisclaimerScreen()._lang == "en"

    def test_german_lang(self) -> None:
        assert DisclaimerScreen(lang="de")._lang == "de"

    def test_unknown_lang_falls_back(self) -> None:
        assert DisclaimerScreen(lang="xx")._lang == "en"

    def test_app_name_stored(self) -> None:
        assert DisclaimerScreen(app_name="scanner")._app_name == "scanner"


class TestPlainText:
    def test_author_is_named_in_the_liability_clause(self) -> None:
        assert "des Autors (Michael Blaess)" in disclaimer_text("de", author="Michael Blaess")

    def test_author_is_named_in_english_too(self) -> None:
        assert "the author (Michael Blaess)" in disclaimer_text("en", author="Michael Blaess")

    def test_without_author_no_empty_brackets(self) -> None:
        text = disclaimer_text("de")
        assert "des Autors für Schäden" in text
        assert "()" not in text

    def test_blank_author_is_treated_as_missing(self) -> None:
        assert "()" not in disclaimer_text("de", author="   ")

    def test_unknown_lang_falls_back_to_english(self) -> None:
        assert disclaimer_text("xx") == disclaimer_text("en")


class TestCustomWording:
    """Anwendungen mit anderem Einsatzzweck muessen den Text anpassen koennen."""

    def test_custom_intro_replaces_default(self) -> None:
        text = disclaimer_text("de", intro="Dieses Programm legt Vorgänge in Jira an.")
        assert "Dieses Programm legt Vorgänge in Jira an." in text
        assert "ruft Webseiten automatisiert ab" not in text

    def test_custom_title_replaces_default(self) -> None:
        assert disclaimer_text("de", title="Bitte lesen").startswith("Bitte lesen")

    def test_custom_duties_are_numbered_automatically(self) -> None:
        text = disclaimer_text("de", duties=("Erste Zusage.", "Zweite Zusage."))
        assert "1. Erste Zusage." in text
        assert "2. Zweite Zusage." in text

    def test_custom_duties_replace_all_defaults(self) -> None:
        text = disclaimer_text("de", duties=("Nur diese eine.",))
        assert "3." not in text
        assert "Berechtigung des Betreibers" not in text

    def test_empty_duties_tuple_drops_the_list(self) -> None:
        text = disclaimer_text("de", duties=())
        assert "1." not in text

    def test_liability_clause_stays_fixed(self) -> None:
        """Der Haftungsabsatz ist bewusst nicht austauschbar."""
        text = disclaimer_text("de", title="X", intro="Y", duties=("Z",))
        assert "Produkthaftungsgesetz" in text
        assert "Apache-Lizenz 2.0" in text

    async def test_custom_wording_reaches_the_dialog(self) -> None:
        app = _Host(intro="Dieses Programm legt Vorgänge an.", duties=("Einzige Zusage.",))
        async with app.run_test() as pilot:
            await pilot.pause()
            rendered = " ".join(str(widget.render()) for widget in app.screen.query(Static))
            assert "Dieses Programm legt Vorgänge an." in rendered
            assert "1. Einzige Zusage." in rendered


class TestStore:
    def test_missing_file_means_no_consent(self, tmp_path: Path) -> None:
        assert DisclaimerStore(tmp_path / "none.json").accepted_version is None

    def test_broken_file_means_no_consent(self, tmp_path: Path) -> None:
        path = tmp_path / "broken.json"
        path.write_text("kein JSON", encoding="utf-8")
        assert DisclaimerStore(path).accepted_version is None

    def test_record_then_read_back(self, tmp_path: Path) -> None:
        store = DisclaimerStore(tmp_path / "sub" / "disclaimer.json")
        store.record()
        assert store.accepted_version == DISCLAIMER_VERSION

    def test_record_writes_timestamp(self, tmp_path: Path) -> None:
        path = tmp_path / "disclaimer.json"
        DisclaimerStore(path).record()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["accepted_at"]

    def test_old_version_is_reported_as_is(self, tmp_path: Path) -> None:
        """Eine alte Fassung fuehrt beim Aufrufer zur erneuten Abfrage."""
        path = tmp_path / "disclaimer.json"
        DisclaimerStore(path).record(version="1999-01-01")
        assert DisclaimerStore(path).accepted_version == "1999-01-01"


class TestInteraction:
    async def test_accept_disabled_until_checkbox_ticked(self) -> None:
        app = _Host()
        async with app.run_test() as pilot:
            await pilot.pause()
            assert app.screen.query_one("#disclaimer-accept", Button).disabled is True

    async def test_checkbox_enables_accept(self) -> None:
        app = _Host()
        async with app.run_test() as pilot:
            await pilot.pause()
            app.screen.query_one("#disclaimer-agree", Checkbox).value = True
            await pilot.pause()
            assert app.screen.query_one("#disclaimer-accept", Button).disabled is False

    async def test_accept_returns_true(self) -> None:
        app = _Host()
        async with app.run_test() as pilot:
            await pilot.pause()
            app.screen.query_one("#disclaimer-agree", Checkbox).value = True
            await pilot.pause()
            app.screen.query_one("#disclaimer-accept", Button).press()
            await pilot.pause()
            assert app.answer is True

    async def test_quit_button_returns_false(self) -> None:
        app = _Host()
        async with app.run_test() as pilot:
            await pilot.pause()
            app.screen.query_one("#disclaimer-quit", Button).press()
            await pilot.pause()
            assert app.answer is False

    async def test_escape_counts_as_refusal(self) -> None:
        """Wegdruecken darf niemals als Zustimmung gewertet werden."""
        app = _Host()
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()
            assert app.answer is False

    async def test_footer_is_rendered_when_given(self) -> None:
        app = _Host(footer="tool 1.0 · © 2026 Michael Blaess")
        async with app.run_test() as pilot:
            await pilot.pause()
            footer = app.screen.query_one("#disclaimer-footer")
            assert "Michael Blaess" in str(footer.render())

    async def test_no_footer_element_without_text(self) -> None:
        app = _Host()
        async with app.run_test() as pilot:
            await pilot.pause()
            assert not app.screen.query("#disclaimer-footer")

    async def test_extra_notice_is_rendered(self) -> None:
        app = _Host(extra_notice="Dieses Werkzeug sendet Formulare tatsächlich ab.")
        async with app.run_test() as pilot:
            await pilot.pause()
            texts = [str(w.render()) for w in app.screen.query(".disclaimer-para")]
            assert any("Formulare tatsächlich ab" in text for text in texts)
