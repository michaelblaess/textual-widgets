"""Tests fuer LogMessage, LogPanel und LogRouter."""

from __future__ import annotations

import glob
import os
from pathlib import Path

from textual.app import App, ComposeResult
from textual.widgets import Static

from textual_widgets import LogMessage, LogPanel, LogRouter


class _LogApp(LogRouter, App[None]):
    """Test-App mit LogPanel und einem Kind-Widget."""

    def compose(self) -> ComposeResult:
        yield Static("child", id="child")
        yield LogPanel(lang="de", export_name="test-tool", id="log")


class TestLogMessage:
    def test_default_level(self) -> None:
        assert LogMessage("x").level == "info"

    def test_unknown_level_falls_back(self) -> None:
        assert LogMessage("x", "bogus").level == "info"

    def test_factory_methods(self) -> None:
        assert LogMessage.success("a").level == "success"
        assert LogMessage.warning("b").level == "warning"
        assert LogMessage.error("c").level == "error"
        assert LogMessage.debug("d").level == "debug"
        assert LogMessage.info("e").level == "info"

    def test_text_stored(self) -> None:
        assert LogMessage.error("kaputt").text == "kaputt"


class TestLogPanel:
    async def test_write_log_appends_plain_mirror(self) -> None:
        async with _LogApp().run_test() as pilot:
            panel = pilot.app.query_one(LogPanel)
            panel.write_log("hello world", "info")
            assert len(panel._lines) == 1
            assert "hello world" in panel._lines[0]

    async def test_write_log_strips_markup_in_mirror(self) -> None:
        async with _LogApp().run_test() as pilot:
            panel = pilot.app.query_one(LogPanel)
            panel.write_log("[bold]important[/bold]", "warning")
            assert "[bold]" not in panel._lines[0]
            assert "important" in panel._lines[0]

    async def test_clear_log(self) -> None:
        async with _LogApp().run_test() as pilot:
            panel = pilot.app.query_one(LogPanel)
            panel.write_log("a")
            panel.clear_log()
            assert panel._lines == []

    async def test_hide_show_toggle(self) -> None:
        async with _LogApp().run_test() as pilot:
            panel = pilot.app.query_one(LogPanel)
            panel.hide()
            assert panel.has_class("-log-hidden")
            panel.show()
            assert not panel.has_class("-log-hidden")
            panel.toggle()
            assert panel.has_class("-log-hidden")

    async def test_export_writes_file(self) -> None:
        async with _LogApp().run_test() as pilot:
            panel = pilot.app.query_one(LogPanel)
            panel.write_log("line one")
            panel.export_log()
            await pilot.pause()
            files = sorted(glob.glob(str(Path.home() / "test-tool-log-*.txt")))
            assert files
            content = Path(files[-1]).read_text(encoding="utf-8")
            assert "line one" in content
            os.remove(files[-1])


class TestLogRouter:
    async def test_routes_message_to_panel(self) -> None:
        async with _LogApp().run_test() as pilot:
            pilot.app.post_message(LogMessage.success("routed"))
            await pilot.pause()
            panel = pilot.app.query_one(LogPanel)
            assert any("routed" in line for line in panel._lines)

    async def test_routes_message_bubbled_from_child(self) -> None:
        async with _LogApp().run_test() as pilot:
            child = pilot.app.query_one("#child", Static)
            child.post_message(LogMessage.error("from child"))
            await pilot.pause()
            panel = pilot.app.query_one(LogPanel)
            assert any("from child" in line for line in panel._lines)
