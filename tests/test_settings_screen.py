"""Tests fuer BaseSettingsScreen."""

from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.widgets import Checkbox, Static, TabPane

from textual_widgets import BaseSettingsScreen, LogPanel, LogRouter


class _DemoSettings(BaseSettingsScreen):
    """Test-Subklasse mit einem eigenen Tab."""

    def app_tabs(self) -> ComposeResult:
        with TabPane("Demo", id="tab-demo"):
            yield Checkbox("Feature X", value=False, id="set-x")

    def collect_app_settings(self, settings: dict[str, object]) -> None:
        settings["feature_x"] = self.query_one("#set-x", Checkbox).value


class _SettingsApp(LogRouter, App[None]):
    """Test-App mit LogPanel (fuer den LogRouter)."""

    def compose(self) -> ComposeResult:
        yield LogPanel(id="log")


class TestBaseSettingsScreen:
    def test_settings_copied(self) -> None:
        original = {"language": "de"}
        screen = _DemoSettings(original)
        screen._settings["language"] = "en"
        assert original["language"] == "de"

    def test_unknown_lang_falls_back(self) -> None:
        assert _DemoSettings({}, lang="xx")._lang == "en"

    async def test_save_returns_settings_dict(self) -> None:
        app = _SettingsApp()
        result: list[dict[str, object] | None] = []
        async with app.run_test() as pilot:
            app.push_screen(_DemoSettings({"language": "de"}, lang="de"), callback=result.append)
            await pilot.pause()
            await pilot.press("ctrl+s")
            await pilot.pause()
        assert result and result[0] is not None
        assert result[0]["language"] == "de"
        assert result[0]["feature_x"] is False

    async def test_cancel_returns_none(self) -> None:
        app = _SettingsApp()
        result: list[dict[str, object] | None] = []
        async with app.run_test() as pilot:
            app.push_screen(_DemoSettings({"language": "de"}, lang="de"), callback=result.append)
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()
        assert result == [None]

    async def test_language_value_preserved(self) -> None:
        app = _SettingsApp()
        result: list[dict[str, object] | None] = []
        async with app.run_test() as pilot:
            app.push_screen(_DemoSettings({"language": "en"}, lang="en"), callback=result.append)
            await pilot.pause()
            await pilot.press("ctrl+s")
            await pilot.pause()
        assert result[0] is not None
        assert result[0]["language"] == "en"

    async def test_save_posts_log_message(self) -> None:
        app = _SettingsApp()
        async with app.run_test() as pilot:
            app.push_screen(_DemoSettings({"language": "de"}, lang="de"))
            await pilot.pause()
            await pilot.press("ctrl+s")
            await pilot.pause()
            panel = app.query_one(LogPanel)
            assert any("gespeichert" in line for line in panel._lines)

    async def test_storage_tab_absent_by_default(self) -> None:
        app = _SettingsApp()
        async with app.run_test() as pilot:
            app.push_screen(_DemoSettings({"language": "de"}, lang="de"))
            await pilot.pause()
            # Kein storage_paths()-Override → kein Tab.
            assert len(app.screen.query("#settings-tab-storage")) == 0


class _StorageSettings(BaseSettingsScreen):
    """Test-Subklasse mit storage_paths()-Override."""

    def __init__(self, paths: list[tuple[str, Path]]) -> None:
        super().__init__({"language": "de"}, lang="de")
        self._paths = paths

    def storage_paths(self) -> list[tuple[str, Path]]:
        return self._paths


class TestStorageTab:
    async def test_storage_tab_renders_paths(self, tmp_path: Path) -> None:
        f = tmp_path / "settings.json"
        f.write_text("{}", encoding="utf-8")
        cache = tmp_path / "cache"
        cache.mkdir()

        app = _SettingsApp()
        async with app.run_test() as pilot:
            screen = _StorageSettings([("Settings", f), ("Cache", cache)])
            app.push_screen(screen)
            await pilot.pause()
            statics = list(screen.query(".storage-path").results(Static))
            assert len(statics) == 2
            # Map ist konsistent zur Reihenfolge.
            ids = [s.id for s in statics]
            assert screen._storage_click_map[ids[0]] == f
            assert screen._storage_click_map[ids[1]] == cache

    async def test_storage_tab_empty_list_no_tab(self) -> None:
        app = _SettingsApp()
        async with app.run_test() as pilot:
            screen = _StorageSettings([])
            app.push_screen(screen)
            await pilot.pause()
            assert len(screen.query("#settings-tab-storage")) == 0
