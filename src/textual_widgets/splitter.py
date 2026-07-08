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

from rich.text import Text
from textual import events
from textual.app import RenderResult
from textual.message import Message
from textual.widget import Widget

# Drag-Handle-Glyphen — Box-Drawing "light quadruple dash" Zeichen, sehen wie
# gestrichelte Linien aus und wirken intuitiv als Greifgriff.
_VERTICAL_HANDLE_CHAR = "┊"
_HORIZONTAL_HANDLE_CHAR = "┄"
# Anzahl Zellen fuer den zentrierten Handle (Rest bleibt einfarbig)
_HANDLE_SIZE = 4

# Icon-Glyphen fuer die optionale Titelzeile (nur BMP-Zeichen mit Text-
# Praesentation, damit sie monochrom und in Text-Breite rendern):
#   Collapse offen/zu, Close. Kein Emoji (wuerde farbig/breit rendern).
_COLLAPSE_OPEN = "▾"
_COLLAPSE_CLOSED = "▸"
_CLOSE_GLYPH = "×"


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
        # Merkt, ob der letzte Mouse-Zyklus ein Drag war. Verhindert, dass ein
        # abgeschlossener Drag zusaetzlich als Icon-Klick interpretiert wird.
        self._drag_happened = False

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
        """Startet das Drag — fangen alle weiteren Mouse-Events ein.

        Ausserhalb der Drag-Zone (z.B. ueber einem Titel-Icon) wird KEIN Drag
        gestartet; der Klick laeuft dann normal weiter zum ``on_click``-Handler.
        """
        self._drag_happened = False
        if not self._is_drag_zone(event):
            return
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
        self._drag_happened = True
        self.remove_class("-dragging")
        target = self._get_target()
        if target is not None and target.id:
            self.post_message(self.Resized(target.id, self._current_size(target)))
        event.stop()

    def _is_drag_zone(self, event: events.MouseDown) -> bool:
        """Ob an der Mausposition ein Drag beginnen darf.

        Basisverhalten: die gesamte Flaeche ist Drag-Zone. Subklassen mit
        Titelzeile/Icons ueberschreiben das, um Icon-Regionen auszunehmen.
        Bewusst KEIN ``on_*``-Handler, damit Textual es nicht ueber die MRO
        doppelt dispatcht.
        """
        return True

    # Subklassen muessen `on_mouse_move` und `_current_size` definieren.
    # Wichtig: `on_mouse_move` darf NICHT in dieser Basisklasse stehen —
    # Textual dispatcht `on_*`-Handler ueber die gesamte MRO und ruft sonst
    # die Basisversion zusaetzlich zur Subklassen-Implementierung auf.
    def _current_size(self, target: Widget) -> int:
        """Liest die aktuelle Groesse (Breite/Hoehe) des Targets."""
        raise NotImplementedError


