"""Wiederverwendbares Kontext-Menue als ModalScreen.

Public API:
    - `ContextMenuItem` — Dataclass fuer ein Menue-Item (id, label, optional icon,
      shortcut, enabled, is_separator).
    - `ContextMenuScreen[str | None]` — ModalScreen, gibt den `id` der gewaehlten
      Aktion zurueck oder `None` bei Abbruch (ESC oder Click ausserhalb).

Usage:
    from textual_widgets import ContextMenuItem, ContextMenuScreen

    class MyWidget(Widget):
        def on_click(self, event: Click) -> None:
            if event.button != 3:  # nur Rechtsklick
                return
            items = [
                ContextMenuItem("rename", "Umbenennen", icon="✎", shortcut="Ctrl+R"),
                ContextMenuItem("delete", "Loeschen", icon="✕", enabled=can_delete),
                ContextMenuItem.separator(),
                ContextMenuItem("info", "Eigenschaften", shortcut="Ctrl+I"),
            ]
            self.app.push_screen(
                ContextMenuScreen(items, at=(event.screen_x, event.screen_y)),
                callback=self._on_menu_action,
            )

        def _on_menu_action(self, action_id: str | None) -> None:
            if action_id == "rename":
                ...
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.events import Click
from textual.screen import ModalScreen
from textual.widgets import OptionList
from textual.widgets.option_list import Option


@dataclass(frozen=True)
class ContextMenuItem:
    """Ein Eintrag im Kontextmenue.

    Attributes:
        id: Identifier, der bei Auswahl an den Callback uebergeben wird.
            Bei Separatoren leer (wird nicht zurueckgegeben).
        label: Anzeigetext des Items.
        icon: Optionales Praefix-Symbol (z.B. Emoji, Unicode-Zeichen).
        shortcut: Optionaler Tastatur-Shortcut zur Anzeige rechts (z.B. "Ctrl+R").
            REIN VISUELL — der Konsument muss das Triggern selbst implementieren.
        enabled: Wenn False, wird das Item disabled (ausgegraut, nicht waehlbar).
        is_separator: Wenn True, wird statt eines Items eine Trennlinie gerendert.
    """

    id: str
    label: str
    icon: str = ""
    shortcut: str = ""
    enabled: bool = True
    is_separator: bool = False

    @classmethod
    def separator(cls) -> "ContextMenuItem":
        """Factory fuer eine Trenner-Zeile zwischen Item-Gruppen."""
        return cls(id="", label="", is_separator=True)


class ContextMenuScreen(ModalScreen[str | None]):
    """Kontext-Menue als ModalScreen.

    Gibt den `id` der gewaehlten Aktion zurueck oder `None` bei Abbruch
    (ESC oder Klick ausserhalb des Menue-Bereichs).
    """

    DEFAULT_CSS = """
    ContextMenuScreen {
        background: transparent;
    }
    ContextMenuScreen > Vertical {
        width: auto;
        height: auto;
        min-width: 16;
        max-width: 60;
        background: $surface;
        border: thick $accent;
        padding: 0 1;
    }
    ContextMenuScreen OptionList {
        background: transparent;
        border: none;
        padding: 0;
        height: auto;
    }
    """

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("escape", "cancel", show=False),
    ]

    def __init__(
        self,
        items: list[ContextMenuItem],
        at: tuple[int, int] | None = None,
    ) -> None:
        """Erstellt das Kontextmenue.

        Args:
            items: Liste der anzuzeigenden Items. Mindestens ein nicht-Separator-Item.
            at: Bildschirm-Koordinaten (x, y) fuer die Positionierung. Typisch
                `(event.screen_x, event.screen_y)` aus einem Click-Handler.
                Wenn None, wird das Menue zentriert dargestellt (geeignet bei
                Tastatur-Trigger ohne Maus-Position).
        """
        super().__init__()
        self._items = list(items)
        self._at = at

    def compose(self) -> ComposeResult:
        """Baut die OptionList aus den Items auf, mit rechts-buendigen Shortcuts."""
        # Maximale Breiten ermitteln, damit Shortcuts rechtsbuendig ausgerichtet werden
        visible = [i for i in self._items if not i.is_separator]
        max_label = max(
            (len(self._format_label(i)) for i in visible),
            default=0,
        )
        max_shortcut = max((len(i.shortcut) for i in visible), default=0)

        # In Textual ist `None` der Separator-Marker zwischen Optionen.
        options: list[Option | None] = []
        for item in self._items:
            if item.is_separator:
                options.append(None)
                continue

            label = self._format_label(item)
            rich_label = Text()
            rich_label.append(label.ljust(max_label))
            if max_shortcut > 0:
                rich_label.append("  ")
                rich_label.append(item.shortcut.rjust(max_shortcut), style="dim")

            options.append(Option(rich_label, id=item.id, disabled=not item.enabled))

        with Vertical():
            yield OptionList(*options, id="menu-options")

    @staticmethod
    def _format_label(item: ContextMenuItem) -> str:
        """Kombiniert Icon und Label mit einem Leerzeichen."""
        if item.icon:
            return f"{item.icon} {item.label}"
        return item.label

    def on_mount(self) -> None:
        """Positioniert das Menue am Klick-Punkt (mit Off-Screen-Schutz)."""
        container = self.query_one(Vertical)
        if self._at is not None:
            x, y = self._at
            term_w, term_h = self.app.size
            # Geschaetzte Menue-Groesse, falls noch nicht gerendert
            menu_w = container.outer_size.width or 30
            menu_h = container.outer_size.height or len(self._items) + 2
            # An Rand pinnen, damit das Menue nicht aus dem Terminal herausragt
            x = max(0, min(x, term_w - menu_w))
            y = max(0, min(y, term_h - menu_h))
            container.styles.offset = (x, y)
        else:
            # Fallback: zentriert (z.B. bei Tastatur-Trigger ohne Click-Coords)
            self.styles.align = ("center", "middle")
        self.query_one(OptionList).focus()

    def on_option_list_option_selected(
        self, event: OptionList.OptionSelected,
    ) -> None:
        """Wird ausgeloest, wenn der User ein Item per Maus oder Tastatur waehlt."""
        option_id = event.option.id
        self.dismiss(str(option_id) if option_id else None)

    def on_click(self, event: Click) -> None:
        """Klick ausserhalb des Menue-Containers → Cancel."""
        try:
            container = self.query_one(Vertical)
            if not container.region.contains(event.screen_x, event.screen_y):
                self.dismiss(None)
        except Exception:
            pass

    def action_cancel(self) -> None:
        """ESC schliesst das Menue ohne Auswahl."""
        self.dismiss(None)
