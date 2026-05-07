"""Tests fuer ContextMenuItem und ContextMenuScreen."""
from __future__ import annotations

import pytest

from textual_widgets import ContextMenuItem, ContextMenuScreen


class TestContextMenuItem:
    def test_minimal_item(self) -> None:
        item = ContextMenuItem(id="open", label="Oeffnen")
        assert item.id == "open"
        assert item.label == "Oeffnen"
        assert item.icon == ""
        assert item.shortcut == ""
        assert item.enabled is True
        assert item.is_separator is False

    def test_full_item(self) -> None:
        item = ContextMenuItem(
            id="rename",
            label="Umbenennen",
            icon="✎",
            shortcut="Ctrl+R",
            enabled=False,
        )
        assert item.icon == "✎"
        assert item.shortcut == "Ctrl+R"
        assert item.enabled is False

    def test_is_frozen(self) -> None:
        item = ContextMenuItem(id="x", label="X")
        with pytest.raises(Exception):  # FrozenInstanceError
            item.id = "y"  # type: ignore[misc]

    def test_separator_factory(self) -> None:
        sep = ContextMenuItem.separator()
        assert sep.is_separator is True
        assert sep.id == ""
        assert sep.label == ""

    def test_separator_distinct_from_regular(self) -> None:
        item = ContextMenuItem(id="x", label="X")
        assert item.is_separator is False


class TestContextMenuScreen:
    def test_init_with_items(self) -> None:
        items = [
            ContextMenuItem(id="a", label="A"),
            ContextMenuItem(id="b", label="B"),
        ]
        screen = ContextMenuScreen(items)
        assert screen._items == items
        assert screen._at is None

    def test_init_with_position(self) -> None:
        items = [ContextMenuItem(id="x", label="X")]
        screen = ContextMenuScreen(items, at=(10, 5))
        assert screen._at == (10, 5)

    def test_items_are_copied(self) -> None:
        """Modifikationen an der Original-Liste beeinflussen das Menue nicht."""
        items = [ContextMenuItem(id="a", label="A")]
        screen = ContextMenuScreen(items)
        items.append(ContextMenuItem(id="b", label="B"))
        assert len(screen._items) == 1

    def test_format_label_without_icon(self) -> None:
        item = ContextMenuItem(id="x", label="Open")
        assert ContextMenuScreen._format_label(item) == "Open"

    def test_format_label_with_icon(self) -> None:
        item = ContextMenuItem(id="x", label="Open", icon="📂")
        assert ContextMenuScreen._format_label(item) == "📂 Open"

    def test_accepts_separator_in_items(self) -> None:
        items = [
            ContextMenuItem(id="a", label="A"),
            ContextMenuItem.separator(),
            ContextMenuItem(id="b", label="B"),
        ]
        screen = ContextMenuScreen(items)
        assert len(screen._items) == 3
        assert screen._items[1].is_separator is True


class TestEstimateSize:
    """Validiert die Groessen-Schaetzung fuer Off-Screen-Schutz beim ersten Render."""

    def test_minimum_width_for_short_labels(self) -> None:
        items = [ContextMenuItem(id="a", label="X")]
        screen = ContextMenuScreen(items)
        w, _ = screen._estimate_size()
        assert w == 16  # min-width-Klemme

    def test_maximum_width_caps_long_labels(self) -> None:
        items = [ContextMenuItem(id="a", label="x" * 100)]
        screen = ContextMenuScreen(items)
        w, _ = screen._estimate_size()
        assert w == 60  # max-width-Klemme

    def test_width_scales_with_label_length(self) -> None:
        items = [ContextMenuItem(id="a", label="Hallo Welt 12345678")]
        screen = ContextMenuScreen(items)
        w, _ = screen._estimate_size()
        # 19 Zeichen Label + 6 (Padding + Border + Safety) = 25
        assert w == 25

    def test_width_includes_shortcut_column(self) -> None:
        items = [
            ContextMenuItem(id="a", label="Open", shortcut="Ctrl+O"),
            ContextMenuItem(id="b", label="Save"),
        ]
        screen = ContextMenuScreen(items)
        w, _ = screen._estimate_size()
        # max_label 4 + 2 (Trenner) + 6 (Ctrl+O) + 6 (Pad+Border+Safety) = 18
        assert w == 18

    def test_width_with_icon(self) -> None:
        items = [ContextMenuItem(id="a", label="Open", icon="📂")]
        screen = ContextMenuScreen(items)
        w, _ = screen._estimate_size()
        # _format_label ergibt "📂 Open" (7 Zeichen) + 6 = 13, geklemmt auf min 16
        assert w == 16

    def test_height_scales_with_item_count(self) -> None:
        items = [ContextMenuItem(id=f"id-{i}", label=f"Item {i}") for i in range(5)]
        screen = ContextMenuScreen(items)
        _, h = screen._estimate_size()
        assert h == 5 + 4  # 5 Items + 2 Border + 2 Safety

    def test_height_includes_separators(self) -> None:
        items = [
            ContextMenuItem(id="a", label="A"),
            ContextMenuItem.separator(),
            ContextMenuItem(id="b", label="B"),
        ]
        screen = ContextMenuScreen(items)
        _, h = screen._estimate_size()
        assert h == 3 + 4  # 3 "Items" (inkl. Separator) + 2 Border + 2 Safety
