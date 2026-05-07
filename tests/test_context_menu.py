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
