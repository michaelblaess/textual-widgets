"""Resizable splitter / divider widgets fuer Textual.

Zwei Varianten:
- ``VerticalSplitter`` — 1 Zelle breite vertikale Linie zwischen zwei Panels in
  einem ``Horizontal``-Container. Drag horizontal aendert die Breite des linken
  (target) Panels.
- ``HorizontalSplitter`` — 1 Zelle hohe horizontale Linie zwischen zwei Panels in
  einem ``Vertical``-Container. Drag vertikal aendert die Hoehe des oberen
  (target) Panels.

Die Bibliothek persistiert nichts. Nach einem abgeschlossenen Drag wird eine
``Resized``-Message gepostet — der Konsument speichert/laedt selbst.

Usage:

    from textual_widgets import VerticalSplitter, HorizontalSplitter

    class MyApp(App):
        def compose(self) -> ComposeResult:
            with Horizontal():
                yield FolderBrowser(id="folder", classes="left-pane")
                yield VerticalSplitter(target_id="folder", min_size=15)
                with Vertical():
                    yield FileTable(id="files", classes="top-pane")
                    yield HorizontalSplitter(target_id="files", min_size=5)
                    yield Lyrics(classes="bottom-pane")

        def on_vertical_splitter_resized(
            self, event: VerticalSplitter.Resized,
        ) -> None:
            self._settings.set_panel_width(event.target_id, event.size)
"""
from __future__ import annotations

from textual import events
from textual.message import Message
from textual.widget import Widget


class _SplitterBase(Widget):
    """Gemeinsame Logik fuer vertikalen und horizontalen Splitter."""

    class Resized(Message):
        """Wird nach Abschluss eines Drag-Vorgangs gepostet.

        Der Konsument kann ``target_id`` und die neue ``size`` zur
        Persistierung verwenden (z.B. in Settings speichern).
        """

        def __init__(self, target_id: str, size: int) -> None:
            super().__init__()
            self.target_id = target_id
            self.size = size

    def __init__(
        self,
        target_id: str | None = None,
        min_size: int = 5,
        max_size: int | None = None,
        **kwargs: object,
    ) -> None:
        """Initialisiert den Splitter.

        Args:
            target_id: ID des Widgets, dessen Groesse durch Drag geaendert wird.
                Wenn None, wird das vorhergehende Geschwister-Widget im
                gleichen Container verwendet.
            min_size: Minimale Groesse des Targets in Zellen (Default 5).
            max_size: Maximale Groesse des Targets in Zellen (Default unbegrenzt).
        """
        super().__init__(**kwargs)
        self._target_id = target_id
        self._min_size = max(1, min_size)
        self._max_size = max_size
        self._dragging = False

    def _get_target(self) -> Widget | None:
        """Findet das Target-Widget — entweder per ID oder als vorigen Sibling."""
        if self._target_id:
            try:
                return self.app.query_one(f"#{self._target_id}", Widget)
            except Exception:
                return None
        # Fallback: vorhergehendes Geschwister im gleichen Container
        if self.parent is None:
            return None
        try:
            siblings = list(self.parent.children)
            idx = siblings.index(self)
            if idx > 0:
                return siblings[idx - 1]
        except (ValueError, IndexError):
            return None
        return None

    def _clamp(self, size: int) -> int:
        """Begrenzt die Groesse auf min_size .. max_size."""
        size = max(self._min_size, size)
        if self._max_size is not None:
            size = min(self._max_size, size)
        return size

    def on_mouse_down(self, event: events.MouseDown) -> None:
        """Startet das Drag — fangen alle weiteren Mouse-Events ein."""
        self.capture_mouse()
        self._dragging = True
        self.add_class("-dragging")
        event.stop()

    def on_mouse_up(self, event: events.MouseUp) -> None:
        """Beendet das Drag und postet ggf. die Resized-Message."""
        if not self._dragging:
            return
        self.release_mouse()
        self._dragging = False
        self.remove_class("-dragging")
        target = self._get_target()
        if target is not None and target.id:
            self.post_message(self.Resized(target.id, self._current_size(target)))
        event.stop()

    # Subklassen ueberschreiben:
    def _current_size(self, target: Widget) -> int:
        """Liest die aktuelle Groesse (Breite/Hoehe) des Targets."""
        raise NotImplementedError

    def on_mouse_move(self, event: events.MouseMove) -> None:
        """Beim Dragging Target-Groesse anhand der Mausposition setzen."""
        raise NotImplementedError


class VerticalSplitter(_SplitterBase):
    """1 Zelle breite vertikale Trennlinie — Drag aendert die Target-Breite.

    Soll in einem horizontal-orientierten Container sitzen, das Target ist
    typischerweise das linke Panel davor. Das Panel braucht eine konkrete
    Breite (kein ``1fr``), damit Resizing wirkt.
    """

    DEFAULT_CSS = """
    VerticalSplitter {
        width: 1;
        height: 1fr;
        background: $surface-darken-1;
    }
    VerticalSplitter:hover {
        background: $accent;
    }
    VerticalSplitter.-dragging {
        background: $accent;
    }
    """

    def _current_size(self, target: Widget) -> int:
        return int(target.outer_size.width)

    def on_mouse_move(self, event: events.MouseMove) -> None:
        if not self._dragging:
            return
        target = self._get_target()
        if target is None:
            return
        # Mauspositionen sind relativ zum Splitter — fuer Absolute brauchen
        # wir screen_x. Neue Breite = Cursor X - linke Kante des Targets.
        new_width = event.screen_x - target.region.x
        target.styles.width = self._clamp(new_width)


class HorizontalSplitter(_SplitterBase):
    """1 Zelle hohe horizontale Trennlinie — Drag aendert die Target-Hoehe.

    Soll in einem vertikal-orientierten Container sitzen, das Target ist
    typischerweise das obere Panel davor. Das Panel braucht eine konkrete
    Hoehe (kein ``1fr``), damit Resizing wirkt.
    """

    DEFAULT_CSS = """
    HorizontalSplitter {
        width: 1fr;
        height: 1;
        background: $surface-darken-1;
    }
    HorizontalSplitter:hover {
        background: $accent;
    }
    HorizontalSplitter.-dragging {
        background: $accent;
    }
    """

    def _current_size(self, target: Widget) -> int:
        return int(target.outer_size.height)

    def on_mouse_move(self, event: events.MouseMove) -> None:
        if not self._dragging:
            return
        target = self._get_target()
        if target is None:
            return
        new_height = event.screen_y - target.region.y
        target.styles.height = self._clamp(new_height)