class VerticalSplitter(_SplitterBase):
    """1 Zelle breite vertikale Trennlinie — Drag aendert die Target-Breite.

    Soll in einem horizontal-orientierten Container sitzen, das Target ist
    typischerweise das linke Panel davor. Das Panel braucht eine konkrete
    Breite (kein ``1fr``), damit Resizing wirkt.
    """

    class Resized(_SplitterBase.Resized):
        """Drag beendet — Handler: ``on_vertical_splitter_resized``.

        Muss hier redeklariert werden, sonst leitet Textual den Handler-Namen
        aus ``_SplitterBase`` ab (``on__splitter_base_resized``) und die
        erwarteten ``on_vertical_splitter_resized``-Handler feuern nie.
        """

    DEFAULT_CSS = """
    VerticalSplitter {
        width: 1;
        height: 1fr;
        background: $surface-darken-1;
        color: $text-muted;
    }
    VerticalSplitter:hover {
        background: $accent;
        color: $text;
    }
    VerticalSplitter.-dragging {
        background: $accent;
        color: $text;
    }
    """

    def render(self) -> RenderResult:
        """Zeichnet einen zentrierten Drag-Handle aus gestrichelten Zeichen."""
        h = max(1, self.size.height)
        handle_n = min(_HANDLE_SIZE, h)
        pad_top = (h - handle_n) // 2
        return "\n".join(_VERTICAL_HANDLE_CHAR if pad_top <= i < pad_top + handle_n else " " for i in range(h))

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

    Optional traegt der Splitter eine Titelzeile im Visual-Studio-Stil: Titel
    links, gestrichelter Drag-Handle in der Mitte, Action-Icons (Einklappen,
    Schliessen) rechts. Wird ueber ``title``/``show_collapse``/``show_close``
    aktiviert. Ohne diese Parameter verhaelt sich der Splitter unveraendert
    (zentrierter Handle).
    """

    class Resized(_SplitterBase.Resized):
        """Drag beendet — Handler: ``on_horizontal_splitter_resized``."""

    class CloseRequested(Message):
        """Close-Icon (``×``) geklickt — Handler:
        ``on_horizontal_splitter_close_requested``.

        Der Splitter blendet nichts selbst aus; die App entscheidet, was
        "schliessen" bedeutet (Panel + Splitter verbergen o.ae.).
        """

    class CollapseRequested(Message):
        """Collapse-Icon geklickt — Handler:
        ``on_horizontal_splitter_collapse_requested``.

        ``collapsed`` traegt den neuen Zustand (True = eingeklappt). Der
        Splitter aktualisiert nur sein Glyph; die App klappt das Panel ein.
        """

        def __init__(self, collapsed: bool) -> None:
            super().__init__()
            self.collapsed = collapsed

    DEFAULT_CSS = """
    HorizontalSplitter {
        width: 1fr;
        height: 1;
        background: $surface-darken-1;
        color: $text-muted;
    }
    HorizontalSplitter:hover {
        background: $accent;
        color: $text;
    }
    HorizontalSplitter.-dragging {
        background: $accent;
        color: $text;
    }
    /* Titelzeilen-Variante: als ruhiger Balken, NICHT die ganze Leiste beim
       Hover accent faerben (nur die Icons heben sich per Reverse-Style ab). */
    HorizontalSplitter.-titled {
        background: $panel;
        color: $text-muted;
    }
    HorizontalSplitter.-titled:hover {
        background: $panel;
        color: $text-muted;
    }
    """

    def __init__(
        self,
        target_id: str | None = None,
        min_size: int = 5,
        max_size: int | None = None,
        *,
        title: str = "",
        show_collapse: bool = False,
        show_close: bool = False,
        **kwargs: object,
    ) -> None:
        """Initialisiert den horizontalen Splitter.

        Args:
            target_id: ID des Widgets, dessen Hoehe durch Drag geaendert wird.
            min_size: Minimale Target-Hoehe in Zellen.
            max_size: Maximale Target-Hoehe in Zellen (Default unbegrenzt).
            title: Optionaler Titel links. Ist er gesetzt (oder eines der
                ``show_*``-Flags), rendert der Splitter als Titelzeile.
            show_collapse: Collapse-Icon (``▾``/``▸``) rechts anzeigen.
            show_close: Close-Icon (``×``) rechts anzeigen.
        """
        super().__init__(target_id, min_size, max_size, **kwargs)
        self._title = title
        self._show_collapse = show_collapse
        self._show_close = show_close
        self._collapsed = False
        # Aktuell gehovertes Icon ("collapse"/"close"/None) fuer das Highlight.
        self._hover_action: str | None = None
        # Absolute Klick-Regionen der Icons: (x0, x1, action). In render() gefuellt.
        self._icon_regions: list[tuple[int, int, str]] = []
        if title or show_collapse or show_close:
            self.add_class("-titled")

    @property
    def collapsed(self) -> bool:
        """Ob der Collapse-Zustand aktiv ist (nur Anzeige-Glyph)."""
        return self._collapsed

    def set_title(self, title: str) -> None:
        """Setzt den Titel zur Laufzeit und zeichnet neu."""
        self._title = title
        self.set_class(bool(title or self._show_collapse or self._show_close), "-titled")
        self.refresh()

    def set_collapsed(self, collapsed: bool) -> None:
        """Setzt den Collapse-Zustand (Glyph) ohne eine Message zu posten."""
        if self._collapsed != collapsed:
            self._collapsed = collapsed
            self.refresh()

    def _has_titlebar(self) -> bool:
        """Ob die Titelzeilen-Variante aktiv ist."""
        return bool(self._title) or self._show_collapse or self._show_close

    def render(self) -> RenderResult:
        """Zeichnet den Drag-Handle bzw. die Titelzeile.

        Ohne Titel/Icons: zentrierter, gestrichelter Handle (Alt-Verhalten).
        Mit Titelzeile: Titel links, Handle als Fueller, Icons rechts.
        """
        w = max(1, self.size.width)
        if not self._has_titlebar():
            handle_n = min(_HANDLE_SIZE, w)
            pad_left = (w - handle_n) // 2
            pad_right = w - handle_n - pad_left
            return " " * pad_left + _HORIZONTAL_HANDLE_CHAR * handle_n + " " * pad_right

        left = f" {self._title} " if self._title else ""

        # Icon-Zellen mit fuehrendem/abschliessendem Space als Klick-Puffer.
        icon_cells: list[tuple[str, str]] = []
        if self._show_collapse:
            glyph = _COLLAPSE_CLOSED if self._collapsed else _COLLAPSE_OPEN
            icon_cells.append(("collapse", f" {glyph} "))
        if self._show_close:
            icon_cells.append(("close", f" {_CLOSE_GLYPH} "))
        right_len = sum(len(text) for _, text in icon_cells)

        fill_n = max(0, w - len(left) - right_len)

        line = Text(no_wrap=True, overflow="ellipsis")
        if left:
            line.append(left, style="bold")
        line.append(_HORIZONTAL_HANDLE_CHAR * fill_n)

        self._icon_regions = []
        x = len(left) + fill_n
        for action, text in icon_cells:
            style = "bold reverse" if self._hover_action == action else "bold"
            line.append(text, style=style)
            self._icon_regions.append((x, x + len(text), action))
            x += len(text)
        return line

    def _action_at(self, x: int) -> str | None:
        """Liefert die Icon-Aktion an Spalte ``x`` (relativ zum Widget)."""
        for x0, x1, action in self._icon_regions:
            if x0 <= x < x1:
                return action
        return None

    def _is_drag_zone(self, event: events.MouseDown) -> bool:
        """Kein Drag ueber einem Icon starten."""
        return self._action_at(event.x) is None

    def _current_size(self, target: Widget) -> int:
        return int(target.outer_size.height)

    def on_mouse_move(self, event: events.MouseMove) -> None:
        if self._dragging:
            target = self._get_target()
            if target is None:
                return
            new_height = event.screen_y - target.region.y
            target.styles.height = self._clamp(new_height)
            return
        # Kein Drag: Icon-Hover-Highlight aktualisieren (nur bei Wechsel).
        new_hover = self._action_at(event.x) if self._has_titlebar() else None
        if new_hover != self._hover_action:
            self._hover_action = new_hover
            self.refresh()

    def on_leave(self, event: events.Leave) -> None:
        """Hebt das Icon-Highlight auf, wenn die Maus den Splitter verlaesst."""
        if self._hover_action is not None:
            self._hover_action = None
            self.refresh()

    def on_click(self, event: events.Click) -> None:
        """Loest die Icon-Aktion aus (Collapse/Close)."""
        if self._drag_happened:
            # Ein soeben beendeter Drag ist kein Icon-Klick.
            self._drag_happened = False
            return
        action = self._action_at(event.x)
        if action == "close":
            event.stop()
            self.post_message(self.CloseRequested())
        elif action == "collapse":
            event.stop()
            self._collapsed = not self._collapsed
            self.refresh()
            self.post_message(self.CollapseRequested(self._collapsed))
