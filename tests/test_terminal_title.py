"""Tests fuer die Terminal-Titel-Helfer."""

from __future__ import annotations

import io
import sys

from textual_widgets import reset_terminal_title, set_terminal_title
from textual_widgets.terminal_title import _OSC_TITLE, _write_osc


class _FakeTty(io.StringIO):
    """StringIO, das sich als TTY ausgibt."""

    def isatty(self) -> bool:
        return True


class TestWriteOsc:
    def test_writes_osc_sequence_to_tty(self) -> None:
        fake = _FakeTty()
        original = sys.__stdout__
        sys.__stdout__ = fake  # type: ignore[misc]
        try:
            _write_osc("hello")
        finally:
            sys.__stdout__ = original  # type: ignore[misc]
        assert fake.getvalue() == _OSC_TITLE.format(title="hello")

    def test_skips_when_not_a_tty(self) -> None:
        fake = io.StringIO()  # isatty() == False
        original = sys.__stdout__
        sys.__stdout__ = fake  # type: ignore[misc]
        try:
            _write_osc("hello")
        finally:
            sys.__stdout__ = original  # type: ignore[misc]
        assert fake.getvalue() == ""

    def test_handles_none_stream(self) -> None:
        original = sys.__stdout__
        sys.__stdout__ = None  # type: ignore[misc]
        try:
            _write_osc("hello")  # darf nicht crashen
        finally:
            sys.__stdout__ = original  # type: ignore[misc]


class TestPublicApi:
    def test_set_terminal_title(self) -> None:
        fake = _FakeTty()
        original = sys.__stdout__
        sys.__stdout__ = fake  # type: ignore[misc]
        try:
            set_terminal_title("♬ my-app")
        finally:
            sys.__stdout__ = original  # type: ignore[misc]
        assert fake.getvalue() == _OSC_TITLE.format(title="♬ my-app")

    def test_reset_terminal_title(self) -> None:
        fake = _FakeTty()
        original = sys.__stdout__
        sys.__stdout__ = fake  # type: ignore[misc]
        try:
            reset_terminal_title()
        finally:
            sys.__stdout__ = original  # type: ignore[misc]
        assert fake.getvalue() == _OSC_TITLE.format(title="")
