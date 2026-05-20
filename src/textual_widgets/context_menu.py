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
    def separator(cls) -> ContextMenuItem:
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
        border: round $accent;
        padding: 0 1;
    }
    /* OptionList in allen States borderless halten — sonst flackern Textuals
       Default-Borders kurz auf bei Focus-Wechsel oder Item-Auswahl ueber den
       aeusseren Vertical-Border drueber. */
    ContextMenuScreen OptionList,
    ContextMenuScreen OptionList:focus,
    ContextMenuScreen OptionList:hover,
    ContextMenuScreen OptionList.-active {
        background: transparent;
        border: none;
        padding: 0;
        width: 1fr;
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
        """Setzt die Breite und positioniert das Menue (mit Off-Screen-Schutz).

        Eine Phase, deterministisch: aus den Items eine bewusst leicht
        ueberschaetzte Groesse berechnen und damit clampen. Lieber das
        Menue 1-2 Zellen zu hoch ausgeben als unten abgeschnitten —
        und kein Reposition-Sprung in einem zweiten Frame.
        """
        # Breite dynamisch aus dem laengsten Eintrag setzen. Ohne das blaeht
        # die OptionList (width: 1fr) den auto-Container bis max-width auf.
        menu_w, _ = self._estimate_size()
        self.query_one(Vertical).styles.width = menu_w

        if self._at is not None:
            self._apply_position()
        else:
            # Fallback: zentriert (z.B. bei Tastatur-Trigger ohne Click-Coords)
            self.styles.align = ("center", "middle")
        self.query_one(OptionList).focus()

    def _apply_position(self) -> None:
        """Positioniert den Menue-Container am Klick-Punkt mit Off-Screen-Schutz."""
        if self._at is None:
            return
        container = self.query_one(Vertical)
        x, y = self._at
        term_w, term_h = self.app.size
        menu_w, menu_h = self._estimate_size()
        x = max(0, min(x, term_w - menu_w))
        y = max(0, min(y, term_h - menu_h))
        container.styles.offset = (x, y)

    def _estimate_size(self) -> tuple[int, int]:
        """Berechnet die erwartete Menue-Groesse vor dem Render — bewusst
        leicht UEBER-konservativ.

        Beruecksichtigt:
        - Maximale Label-Breite (inkl. Icon)
        - Optionale Shortcut-Spalte rechts (mit 2 Leerzeichen Abstand)
        - 2 Zellen Padding (CSS: padding: 0 1) horizontal
        - 2 Zellen Border (CSS: border: thick) auf beiden Achsen
        - min-width 16 / max-width 60 (CSS-Schranken)
        - +2 Zellen Sicherheitsmarge horizontal und vertikal — falls Textuals
          OptionList-Defaults (border tall, padding 0 1) trotz Override
          durchschlagen oder das Theme zusaetzliche Zellen verbraucht.

        Folge: das Menue erscheint im Worst Case 2 Zeilen hoeher als ideal
        (statt direkt unter dem Cursor), bleibt aber immer vollstaendig
        sichtbar. Kein Reposition-Sprung in einem spaeteren Frame.
        """
        visible = [i for i in self._items if not i.is_separator]
        max_label = max(
            (len(self._format_label(i)) for i in visible),
            default=0,
        )
        max_shortcut = max((len(i.shortcut) for i in visible), default=0)

        content_w = max_label
        if max_shortcut > 0:
            content_w += 2 + max_shortcut

        # +4 fest (2 Padding + 2 Border) — kein Width-Safety mehr, da das den
        # Off-Screen-Clamp nach links ueberschiessen liess. Hoehen-Safety bleibt,
        # weil dort auch Cursor-Position-Effekte zaehlen.
        total_w = max(16, min(60, content_w + 4))
        # +2 fest (Border) +2 Sicherheit
        total_h = max(3, len(self._items) + 4)

        return (total_w, total_h)

    def on_option_list_option_selected(
        self,
        event: OptionList.OptionSelected,
    ) -> None:
        """Wird ausgeloest, wenn der User ein Item per Maus oder Tastatur waehlt."""
        option_id = event.option.id
        self.dismiss(str(option_id) if option_id else None)

    def on_click(self, event: Click) -> None:
        """Klick im Modal: immer hier konsumieren, sonst Klick ausserhalb → Cancel.

        Wichtig: ``event.stop()`` unbedingt — sonst bubblet derselbe Klick,
        der das Menue gerade ausgewaehlt/abgebrochen hat, nach dem
        ``dismiss()`` weiter zu dem Widget UNTER dem Modal (z.B. einer
        DataTable, deren Row-Selection sonst sofort mitfeuert).
        """
        event.stop()
        try:
            container = self.query_one(Vertical)
            if not container.region.contains(event.screen_x, event.screen_y):
                self.dismiss(None)
        except Exception:
            pass

    def action_cancel(self) -> None:
        """ESC schliesst das Menue ohne Auswahl."""
        self.dismiss(None)
