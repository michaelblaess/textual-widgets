"""Tests fuer textual_widgets.testing Helpers."""

from __future__ import annotations

import asyncio

import pytest
from textual import work
from textual.app import App, ComposeResult
from textual.widgets import Static

from textual_widgets.testing import iter_until, workers_finished


class _CounterApp(App):
    """Test-App die einen Zaehler ueber einen Timer hochzaehlt."""

    counter: int = 0

    def compose(self) -> ComposeResult:
        yield Static("dummy", id="dummy")

    def on_mount(self) -> None:
        self.set_interval(0.05, self._tick)

    def _tick(self) -> None:
        self.counter += 1


class _WorkerApp(App):
    """Test-App mit einem @work-Worker am Static-Widget."""

    worker_done: bool = False

    def compose(self) -> ComposeResult:
        yield Static("dummy", id="dummy")

    def on_mount(self) -> None:
        self._run_long_job()

    @work
    async def _run_long_job(self) -> None:
        await asyncio.sleep(0.2)
        self.worker_done = True


class TestIterUntil:
    async def test_succeeds_when_condition_becomes_true(self) -> None:
        async with _CounterApp().run_test() as pilot:
            app = pilot.app
            assert isinstance(app, _CounterApp)
            await iter_until(pilot, lambda: app.counter >= 2, timeout=1.0)
            assert app.counter >= 2

    async def test_raises_assertion_on_timeout(self) -> None:
        async with _CounterApp().run_test() as pilot:
            with pytest.raises(AssertionError):
                await iter_until(pilot, lambda: False, timeout=0.2, interval=0.05)

    async def test_returns_immediately_if_already_true(self) -> None:
        async with _CounterApp().run_test() as pilot:
            await iter_until(pilot, lambda: True, timeout=0.1)


class TestWorkersFinished:
    async def test_waits_for_worker_to_complete(self) -> None:
        async with _WorkerApp().run_test() as pilot:
            app = pilot.app
            assert isinstance(app, _WorkerApp)
            await workers_finished(pilot, app, timeout=1.0)
            assert app.worker_done is True

    async def test_returns_when_no_workers_at_all(self) -> None:
        async with _CounterApp().run_test() as pilot:
            dummy = pilot.app.query_one("#dummy")
            await workers_finished(pilot, dummy, timeout=0.2)

    async def test_accepts_selector_string(self) -> None:
        async with _CounterApp().run_test() as pilot:
            await workers_finished(pilot, "#dummy", timeout=0.2)
