"""Tests fuer VerticalSplitter und HorizontalSplitter."""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Static

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

    def test_subclass_message_carries_payload(self) -> None:
        msg = HorizontalSplitter.Resized("file-table", 12)
        assert msg.target_id == "file-table"
        assert msg.size == 12


class TestInheritance:
    def test_vertical_inherits_base(self) -> None:
        assert issubclass(VerticalSplitter, _SplitterBase)

    def test_horizontal_inherits_base(self) -> None:
        assert issubclass(HorizontalSplitter, _SplitterBase)

    def test_resized_message_is_subclass(self) -> None:
        """Jeder Splitter redeklariert Resized als Subklasse der Basis-Message."""
        assert issubclass(VerticalSplitter.Resized, _SplitterBase.Resized)
        assert issubclass(HorizontalSplitter.Resized, _SplitterBase.Resized)


class TestHandlerNames:
    """Die Handler-Namen muessen orientierungsspezifisch sein — sonst feuern
    die erwarteten ``on_horizontal_splitter_*`` / ``on_vertical_splitter_*``
    Handler in den Consumer-Apps nie."""

    def test_resized_handler_names(self) -> None:
        assert VerticalSplitter.Resized.handler_name == "on_vertical_splitter_resized"
        assert HorizontalSplitter.Resized.handler_name == "on_horizontal_splitter_resized"

    def test_close_and_collapse_handler_names(self) -> None:
        assert HorizontalSplitter.CloseRequested.handler_name == "on_horizontal_splitter_close_requested"
        assert HorizontalSplitter.CollapseRequested.handler_name == "on_horizontal_splitter_collapse_requested"


class TestTitleBar:
    def test_plain_splitter_has_no_titlebar(self) -> None:
        splitter = HorizontalSplitter()
        assert splitter._has_titlebar() is False
        assert splitter.has_class("-titled") is False

    def test_title_enables_titlebar(self) -> None:
        splitter = HorizontalSplitter(title="Log")
        assert splitter._has_titlebar() is True
        assert splitter.has_class("-titled") is True

    def test_flags_enable_titlebar_without_title(self) -> None:
        splitter = HorizontalSplitter(show_close=True)
        assert splitter._has_titlebar() is True
        assert splitter.has_class("-titled") is True

    def test_collapse_message_payload(self) -> None:
        msg = HorizontalSplitter.CollapseRequested(collapsed=True)
        assert msg.collapsed is True

    def test_set_collapsed_toggles_state(self) -> None:
        splitter = HorizontalSplitter(title="Log", show_collapse=True)
        assert splitter.collapsed is False
        splitter.set_collapsed(True)
        assert splitter.collapsed is True


class _TitledApp(App[None]):
    """App mit einem betitelten HorizontalSplitter ueber einem Target."""

    def __init__(self) -> None:
        super().__init__()
        self.events: list[object] = []

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("target", id="target")
            yield HorizontalSplitter(
                target_id="target",
                title="Log",
                show_collapse=True,
                show_close=True,
                id="sp",
            )

    def on_horizontal_splitter_close_requested(self, event: HorizontalSplitter.CloseRequested) -> None:
        self.events.append("close")

    def on_horizontal_splitter_collapse_requested(self, event: HorizontalSplitter.CollapseRequested) -> None:
        self.events.append(("collapse", event.collapsed))


class TestTitleBarInteraction:
    async def test_render_populates_icon_regions(self) -> None:
        async with _TitledApp().run_test(size=(60, 10)) as pilot:
            sp = pilot.app.query_one("#sp", HorizontalSplitter)
            actions = {action for _, _, action in sp._icon_regions}
            assert actions == {"collapse", "close"}

    async def test_click_close_posts_message(self) -> None:
        app = _TitledApp()
        async with app.run_test(size=(60, 10)) as pilot:
            sp = pilot.app.query_one("#sp", HorizontalSplitter)
            x0, x1, _ = next(r for r in sp._icon_regions if r[2] == "close")
            await pilot.click("#sp", offset=((x0 + x1) // 2, 0))
            await pilot.pause()
            assert "close" in app.events

    async def test_click_collapse_toggles_and_posts(self) -> None:
        app = _TitledApp()
        async with app.run_test(size=(60, 10)) as pilot:
            sp = pilot.app.query_one("#sp", HorizontalSplitter)
            x0, x1, _ = next(r for r in sp._icon_regions if r[2] == "collapse")
            await pilot.click("#sp", offset=((x0 + x1) // 2, 0))
            await pilot.pause()
            assert sp.collapsed is True
            assert ("collapse", True) in app.events

    async def test_click_middle_does_not_post_icon_message(self) -> None:
        """Klick in die Drag-Zone (Mitte) loest keine Icon-Aktion aus."""
        app = _TitledApp()
        async with app.run_test(size=(60, 10)) as pilot:
            await pilot.click("#sp", offset=(20, 0))
            await pilot.pause()
            assert app.events == []
