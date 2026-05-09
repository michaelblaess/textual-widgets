"""Collapsible hamburger menu — DevExpress-style.

Two visual states:
- Collapsed: narrow column showing only icons (~4 cells wide).
- Expanded: wider column showing icons + labels with optional group headers.

Click the hamburger icon at the top to toggle, or call ``menu.toggle()``
programmatically. Width changes are animated.

Public API:
    - ``HamburgerItem`` — dataclass: ``id``, ``label``, optional ``icon``.
      Factories ``HamburgerItem.group(label)`` for group headers and
      ``HamburgerItem.separator()`` for thin divider lines.
    - ``HamburgerMenu`` — Widget. Subscribe to ``HamburgerMenu.ItemSelected``
      to react to clicks.

Usage:

    from textual_widgets import HamburgerMenu, HamburgerItem

    class MyApp(App):
        def compose(self) -> ComposeResult:
            with Horizontal():
                yield HamburgerMenu(
                    items=[
                        HamburgerItem("new", "New mail", icon="+"),
                        HamburgerItem.group("Accounts"),
                        HamburgerItem("inbox", "Inbox", icon="📧"),
                        HamburgerItem("sent", "Sent", icon="📤"),
                    ],
                    bottom_items=[
                        HamburgerItem("settings", "Settings", icon="⚙"),
                    ],
                )
                yield Container(id="main")

        def on_hamburger_menu_item_selected(
            self, event: HamburgerMenu.ItemSelected,
        ) -> None:
            self.notify(f"Selected: {event.item_id}")

JSON config (optional):

    items = HamburgerMenu.from_json("menu.json")

    # menu.json:
    # {
    #   "items": [
    #     {"id": "new", "label": "New mail", "icon": "+"},
    #     {"group": "Accounts"},
    #     {"id": "inbox", "label": "Inbox", "icon": "📧"}
    #   ],
    #   "bottom_items": [
    #     {"id": "settings", "label": "Settings", "icon": "⚙"}
    #   ]
    # }
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static


@dataclass(frozen=True)
class HamburgerItem:
    """One entry in the hamburger menu.

    Attributes:
        id: Identifier delivered with ``ItemSelected`` when the user clicks
            this item. Empty for group headers and separators.
        label: Display text shown when the menu is expanded.
        icon: Optional symbol shown both collapsed and expanded.
        is_group_header: If True, renders as a dimmed group label and is
            NOT clickable. Use ``HamburgerItem.group(...)`` factory.
        is_separator: If True, renders as a thin horizontal line. Use
            ``HamburgerItem.separator()`` factory.
    """

    id: str
    label: str
    icon: str = ""
    is_group_header: bool = False
    is_separator: bool = False

    @classmethod
    def group(cls, label: str) -> "HamburgerItem":
        """Factory: create a group header (visual section title)."""
        return cls(id="", label=label, is_group_header=True)

    @classmethod
    def separator(cls) -> "HamburgerItem":
        """Factory: create a separator line between items."""
        return cls(id="", label="", is_separator=True)


def _item_from_dict(data: dict) -> HamburgerItem:
    """Build an item from a JSON dict (see ``HamburgerMenu.from_json``)."""
    if data.get("separator"):
        return HamburgerItem.separator()
    if "group" in data:
        return HamburgerItem.group(str(data["group"]))
    return HamburgerItem(
        id=str(data.get("id", "")),
        label=str(data.get("label", "")),
        icon=str(data.get("icon", "")),
    )


class _HamburgerEntry(Static, can_focus=True):
    """Single row in the hamburger menu.

    Renders different content depending on the parent menu's expanded state.
    Click posts an ``Activated`` message that the menu translates into the
    public ``ItemSelected`` event.
    """

    DEFAULT_CSS = """
    _HamburgerEntry {
        height: 1;
        padding: 0 1;
        color: $text;
    }
    _HamburgerEntry:hover {
        background: $surface;
    }
    _HamburgerEntry.-selected {
        background: $accent;
        color: $text;
        text-style: bold;
    }
    _HamburgerEntry.-group {
        color: $text-muted;
        text-style: bold;
        background: transparent;
    }
    _HamburgerEntry.-group:hover {
        background: transparent;
    }
    _HamburgerEntry.-separator {
        color: $surface-lighten-1;
        background: transparent;
    }
    _HamburgerEntry.-separator:hover {
        background: transparent;
    }
    _HamburgerEntry.-toggle {
        background: $accent;
        color: $text;
        text-style: bold;
    }
    _HamburgerEntry.-toggle:hover {
        background: $accent-darken-1;
    }
    """

    class Activated(Message):
        """User clicked an item — internal message, translated to ItemSelected."""

        def __init__(self, item_id: str, is_toggle: bool = False) -> None:
            super().__init__()
            self.item_id = item_id
            self.is_toggle = is_toggle

    def __init__(
        self,
        item: HamburgerItem,
        *,
        expanded: bool = False,
        is_toggle: bool = False,
        toggle_icon: str = "≡",
        show_tooltip: bool = False,
        **kwargs: object,
    ) -> None:
        # Pre-compute the initial content so the entry already shows its icon
        # the moment it is mounted. Relying on a post-mount refresh proved
        # unreliable because the watcher only fires when the reactive value
        # actually changes — for the default collapsed state that meant the
        # entries stayed empty until the user clicked toggle.
        content = self._compute_content(item, expanded, is_toggle, toggle_icon)
        super().__init__(content, **kwargs)
        self._item = item
        self._is_toggle = is_toggle
        self._toggle_icon = toggle_icon
        if item.is_group_header:
            self.add_class("-group")
        elif item.is_separator:
            self.add_class("-separator")
        if is_toggle:
            self.add_class("-toggle")
            self.can_focus = False
        if show_tooltip and not is_toggle and not item.is_group_header and not item.is_separator:
            self.tooltip = item.label

    @staticmethod
    def _compute_content(
        item: HamburgerItem, expanded: bool, is_toggle: bool, toggle_icon: str,
    ) -> str:
        """Map the entry+state to the string we render."""
        if is_toggle:
            return toggle_icon
        if item.is_separator:
            return "─"
        if item.is_group_header:
            return item.label.upper() if expanded else " "
        icon = item.icon or " "
        return f"{icon}  {item.label}" if expanded else icon

    def render_for(self, expanded: bool) -> None:
        """Re-render content for a new expanded state (called on toggle)."""
        self.update(
            self._compute_content(
                self._item, expanded, self._is_toggle, self._toggle_icon,
            )
        )

    def on_click(self) -> None:
        """Click → activate. Group headers and separators are inert."""
        if self._is_toggle:
            self.post_message(self.Activated("", is_toggle=True))
            return
        if self._item.is_group_header or self._item.is_separator:
            return
        if self._item.id:
            self.post_message(self.Activated(self._item.id))


class HamburgerMenu(Widget):
    """Collapsible side menu with icon-only / icon-plus-label states.

    Click the hamburger icon at the top, or call ``menu.toggle()``, to switch
    between collapsed (narrow, icons only) and expanded (wide, icons + labels).

    Subscribe to ``HamburgerMenu.ItemSelected`` to react to user clicks on
    items. Group headers and separators don't emit events.
    """

    DEFAULT_CSS = """
    HamburgerMenu {
        height: 1fr;
        background: $panel;
        border-right: solid $accent;
        layout: vertical;
    }
    HamburgerMenu #hb-items {
        height: 1fr;
        background: $panel;
    }
    HamburgerMenu #hb-bottom {
        dock: bottom;
        height: auto;
        border-top: solid $surface-lighten-1;
        background: $panel;
    }
    """

    expanded: reactive[bool] = reactive(False, init=False)
    selected_id: reactive[str] = reactive("", init=False)

    class ItemSelected(Message):
        """User selected a menu item."""

        def __init__(self, item_id: str) -> None:
            super().__init__()
            self.item_id = item_id

    class Toggled(Message):
        """Menu was expanded or collapsed."""

        def __init__(self, expanded: bool) -> None:
            super().__init__()
            self.expanded = expanded

    def __init__(
        self,
        items: list[HamburgerItem],
        bottom_items: list[HamburgerItem] | None = None,
        collapsed_width: int = 6,
        expanded_width: int = 26,
        toggle_icon: str = "≡",
        initial_expanded: bool = False,
        animate_duration: float = 0.15,
        show_tooltips: bool = False,
        **kwargs: object,
    ) -> None:
        """Initialise the menu.

        Args:
            items: Top-level entries in the scrollable upper section.
            bottom_items: Items docked to the bottom (e.g. Settings).
            collapsed_width: Width in cells when collapsed (default 6).
            expanded_width: Width in cells when expanded (default 26).
            toggle_icon: Symbol shown in the toggle row at the top.
            initial_expanded: Start expanded if True (default False).
            animate_duration: Seconds for the width animation (0 disables).
            show_tooltips: If True, hovering a collapsed icon shows the
                label as a tooltip. Off by default — tooltips compete
                visually with the menu and the user can just expand the
                menu to read labels.
        """
        super().__init__(**kwargs)
        self._items = list(items)
        self._bottom_items = list(bottom_items or [])
        self._collapsed_width = collapsed_width
        self._expanded_width = expanded_width
        self._toggle_icon = toggle_icon
        self._animate_duration = animate_duration
        self._show_tooltips = show_tooltips
        # Set the reactive AFTER everything else, so watch_expanded can rely on
        # all attributes being present.
        self._initial_expanded = initial_expanded

    def compose(self) -> ComposeResult:
        # Toggle row at the top — virtual "item" with empty id
        yield _HamburgerEntry(
            HamburgerItem(id="", label="", icon=self._toggle_icon),
            expanded=self._initial_expanded,
            is_toggle=True,
            toggle_icon=self._toggle_icon,
            show_tooltip=self._show_tooltips,
            id="hb-toggle",
        )
        with VerticalScroll(id="hb-items"):
            for idx, item in enumerate(self._items):
                yield _HamburgerEntry(
                    item, expanded=self._initial_expanded,
                    show_tooltip=self._show_tooltips,
                    id=f"hb-top-{idx}",
                )
        if self._bottom_items:
            with Vertical(id="hb-bottom"):
                for idx, item in enumerate(self._bottom_items):
                    yield _HamburgerEntry(
                        item, expanded=self._initial_expanded,
                        show_tooltip=self._show_tooltips,
                        id=f"hb-bot-{idx}",
                    )

    def on_mount(self) -> None:
        # Apply initial width directly (no animation on first show)
        initial_w = self._expanded_width if self._initial_expanded else self._collapsed_width
        self.styles.width = initial_w
        # Sync the reactive — this only triggers the watcher when the value
        # actually changes from its default. With initial_expanded=False
        # (the default) it doesn't fire, so we render the entries explicitly
        # afterwards. Otherwise the toggle and item icons stay empty until
        # the user clicks toggle.
        self.expanded = self._initial_expanded
        self._refresh_entries()

    # --- Public API ----------------------------------------------------

    def toggle(self) -> None:
        """Toggle between collapsed and expanded."""
        self.expanded = not self.expanded

    def expand(self) -> None:
        self.expanded = True

    def collapse(self) -> None:
        self.expanded = False

    def set_selected(self, item_id: str) -> None:
        """Programmatically mark an item as selected (visual highlight only)."""
        self.selected_id = item_id

    # --- Reactive watchers ---------------------------------------------

    def watch_expanded(self, expanded: bool) -> None:
        """Animate the width and re-render entries when state changes."""
        target = self._expanded_width if expanded else self._collapsed_width
        if self._animate_duration > 0 and self.is_mounted:
            self.styles.animate("width", value=target, duration=self._animate_duration)
        else:
            self.styles.width = target
        self._refresh_entries()
        if self.is_mounted:
            self.post_message(self.Toggled(expanded))

    def watch_selected_id(self, new_id: str) -> None:
        """Update visual highlight when the selected id changes."""
        for entry in self.query(_HamburgerEntry):
            if entry._is_toggle:
                continue
            if entry._item.id == new_id and new_id:
                entry.add_class("-selected")
            else:
                entry.remove_class("-selected")

    def _refresh_entries(self) -> None:
        """Re-render every entry for the current expanded state."""
        if not self.is_mounted:
            return
        for entry in self.query(_HamburgerEntry):
            entry.render_for(self.expanded)

    # --- Internal message handling -------------------------------------

    def on__hamburger_entry_activated(
        self, event: _HamburgerEntry.Activated,
    ) -> None:
        """Translate the internal Activated message into the public API."""
        event.stop()
        if event.is_toggle:
            self.toggle()
            return
        if event.item_id:
            self.selected_id = event.item_id
            self.post_message(self.ItemSelected(event.item_id))

    # --- JSON loader ---------------------------------------------------

    @classmethod
    def from_json(
        cls, path: str | Path, **kwargs: object,
    ) -> "HamburgerMenu":
        """Construct a menu from a JSON config file.

        Expected structure::

            {
              "items": [
                {"id": "new", "label": "New", "icon": "+"},
                {"group": "Accounts"},
                {"id": "inbox", "label": "Inbox", "icon": "📧"},
                {"separator": true}
              ],
              "bottom_items": [
                {"id": "settings", "label": "Settings", "icon": "⚙"}
              ]
            }

        Selection events still need to be wired up in Python — JSON cannot
        carry callbacks.
        """
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        items = [_item_from_dict(d) for d in data.get("items", [])]
        bottom = [_item_from_dict(d) for d in data.get("bottom_items", [])]
        return cls(items=items, bottom_items=bottom, **kwargs)
