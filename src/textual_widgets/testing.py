"""Test-Helpers fuer Textual-Pilot-basierte UI-Tests.

Zwei Hilfsfunktionen fuer den Umgang mit async UI-Verhalten in pytest-Tests:

- ``iter_until`` — pollt eine Bedingung bis True oder Timeout. Nuetzlich
  fuer "warte bis das Widget den Zustand X erreicht hat".
- ``workers_finished`` — wartet bis alle ``@work``-Worker eines bestimmten
  Widgets fertig sind. Nuetzlich vor Assertions, die das Ergebnis eines
  Workers pruefen.

Usage:

    import pytest
    from textual_widgets.testing import iter_until, workers_finished
    from myapp import MyApp

    @pytest.mark.asyncio
    async def test_search_finds_results() -> None:
        async with MyApp().run_test() as pilot:
            await pilot.click("#search-input")
            await pilot.press("a")
            await workers_finished(pilot, "#search")
            search = pilot.app.query_one("#search")
            await iter_until(pilot, lambda: len(search.results) > 0)
            assert search.results[0].title == "Apple"

Beide Funktionen werfen ``AssertionError`` wenn das Timeout erreicht ist.
Default-Timeout: 2 Sekunden, Default-Interval: 100 ms.

Inspiriert von NSPC911/rovr's ``tests/conftest.py``.
"""

from __future__ import annotations

from collections.abc import Callable

from textual.dom import DOMNode
from textual.pilot import Pilot


async def iter_until(
    pilot: Pilot,
    condition: Callable[[], bool],
    timeout: float = 2.0,  # noqa: ASYNC109 - timeout is part of the public API
    interval: float = 0.1,
) -> None:
    """Pollt eine Bedingung bis sie True liefert oder das Timeout abgelaufen ist.

    Args:
        pilot: Das ``Pilot``-Objekt aus ``app.run_test()``. Wird fuer
            ``pilot.pause(interval)`` benoetigt, damit Textual zwischen
            Polls einen Event-Loop-Tick bekommt.
        condition: Callable ohne Argumente. Gibt ``True`` zurueck wenn
            die erwartete Bedingung eingetreten ist.
        timeout: Maximale Wartezeit in Sekunden. Default: 2.0.
        interval: Wartezeit zwischen Polls in Sekunden. Default: 0.1.

    Raises:
        AssertionError: Wenn ``condition()`` nicht innerhalb von
            ``timeout`` Sekunden ``True`` liefert.
    """
    for _ in range(int(timeout / interval)):
        await pilot.pause(interval)
        if condition():
            return
    assert condition()


async def workers_finished(
    pilot: Pilot,
    target: DOMNode | str,
    timeout: float = 2.0,  # noqa: ASYNC109 - timeout is part of the public API
    interval: float = 0.1,
) -> None:
    """Wartet bis alle laufenden Worker eines Widgets beendet sind.

    Args:
        pilot: Das ``Pilot``-Objekt aus ``app.run_test()``.
        target: Widget-Instanz oder CSS-Selektor (z.B. ``"#search"``).
        timeout: Maximale Wartezeit in Sekunden. Default: 2.0.
        interval: Wartezeit zwischen Polls in Sekunden. Default: 0.1.

    Raises:
        AssertionError: Wenn nach ``timeout`` Sekunden immer noch Worker
            am Widget laufen.
    """
    widget: DOMNode = pilot.app.query_one(target) if isinstance(target, str) else target

    def all_done() -> bool:
        return not any(w for w in pilot.app.workers if w.node == widget and w.is_running)

    for _ in range(int(timeout / interval)):
        await pilot.pause(interval)
        if all_done():
            return
    assert all_done()
