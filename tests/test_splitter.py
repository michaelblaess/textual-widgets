"""Tests fuer VerticalSplitter und HorizontalSplitter."""
from __future__ import annotations

from textual_widgets import HorizontalSplitter, VerticalSplitter
from textual_widgets.splitter import _SplitterBase


class TestSplitterConstruction:
    def test_vertical_default(self) -> None:
        splitter = VerticalSplitter()
        assert splitter._target_id is None
        assert splitter._min_size == 5
        assert splitter._max_size is None
        assert splitter._dragging is False

    def test_horizontal_default(self) -> None:
        splitter = HorizontalSplitter()
        assert splitter._target_id is None
        assert splitter._min_size == 5
        assert splitter._max_size is None

    def test_with_target_id(self) -> None:
        splitter = VerticalSplitter(target_id="left-pane")
        assert splitter._target_id == "left-pane"

    def test_min_size(self) -> None:
        splitter = VerticalSplitter(min_size=20)
        assert splitter._min_size == 20

    def test_min_size_clamped_to_one(self) -> None:
        """min_size darf nicht 0 oder negativ sein."""
        splitter = VerticalSplitter(min_size=0)
        assert splitter._min_size == 1

    def test_max_size(self) -> None:
        splitter = VerticalSplitter(max_size=80)
        assert splitter._max_size == 80


class TestClamp:
    def test_clamp_within_range(self) -> None:
        splitter = VerticalSplitter(min_size=10, max_size=50)
        assert splitter._clamp(25) == 25

    def test_clamp_to_min(self) -> None:
        splitter = VerticalSplitter(min_size=10, max_size=50)
        assert splitter._clamp(3) == 10

    def test_clamp_to_max(self) -> None:
        splitter = VerticalSplitter(min_size=10, max_size=50)
        assert splitter._clamp(99) == 50

    def test_clamp_no_max(self) -> None:
        splitter = VerticalSplitter(min_size=10)
        assert splitter._clamp(99999) == 99999

    def test_clamp_horizontal(self) -> None:
        splitter = HorizontalSplitter(min_size=3, max_size=30)
        assert splitter._clamp(40) == 30
        assert splitter._clamp(1) == 3


class TestResizedMessage:
    def test_message_carries_target_and_size(self) -> None:
        msg = _SplitterBase.Resized("left-pane", 42)
        assert msg.target_id == "left-pane"
        assert msg.size == 42


class TestInheritance:
    def test_vertical_inherits_base(self) -> None:
        assert issubclass(VerticalSplitter, _SplitterBase)

    def test_horizontal_inherits_base(self) -> None:
        assert issubclass(HorizontalSplitter, _SplitterBase)

    def test_resized_message_shared(self) -> None:
        """Beide Splitter teilen sich die gleiche Resized-Message."""
        assert VerticalSplitter.Resized is _SplitterBase.Resized
        assert HorizontalSplitter.Resized is _SplitterBase.Resized
