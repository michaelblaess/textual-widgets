"""Einzeilige Kennzahlenleiste mit Rahmen und Trennern.

WARUM EIN EIGENES WIDGET UND NICHT ``InfoHeader``: Der InfoHeader rendert ein
Spaltenraster mit fester ``label_width`` - das spreizt Label und Wert
auseinander und taugt fuer eine kompakte Inline-Zeile nicht. Genau deshalb
hatte jira-timesheet ein eigenes SummaryPanel, death-proof eine zweite und
claude-sanctuary eine dritte Fassung, alle leicht verschieden. Diese Klasse
loest das an einer Stelle.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from rich.text import Text
from textual.widgets import Static

TRENNER = "  |  "
"""Vorgabe-Trenner zwischen zwei Angaben."""


@dataclass(frozen=True)
class StatusItem:
    """Eine Angabe in der Leiste.

    Attributes:
        label:
            Beschriftung links, gedimmt dargestellt. Leer lassen fuer einen
            reinen Wert ohne Beschriftung.
        value:
            Der Wert. Wird fett gesetzt, sofern kein eigener Stil angegeben ist.
        value_style:
            Optionaler Rich-Stil fuer den Wert, etwa ``"bold red"``.
        label_style:
            Optionaler Rich-Stil fuer die Beschriftung.
    """

    label: str
    value: str
    value_style: str = "bold"
    label_style: str = "dim"


class StatusBar(Static):
    """Eine Zeile Kennzahlen, umrandet, mit Trennern zwischen den Angaben.

    Die Hoehe ist ``auto`` mit ``min-height: 1``: der Rahmen braucht zwei
    Zeilen mehr, und ein fester Wert wuerde bei laengerem Inhalt abschneiden.
    """

    DEFAULT_CSS = """
    StatusBar {
        height: auto;
        min-height: 1;
        padding: 0 1;
        background: $surface;
        border: solid $accent;
    }
    """

    def __init__(
        self,
        items: Sequence[StatusItem] | None = None,
        *,
        separator: str = TRENNER,
        hint: str = "",
        **kwargs: Any,
    ) -> None:
        """Legt die Leiste an.

        Args:
            items: Angaben, die sofort erscheinen sollen.
            separator: Trenner zwischen zwei Angaben.
            hint: Text, der erscheint, solange keine Angaben gesetzt sind.
        """
        super().__init__("", **kwargs)
        self._items: list[StatusItem] = list(items or [])
        self._separator = separator
        self._hint = hint

    def on_mount(self) -> None:
        self._redraw()

    # -- oeffentlich ----------------------------------------------------

    def set_items(self, items: Sequence[StatusItem]) -> None:
        """Ersetzt alle Angaben."""
        self._items = list(items)
        self._redraw()

    def set_hint(self, text: str) -> None:
        """Setzt den Text fuer den Zustand ohne Angaben."""
        self._hint = text
        if not self._items:
            self._redraw()

    def clear(self) -> None:
        """Entfernt alle Angaben, der Hinweistext erscheint wieder."""
        self._items = []
        self._redraw()

    # -- intern ---------------------------------------------------------

    def _redraw(self) -> None:
        """Baut den Inhalt neu.

        NICHT ``_render`` nennen - das ist eine interne Textual-API, ein
        Override davon bringt das Layout-System zu Fall.
        """
        self.update(self._build())

    def _build(self) -> Text:
        if not self._items:
            return Text(self._hint, style="dim")
        text = Text()
        for i, item in enumerate(self._items):
            if i:
                text.append(self._separator, style="dim")
            if item.label:
                text.append(f"{item.label}: ", style=item.label_style)
            text.append(item.value, style=item.value_style)
        return text
