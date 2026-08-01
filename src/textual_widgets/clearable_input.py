"""Eingabefeld mit einem Knopf zum Leeren.

Textuals ``Input`` hat dafuer nichts - es kennt nur die Methode ``clear()``.
Wer den Knopf will, baut ihn sonst in jeder Anwendung neu daneben.
"""

from __future__ import annotations

from typing import Any

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widgets import Button, Input

SYMBOL = "X"
"""Vorgabe-Zeichen auf dem Knopf.

Bewusst ein lateinisches X: das Multiplikationszeichen sieht schoener aus,
ist aber mehrdeutig (ruff RUF001) und in manchen Schriften zwei Zellen breit.
"""


class ClearableInput(Horizontal):
    """Ein ``Input`` mit Leeren-Knopf daneben.

    Der Knopf leert das Feld selbst und setzt den Fokus zurueck - wer mehr
    braucht, faengt ``ClearableInput.Cleared`` ab.
    """

    DEFAULT_CSS = """
    ClearableInput {
        height: auto;
    }
    ClearableInput > Input {
        width: 1fr;
    }
    ClearableInput > Button {
        width: 5;
        min-width: 5;
    }
    """

    class Cleared(Message):
        """Das Feld wurde ueber den Knopf geleert."""

        def __init__(self, eingabe: ClearableInput) -> None:
            super().__init__()
            self.eingabe = eingabe

        @property
        def control(self) -> ClearableInput:
            return self.eingabe

    def __init__(
        self,
        *,
        placeholder: str = "",
        value: str = "",
        symbol: str = SYMBOL,
        tooltip: str = "",
        input_id: str = "clearable-input",
        button_id: str = "clearable-clear",
        **kwargs: Any,
    ) -> None:
        """Legt Feld und Knopf an.

        Args:
            placeholder: Platzhaltertext des Eingabefelds.
            value: Anfangswert.
            symbol: Beschriftung des Knopfs, etwa ``"X"`` oder ``"⌫"``.
            tooltip: Hinweis am Knopf.
            input_id: ID des inneren ``Input``.
            button_id: ID des Knopfs.
        """
        super().__init__(**kwargs)
        self._placeholder = placeholder
        self._value = value
        self._symbol = symbol
        self._tooltip = tooltip
        self._input_id = input_id
        self._button_id = button_id

    def compose(self) -> ComposeResult:
        yield Input(placeholder=self._placeholder, value=self._value, id=self._input_id)
        knopf = Button(self._symbol, id=self._button_id)
        # Der Knopf soll den Fokus nicht aus dem Feld ziehen.
        knopf.can_focus = False
        if self._tooltip:
            knopf.tooltip = self._tooltip
        yield knopf

    # -- oeffentlich ----------------------------------------------------

    @property
    def input(self) -> Input:
        """Das innere Eingabefeld."""
        return self.query_one(f"#{self._input_id}", Input)

    @property
    def value(self) -> str:
        return self.input.value

    @value.setter
    def value(self, text: str) -> None:
        self.input.value = text

    @property
    def disabled_input(self) -> bool:
        """Ob Feld und Knopf gesperrt sind."""
        return bool(self.input.disabled)

    def set_disabled(self, gesperrt: bool) -> None:
        """Sperrt oder entsperrt Feld und Knopf gemeinsam."""
        self.input.disabled = gesperrt
        self.query_one(f"#{self._button_id}", Button).disabled = gesperrt

    def clear(self) -> None:
        """Leert das Feld, ohne eine Nachricht zu senden."""
        self.input.value = ""

    def focus_input(self) -> None:
        """Setzt den Fokus ins Feld."""
        self.input.focus()

    # -- intern ---------------------------------------------------------

    @on(Button.Pressed)
    def _geleert(self, ereignis: Button.Pressed) -> None:
        if ereignis.button.id != self._button_id:
            return
        ereignis.stop()
        self.clear()
        self.focus_input()
        self.post_message(self.Cleared(self))
