"""Tests for HamburgerItem and HamburgerMenu construction + JSON loading."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from textual_widgets import HamburgerItem, HamburgerMenu


class TestHamburgerItem:
    def test_minimal(self) -> None:
        item = HamburgerItem(id="inbox", label="Inbox")
        assert item.id == "inbox"
        assert item.label == "Inbox"
        assert item.icon == ""
        assert item.is_group_header is False
        assert item.is_separator is False

    def test_with_icon(self) -> None:
        item = HamburgerItem("inbox", "Inbox", icon="📧")
        assert item.icon == "📧"

    def test_is_frozen(self) -> None:
        item = HamburgerItem("a", "A")
        with pytest.raises(Exception):
            item.id = "b"  # type: ignore[misc]

    def test_group_factory(self) -> None:
        g = HamburgerItem.group("Accounts")
        assert g.is_group_header is True
        assert g.label == "Accounts"
        assert g.id == ""

    def test_separator_factory(self) -> None:
        s = HamburgerItem.separator()
        assert s.is_separator is True
        assert s.id == ""
        assert s.label == ""


class TestHamburgerMenuConstruction:
    def test_minimal(self) -> None:
        menu = HamburgerMenu(items=[HamburgerItem("a", "A")])
        assert len(menu._items) == 1
        assert menu._bottom_items == []
        assert menu._collapsed_width == 4
        assert menu._expanded_width == 26
        assert menu._initial_expanded is False

    def test_with_bottom_items(self) -> None:
        menu = HamburgerMenu(
            items=[HamburgerItem("a", "A")],
            bottom_items=[HamburgerItem("settings", "Settings")],
        )
        assert len(menu._bottom_items) == 1
        assert menu._bottom_items[0].id == "settings"

    def test_initial_expanded(self) -> None:
        menu = HamburgerMenu(
            items=[HamburgerItem("a", "A")],
            initial_expanded=True,
        )
        assert menu._initial_expanded is True

    def test_custom_widths(self) -> None:
        menu = HamburgerMenu(
            items=[HamburgerItem("a", "A")],
            collapsed_width=6,
            expanded_width=40,
        )
        assert menu._collapsed_width == 6
        assert menu._expanded_width == 40

    def test_items_are_copied(self) -> None:
        original = [HamburgerItem("a", "A")]
        menu = HamburgerMenu(items=original)
        original.append(HamburgerItem("b", "B"))
        assert len(menu._items) == 1


class TestFromJson:
    def test_basic_load(self, tmp_path: Path) -> None:
        config = {
            "items": [
                {"id": "new", "label": "New", "icon": "+"},
                {"group": "Accounts"},
                {"id": "inbox", "label": "Inbox", "icon": "📧"},
                {"separator": True},
                {"id": "sent", "label": "Sent", "icon": "📤"},
            ],
            "bottom_items": [
                {"id": "settings", "label": "Settings", "icon": "⚙"},
            ],
        }
        path = tmp_path / "menu.json"
        path.write_text(json.dumps(config), encoding="utf-8")

        menu = HamburgerMenu.from_json(path)

        assert len(menu._items) == 5
        assert menu._items[0].id == "new"
        assert menu._items[1].is_group_header is True
        assert menu._items[1].label == "Accounts"
        assert menu._items[2].id == "inbox"
        assert menu._items[3].is_separator is True
        assert menu._items[4].id == "sent"
        assert len(menu._bottom_items) == 1
        assert menu._bottom_items[0].id == "settings"

    def test_kwargs_passed_through(self, tmp_path: Path) -> None:
        path = tmp_path / "m.json"
        path.write_text('{"items": []}', encoding="utf-8")
        menu = HamburgerMenu.from_json(path, expanded_width=50)
        assert menu._expanded_width == 50

    def test_missing_keys_default_to_empty(self, tmp_path: Path) -> None:
        path = tmp_path / "m.json"
        path.write_text("{}", encoding="utf-8")
        menu = HamburgerMenu.from_json(path)
        assert menu._items == []
        assert menu._bottom_items == []

    def test_string_path(self, tmp_path: Path) -> None:
        path = tmp_path / "m.json"
        path.write_text('{"items": [{"id": "x", "label": "X"}]}', encoding="utf-8")
        menu = HamburgerMenu.from_json(str(path))
        assert menu._items[0].id == "x"


class TestMessages:
    def test_item_selected_carries_id(self) -> None:
        msg = HamburgerMenu.ItemSelected("inbox")
        assert msg.item_id == "inbox"

    def test_toggled_carries_state(self) -> None:
        msg = HamburgerMenu.Toggled(True)
        assert msg.expanded is True
