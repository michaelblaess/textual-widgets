"""Tests fuer InfoHeader, InfoItem und InfoAction."""

from __future__ import annotations

from textual.app import App, ComposeResult

from textual_widgets import InfoAction, InfoHeader, InfoItem


class TestInfoItem:
    def test_defaults(self) -> None:
        item = InfoItem("k", "Label")
        assert item.value == ""
        assert item.value_style == ""
        assert item.value_align == "left"
        assert item.navigable is False

    def test_all_fields(self) -> None:
        item = InfoItem("k", "L", "V", value_style="bold", value_align="right", navigable=True)
        assert (item.key, item.label, item.value) == ("k", "L", "V")
        assert item.value_style == "bold"
        assert item.value_align == "right"
        assert item.navigable is True


class TestInfoAction:
    def test_fields(self) -> None:
        action = InfoAction("open", "Open")
        assert action.key == "open"
        assert action.label == "Open"


class TestInfoHeaderConstruction:
    def test_items_stored_by_key(self) -> None:
        header = InfoHeader([InfoItem("a", "A", "1"), InfoItem("b", "B", "2")])
        assert list(header._items) == ["a", "b"]

    def test_columns_default(self) -> None:
        assert InfoHeader([])._columns == 2

    def test_columns_clamped_to_one(self) -> None:
        assert InfoHeader([], columns=0)._columns == 1

    def test_collapsed_initial(self) -> None:
        header = InfoHeader([], collapsible=True, collapsed=True)
        assert header.collapsed is True

    def test_not_collapsed_by_default(self) -> None:
        assert InfoHeader([])._collapsible is False
        assert InfoHeader([]).collapsed is False


class TestTitleText:
    def test_plain_title_without_collapsible(self) -> None:
        header = InfoHeader([], title="Stats")
        assert header._title_text() == "Stats"

    def test_collapsible_expanded_marker(self) -> None:
        header = InfoHeader([], title="Stats", collapsible=True)
        assert header._title_text() == "▾ Stats"

    def test_collapsible_collapsed_marker(self) -> None:
        header = InfoHeader([], title="Stats", collapsible=True, collapsed=True)
        assert header._title_text() == "▸ Stats"


class TestSetValueOffline:
    def test_set_value_updates_stored_item(self) -> None:
        header = InfoHeader([InfoItem("a", "A", "1")])
        header.set_value("a", "99")
        assert header._items["a"].value == "99"

    def test_set_value_keeps_style_when_none(self) -> None:
        header = InfoHeader([InfoItem("a", "A", "1", value_style="bold")])
        header.set_value("a", "2")
        assert header._items["a"].value_style == "bold"

    def test_set_value_changes_style(self) -> None:
        header = InfoHeader([InfoItem("a", "A", "1")])
        header.set_value("a", "2", value_style="red")
        assert header._items["a"].value_style == "red"

    def test_set_value_unknown_key_is_noop(self) -> None:
        header = InfoHeader([InfoItem("a", "A", "1")])
        header.set_value("missing", "x")  # darf nicht werfen
        assert "missing" not in header._items

    def test_toggle_noop_when_not_collapsible(self) -> None:
        header = InfoHeader([])
        header.toggle()
        assert header.collapsed is False


class TestFill:
    def test_default_fill_is_row(self) -> None:
        assert InfoHeader([])._fill == "row"

    def test_fill_column(self) -> None:
        assert InfoHeader([], fill="column")._fill == "column"

    def test_invalid_fill_falls_back_to_row(self) -> None:
        assert InfoHeader([], fill="diagonal")._fill == "row"


class _HeaderApp(App[None]):
    def __init__(self, header: InfoHeader) -> None:
        super().__init__()
        self._header = header

    def compose(self) -> ComposeResult:
        yield self._header


class TestInfoHeaderMounted:
    async def test_rows_built_for_items(self) -> None:
        header = InfoHeader(
            [InfoItem(f"k{i}", f"L{i}", str(i)) for i in range(5)],
            columns=2,
        )
        app = _HeaderApp(header)
        async with app.run_test():
            # 5 Items / 2 Spalten -> 3 Zeilen
            assert len(header.query(".info-row")) == 3

    async def test_set_value_updates_widget(self) -> None:
        header = InfoHeader([InfoItem("a", "A", "1")])
        app = _HeaderApp(header)
        async with app.run_test():
            header.set_value("a", "42")
            assert "42" in header._value_widgets["a"].render().plain

    async def test_toggle_collapses_body(self) -> None:
        header = InfoHeader([InfoItem("a", "A", "1")], title="T", collapsible=True)
        app = _HeaderApp(header)
        async with app.run_test() as pilot:
            assert header.query_one("#info-body").display is True
            header.toggle()
            await pilot.pause()
            assert header.collapsed is True
            assert header.query_one("#info-body").display is False

    async def test_column_fill_pads_to_full_grid(self) -> None:
        # 5 Items, 2 Spalten -> 3 Zeilen, jede Zeile 2 Zellen (letzte gepaddet)
        header = InfoHeader(
            [InfoItem(f"k{i}", f"L{i}", str(i)) for i in range(5)],
            columns=2,
            fill="column",
        )
        app = _HeaderApp(header)
        async with app.run_test():
            rows = header.query(".info-row")
            assert len(rows) == 3
            for row in rows:
                assert len(row.children) == 2

    async def test_set_items_rebuilds(self) -> None:
        header = InfoHeader([InfoItem("a", "A", "1")], columns=1)
        app = _HeaderApp(header)
        async with app.run_test() as pilot:
            assert len(header.query(".info-row")) == 1
            header.set_items([InfoItem("x", "X", "1"), InfoItem("y", "Y", "2")])
            await pilot.pause()
            assert len(header.query(".info-row")) == 2
