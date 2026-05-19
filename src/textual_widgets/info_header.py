"""Info-Header-Widget fuer Textual-Apps.

Public API:
    - `InfoItem` - ein Label/Wert-Paar im Header.
    - `InfoAction` - ein anklickbarer Action-Link.
    - `InfoHeader` - umrandetes Kopf-Panel, das InfoItems im Spalten-Raster zeigt.

Usage:
    from textual_widgets import InfoHeader, InfoItem, InfoAction

    yield InfoHeader(
        [
            InfoItem("vehicle", "Fahrzeug", "Mazda CX-5"),
            InfoItem("period", "Zeitraum", "Februar 2025", navigable=True),
        ],
        columns=2,
        title="Fahrtenbuch",
        actions=[InfoAction("open", "Open")],
        collapsible=True,
    )

    # Laufzeit:
    header.set_value("vehicle", "Audi A5", value_style="bold")

Messages:
    - `InfoHeader.ActionPressed(key)` - ein Action-Link wurde geklickt.
    - `InfoHeader.Navigated(key, direction)` - der Pfeil eines navigierbaren
      Items wurde geklickt; direction ist "prev" oder "next".
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass, replace

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.css.query import NoMatches
from textual.events import Click
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Static

# Marker vor dem Titel bei collapsible Headern.
_MARKER_EXPANDED = "▾"  # ▾
_MARKER_COLLAPSED = "▸"  # ▸


@dataclass(frozen=True)
class InfoItem:
    """Ein Label/Wert-Paar im Header.

    Attributes:
        key:
            Stabile ID fuer Laufzeit-Updates (set_value) und Navigations-
            Messages. Muss innerhalb eines Headers eindeutig sein.
        label:
            Linker Beschriftungstext (gedimmt dargestellt).
        value:
            Rechter Wert-Text.
        value_style:
            Optionaler Rich-Style fuer den Wert (z.B. "bold green").
        value_align:
            Ausrichtung des Werts: "left" (Default) oder "right".
        navigable:
            Wenn True, wird der Wert zwischen zwei Pfeilen dargestellt;
            ein Klick postet `InfoHeader.Navigated`.
    """

    key: str
    label: str
    value: str = ""
    value_style: str = ""
    value_align: str = "left"
    navigable: bool = False


@dataclass(frozen=True)
class InfoAction:
    """Ein anklickbarer Action-Link unten rechts im Header.

    Attributes:
        key:
            Stabile ID, die mit `InfoHeader.ActionPressed` zurueckgegeben wird.
        label:
            Angezeigter Text des Links.
    """

    key: str
    label: str


class InfoHeader(Vertical):
    """Umrandetes Kopf-Panel mit Label/Wert-Paaren im Spalten-Raster.

    Die Items werden auf `columns` Paare pro Zeile verteilt; weitere Items
    brechen automatisch in zusaetzliche Zeilen um. Werte lassen sich zur
    Laufzeit mit `set_value()` aendern. Optional gibt es eine Titelzeile,
    Action-Links und ein Ein-/Ausklappen (collapsible).
    """

    DEFAULT_CSS = """
    InfoHeader {
        height: auto;
        background: $surface;
        border: solid $accent;
        padding: 0 1;
    }

    InfoHeader #info-title {
        width: 1fr;
        height: 1;
        color: $accent;
        text-style: bold;
    }

    InfoHeader #info-body {
        height: auto;
    }

    InfoHeader .info-row {
        height: 1;
        layout: horizontal;
    }

    InfoHeader .info-cell {
        width: 1fr;
        height: 1;
        layout: horizontal;
        padding: 0 2 0 0;
    }

    InfoHeader .info-label {
        height: 1;
        color: $text-muted;
    }

    InfoHeader .info-value {
        width: 1fr;
        height: 1;
        color: $text;
    }

    InfoHeader .info-value-right {
        text-align: right;
    }

    InfoHeader .info-nav {
        width: 1fr;
        height: 1;
        layout: horizontal;
    }

    InfoHeader .info-nav-value {
        width: 1fr;
        height: 1;
        text-align: center;
        color: $text;
    }

    InfoHeader #info-actions {
        height: 1;
        align: right middle;
    }

    InfoHeader .info-nav-arrow {
        width: 3;
        height: 1;
        content-align: center middle;
        color: $accent;
    }

    InfoHeader .info-action {
        height: 1;
        width: auto;
        padding: 0 1;
        color: $accent;
        text-style: underline;
    }

    InfoHeader .info-nav-arrow:hover, InfoHeader .info-action:hover {
        background: $accent 20%;
    }
    """

    collapsed: reactive[bool] = reactive(False)

    class ActionPressed(Message):
        """Ein Action-Link wurde geklickt."""

        def __init__(self, key: str) -> None:
            super().__init__()
            self.key = key

    class Navigated(Message):
        """Ein Pfeil eines navigierbaren Items wurde geklickt."""

        def __init__(self, key: str, direction: str) -> None:
            super().__init__()
            self.key = key
            self.direction = direction  # "prev" | "next"

    def __init__(
        self,
        items: list[InfoItem],
        *,
        columns: int = 2,
        title: str = "",
        actions: list[InfoAction] | None = None,
        label_width: int = 14,
        collapsible: bool = False,
        collapsed: bool = False,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        """Erstellt den Info-Header.

        Args:
            items:
                Die anzuzeigenden Label/Wert-Paare.
            columns:
                Anzahl Label/Wert-Paare pro Zeile (mind. 1).
            title:
                Optionale Titelzeile ueber den Items.
            actions:
                Optionale Action-Links unten rechts.
            label_width:
                Feste Breite der Label-Spalte in Zellen.
            collapsible:
                Wenn True, kann der Header ein-/ausgeklappt werden (per
                Klick auf die Titelzeile oder via toggle()).
            collapsed:
                Anfangszustand, wenn collapsible True ist.
            name:
                Optionaler Widget-Name (Textual-Standard).
            id:
                Optionale Widget-ID (Textual-Standard).
            classes:
                Optionale CSS-Klassen (Textual-Standard).
            disabled:
                Ob das Widget deaktiviert ist (Textual-Standard).
        """
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self._columns = max(1, columns)
        self._title = title
        self._actions = list(actions or [])
        self._label_width = label_width
        self._collapsible = collapsible
        self._items: dict[str, InfoItem] = {}
        self._init_items(items)
        # Widget-Referenzen fuer Laufzeit-Updates / Klick-Aufloesung.
        self._value_widgets: dict[str, Static] = {}
        self._click_map: dict[str, tuple[str, str]] = {}
        self._click_counter = 0
        self.set_reactive(InfoHeader.collapsed, collapsed)

    def _init_items(self, items: list[InfoItem]) -> None:
        """Uebernimmt die Item-Liste in das geordnete Dict."""
        self._items = {item.key: item for item in items}

    # --- Compose -----------------------------------------------------

    def compose(self) -> ComposeResult:
        """Erstellt Titelzeile, Item-Koerper und Action-Zeile."""
        if self._title or self._collapsible:
            yield Static(self._title_text(), id="info-title")
        with Vertical(id="info-body"):
            yield from self._build_rows()
        if self._actions:
            with Horizontal(id="info-actions"):
                for action in self._actions:
                    yield Static(
                        action.label,
                        classes="info-action",
                        id=self._click_id("action", action.key),
                    )

    def on_mount(self) -> None:
        """Wendet den initialen Collapsed-Zustand an."""
        self._apply_collapsed()

    def _build_rows(self) -> list[Horizontal]:
        """Baut die Item-Zeilen (je `columns` Zellen)."""
        self._value_widgets.clear()
        order = list(self._items.values())
        rows: list[Horizontal] = []
        for start in range(0, len(order), self._columns):
            chunk = order[start : start + self._columns]
            rows.append(Horizontal(*[self._build_cell(item) for item in chunk], classes="info-row"))
        return rows

    def _build_cell(self, item: InfoItem) -> Horizontal:
        """Baut eine einzelne Label/Wert-Zelle."""
        label = Static(item.label, classes="info-label")
        label.styles.width = self._label_width

        if item.navigable:
            value = Static(self._value_text(item), classes="info-nav-value")
            self._value_widgets[item.key] = value
            prev_arrow = Static("<", classes="info-nav-arrow", id=self._click_id("prev", item.key))
            next_arrow = Static(">", classes="info-nav-arrow", id=self._click_id("next", item.key))
            nav = Horizontal(prev_arrow, value, next_arrow, classes="info-nav")
            return Horizontal(label, nav, classes="info-cell")

        classes = "info-value"
        if item.value_align == "right":
            classes += " info-value-right"
        value = Static(self._value_text(item), classes=classes)
        self._value_widgets[item.key] = value
        return Horizontal(label, value, classes="info-cell")

    def _click_id(self, kind: str, key: str) -> str:
        """Erzeugt eine eindeutige Widget-ID und merkt sich kind+key."""
        click_id = f"info-click-{self._click_counter}"
        self._click_counter += 1
        self._click_map[click_id] = (kind, key)
        return click_id

    # --- Rendering-Helfer -------------------------------------------

    @staticmethod
    def _value_text(item: InfoItem) -> Text:
        """Baut den Wert als Rich Text (mit optionalem Style)."""
        return Text(item.value, style=item.value_style) if item.value_style else Text(item.value)

    def _title_text(self) -> str:
        """Baut die Titelzeile (mit Marker, wenn collapsible)."""
        if not self._collapsible:
            return self._title
        marker = _MARKER_COLLAPSED if self.collapsed else _MARKER_EXPANDED
        return f"{marker} {self._title}".rstrip()

    # --- Public API --------------------------------------------------

    def set_value(self, key: str, value: str, value_style: str | None = None) -> None:
        """Aktualisiert den Wert eines Items.

        Args:
            key:
                Key des Items.
            value:
                Neuer Wert-Text.
            value_style:
                Optionaler neuer Rich-Style. None laesst den bisherigen
                Style unveraendert.
        """
        item = self._items.get(key)
        if item is None:
            return
        style = item.value_style if value_style is None else value_style
        self._items[key] = replace(item, value=value, value_style=style)
        widget = self._value_widgets.get(key)
        if widget is not None:
            widget.update(Text(value, style=style) if style else Text(value))

    def set_items(self, items: list[InfoItem]) -> None:
        """Ersetzt alle Items und baut den Koerper neu auf.

        Args:
            items:
                Die neue Item-Liste.
        """
        self._init_items(items)
        try:
            body = self.query_one("#info-body", Vertical)
        except NoMatches:
            return
        body.remove_children()
        body.mount(*self._build_rows())

    def toggle(self) -> None:
        """Klappt den Header ein bzw. aus (nur wenn collapsible).

        Fuer einen festen Zustand direkt das `collapsed`-Reactive setzen
        (`header.collapsed = True` / `False`).
        """
        if self._collapsible:
            self.collapsed = not self.collapsed

    # --- Reaktionen --------------------------------------------------

    def watch_collapsed(self, collapsed: bool) -> None:
        """Reagiert auf Aenderung des Collapsed-Zustands."""
        self._apply_collapsed()

    def _apply_collapsed(self) -> None:
        """Blendet Koerper und Action-Zeile je nach Collapsed-Zustand aus."""
        visible = not self.collapsed
        for selector in ("#info-body", "#info-actions"):
            with contextlib.suppress(NoMatches):
                self.query_one(selector).display = visible
        with contextlib.suppress(NoMatches):
            self.query_one("#info-title", Static).update(self._title_text())

    def on_click(self, event: Click) -> None:
        """Verarbeitet Klicks auf Titel, Action-Links und Navigations-Pfeile."""
        widget = event.widget
        if widget is None:
            return
        widget_id = widget.id or ""

        if self._collapsible and widget_id == "info-title":
            event.stop()
            self.toggle()
            return

        entry = self._click_map.get(widget_id)
        if entry is None:
            return
        event.stop()
        kind, key = entry
        if kind == "action":
            self.post_message(self.ActionPressed(key))
        elif kind == "prev":
            self.post_message(self.Navigated(key, "prev"))
        elif kind == "next":
            self.post_message(self.Navigated(key, "next"))
