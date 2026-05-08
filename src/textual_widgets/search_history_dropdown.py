"""Such-Verlauf-Dropdown fuer Textual TUI-Apps.

Zwei Komponenten mit unterschiedlichem Abstraktionsgrad:

- ``SearchHistoryDropdown`` — OptionList die History-Eintraege rendert,
  Substring-filtert und Treffer hervorhebt. Der Host fuettert die Liste
  und reagiert auf ``EntrySelected`` / ``EntryDeleteRequested``.

- ``SearchInputWithHistory`` — fertig verdrahteter Container aus ``Input``
  und ``SearchHistoryDropdown``. Drop-in fuer ein einzelnes ``Input`` —
  ``Input.Submitted`` wird wie gewohnt emittiert.
"""

from __future__ import annotations

from rich.text import Text
from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widgets import Input, OptionList, Static
from textual.widgets.option_list import Option


# ------------------------------------------------------------------
# SearchHistoryDropdown — OptionList mit Substring-Filter
# ------------------------------------------------------------------


class SearchHistoryDropdown(OptionList):
    """OptionList die einen Such-Verlauf rendert und filtert.

    Substring-Filter (case-insensitive) ueber ``filter(query)``. Treffer
    werden im Eintrag farblich hervorgehoben. Versteckt sich automatisch
    wenn nach dem Filter keine Eintraege uebrig sind.

    Tasten:
    - ``Enter`` / Klick: Eintrag uebernehmen → ``EntrySelected``
    - ``Delete``: Eintrag aus Verlauf loeschen → ``EntryDeleteRequested``
    - ``Escape``: Dropdown schliessen
    """

    DEFAULT_CSS = """
    SearchHistoryDropdown {
        height: auto;
        max-height: 12;
        background: $surface;
        border: round $accent;
        display: none;
        padding: 0;
    }
    SearchHistoryDropdown.-visible {
        display: block;
    }
    """

    BINDINGS = [
        Binding("delete", "delete_entry", "Loeschen", show=False),
        Binding("escape", "hide", "Schliessen", show=False),
    ]

    class EntrySelected(Message):
        """Eintrag wurde via Klick oder Enter ausgewaehlt."""

        def __init__(self, entry: str) -> None:
            super().__init__()
            self.entry = entry

    class EntryDeleteRequested(Message):
        """User moechte den markierten Eintrag aus dem Verlauf entfernen.

        Die Persistenz uebernimmt der Host — das Widget ruft danach
        ``set_entries(...)`` mit der aktualisierten Liste neu auf.
        """

        def __init__(self, entry: str) -> None:
            super().__init__()
            self.entry = entry

    def __init__(
        self,
        entries: list[str] | None = None,
        max_visible: int = 10,
        highlight_style: str = "bold",
        accent_var: str = "accent",
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)
        self._all_entries: list[str] = list(entries or [])
        self._visible_entries: list[str] = []
        self._max_visible = max_visible
        self._highlight_style = highlight_style
        self._accent_var = accent_var
        self._current_query = ""

    @property
    def visible_entries(self) -> list[str]:
        """Aktuell sichtbare Eintraege (nach Filter, max ``max_visible``)."""
        return list(self._visible_entries)

    def set_entries(self, entries: list[str]) -> None:
        """Setzt die komplette Liste der History-Eintraege neu."""
        self._all_entries = list(entries)
        self._refresh_options()

    def filter(self, query: str) -> None:
        """Filtert die Eintraege per Substring (case-insensitive)."""
        self._current_query = query or ""
        self._refresh_options()

    def show(self) -> None:
        """Zeigt das Dropdown — falls Eintraege vorhanden sind."""
        if self._visible_entries:
            self.add_class("-visible")

    def hide(self) -> None:
        """Versteckt das Dropdown."""
        self.remove_class("-visible")

    def action_hide(self) -> None:
        """Tasten-Action fuer Escape."""
        self.hide()

    def action_delete_entry(self) -> None:
        """Tasten-Action fuer Delete: aktuell markierten Eintrag loeschen."""
        idx = self.highlighted
        if idx is None:
            return
        if 0 <= idx < len(self._visible_entries):
            entry = self._visible_entries[idx]
            self.post_message(self.EntryDeleteRequested(entry))

    def _accent_color(self) -> str:
        """Liest die aktuelle Accent-Farbe aus den CSS-Variablen."""
        try:
            return str(self.app.get_css_variables().get(self._accent_var, "yellow"))
        except Exception:
            return "yellow"

    def _refresh_options(self) -> None:
        """Berechnet die sichtbaren Eintraege und befuellt die OptionList."""
        q = self._current_query.lower().strip()
        if q:
            self._visible_entries = [
                e for e in self._all_entries if q in e.lower()
            ][: self._max_visible]
        else:
            self._visible_entries = self._all_entries[: self._max_visible]

        self.clear_options()
        accent = self._accent_color()
        match_style = f"{self._highlight_style} {accent}".strip()
        for entry in self._visible_entries:
            text = Text(entry)
            if q:
                lowered = entry.lower()
                start = lowered.find(q)
                while start >= 0:
                    text.stylize(match_style, start, start + len(q))
                    start = lowered.find(q, start + len(q))
            self.add_option(Option(text, id=entry))

        if self._visible_entries:
            self.add_class("-visible")
            self.highlighted = 0
        else:
            self.remove_class("-visible")

    def on_option_list_option_selected(
        self, event: OptionList.OptionSelected,
    ) -> None:
        """Eintrag wurde via Enter oder Klick ausgewaehlt."""
        event.stop()
        option_id = event.option.id
        if option_id is None:
            entry = event.option.prompt.plain if hasattr(event.option.prompt, "plain") else str(event.option.prompt)
        else:
            entry = str(option_id)
        self.post_message(self.EntrySelected(entry))


# ------------------------------------------------------------------
# SearchInputWithHistory — Input + Dropdown verdrahtet
# ------------------------------------------------------------------


class SearchInputWithHistory(Vertical):
    """Container aus ``Input`` und ``SearchHistoryDropdown``.

    Drop-in fuer ein einfaches ``Input``: emittiert weiterhin
    ``Input.Submitted`` sodass bestehende Handler unveraendert bleiben.
    Zusaetzlich:

    - ``HistoryEntrySelected`` wenn ein Eintrag aus dem Dropdown
      uebernommen wird (Submit wird automatisch ausgeloest)
    - ``HistoryEntryDeleteRequested`` wenn der User Delete drueckt

    Der Host ist verantwortlich fuer Persistenz: nach Submit
    ``add(query)`` aufrufen, dann ``set_entries(repo.list_recent(...))``
    auf diesem Widget aufrufen.
    """

    DEFAULT_CSS = """
    SearchInputWithHistory {
        height: auto;
        layout: vertical;
    }
    /* Icon-Modus: Wrapper traegt den gemeinsamen Border statt Input,
       damit Icon und Input wie EINE Box wirken (analog Textual Command-Palette). */
    SearchInputWithHistory .search-row {
        layout: horizontal;
        height: 3;
        background: $surface;
        border: tall $primary;
    }
    SearchInputWithHistory .search-row:focus-within {
        background: $surface-darken-1;
    }
    SearchInputWithHistory .search-icon {
        width: auto;
        min-width: 4;
        height: 1;
        content-align: center middle;
        background: transparent;
        color: $text-muted;
    }
    SearchInputWithHistory .search-row Input {
        width: 1fr;
        height: 1;
        border: none;
        background: transparent;
        padding: 0 1;
    }
    """

    class HistoryEntrySelected(Message):
        """Eintrag aus Dropdown gewaehlt (Submit wird automatisch ausgeloest)."""

        def __init__(self, entry: str) -> None:
            super().__init__()
            self.entry = entry

    class HistoryEntryDeleteRequested(Message):
        """Eintrag soll aus dem Verlauf entfernt werden."""

        def __init__(self, entry: str) -> None:
            super().__init__()
            self.entry = entry

    def __init__(
        self,
        placeholder: str = "",
        entries: list[str] | None = None,
        max_visible: int = 10,
        input_id: str = "search-input",
        dropdown_id: str = "search-dropdown",
        highlight_style: str = "bold",
        icon: str = "",
        **kwargs: object,
    ) -> None:
        """Initialisiert das Such-Eingabefeld mit Verlauf.

        Args:
            placeholder: Hinweistext im leeren Input.
            entries: Initiale Verlaufseintraege.
            max_visible: Maximale Anzahl gleichzeitig sichtbarer Dropdown-Eintraege.
            input_id: ID des inneren Input-Widgets.
            dropdown_id: ID des inneren Dropdown-Widgets.
            highlight_style: Rich-Style fuer Treffer-Hervorhebung im Dropdown.
            icon: Optionales Praefix-Symbol (z.B. "🔍"), permanent links neben
                dem Input sichtbar — auch wenn Text eingegeben ist. Leerstring
                bedeutet kein Icon.
        """
        super().__init__(**kwargs)
        self._placeholder = placeholder
        self._initial_entries = list(entries or [])
        self._max_visible = max_visible
        self._input_id = input_id
        self._dropdown_id = dropdown_id
        self._highlight_style = highlight_style
        self._icon = icon
        # Verhindert, dass on_input_changed das Dropdown wieder zeigt,
        # nachdem on_search_history_dropdown_entry_selected es gerade
        # geschlossen hat.
        self._suppress_show: bool = False

    def compose(self) -> ComposeResult:
        if self._icon:
            with Horizontal(classes="search-row"):
                yield Static(self._icon, classes="search-icon")
                yield Input(placeholder=self._placeholder, id=self._input_id)
        else:
            yield Input(placeholder=self._placeholder, id=self._input_id)
        yield SearchHistoryDropdown(
            entries=self._initial_entries,
            max_visible=self._max_visible,
            highlight_style=self._highlight_style,
            id=self._dropdown_id,
        )

    # --- Public API --------------------------------------------------

    @property
    def value(self) -> str:
        """Aktueller Wert des Eingabefelds."""
        try:
            return self.query_one(f"#{self._input_id}", Input).value
        except Exception:
            return ""

    @value.setter
    def value(self, val: str) -> None:
        try:
            self.query_one(f"#{self._input_id}", Input).value = val
        except Exception:
            pass

    def set_entries(self, entries: list[str]) -> None:
        """Aktualisiert die History-Eintraege im Dropdown."""
        try:
            dd = self.query_one(f"#{self._dropdown_id}", SearchHistoryDropdown)
            dd.set_entries(entries)
        except Exception:
            pass

    def focus_input(self) -> None:
        """Fokussiert das Eingabefeld."""
        try:
            self.query_one(f"#{self._input_id}", Input).focus()
        except Exception:
            pass

    def hide_dropdown(self) -> None:
        """Versteckt das Dropdown explizit."""
        try:
            self.query_one(f"#{self._dropdown_id}", SearchHistoryDropdown).hide()
        except Exception:
            pass

    # --- Event-Handler -----------------------------------------------

    def on_descendant_focus(self, event: events.DescendantFocus) -> None:
        """Input fokussiert → Dropdown anzeigen mit aktueller Filterung."""
        try:
            inp = self.query_one(f"#{self._input_id}", Input)
        except Exception:
            return
        if event.widget is inp:
            try:
                dd = self.query_one(f"#{self._dropdown_id}", SearchHistoryDropdown)
                dd.filter(inp.value)
                dd.show()
            except Exception:
                pass

    def on_descendant_blur(self, event: events.DescendantBlur) -> None:
        """Wenn weder Input noch Dropdown den Fokus haben → Dropdown weg."""
        # Verzoegert pruefen, weil zwischen Blur und neuem Focus ein Tick liegt.
        self.set_timer(0.05, self._maybe_hide_dropdown)

    def _maybe_hide_dropdown(self) -> None:
        try:
            inp = self.query_one(f"#{self._input_id}", Input)
            dd = self.query_one(f"#{self._dropdown_id}", SearchHistoryDropdown)
        except Exception:
            return
        focused = self.app.focused
        if focused is not inp and focused is not dd:
            dd.hide()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Live-Filter waehrend des Tippens."""
        if event.input.id != self._input_id:
            return
        if self._suppress_show:
            return
        try:
            dd = self.query_one(f"#{self._dropdown_id}", SearchHistoryDropdown)
            dd.filter(event.value)
            dd.show()
        except Exception:
            pass

    def on_search_history_dropdown_entry_selected(
        self, event: SearchHistoryDropdown.EntrySelected,
    ) -> None:
        """Eintrag uebernehmen → Input befuellen, Dropdown schliessen, submitten."""
        event.stop()
        try:
            inp = self.query_one(f"#{self._input_id}", Input)
            dd = self.query_one(f"#{self._dropdown_id}", SearchHistoryDropdown)
            self._suppress_show = True
            inp.value = event.entry
            dd.hide()
            self._suppress_show = False
            inp.focus()
            # Input.Submitted nachbilden, damit bestehende Submit-Handler greifen.
            self.post_message(Input.Submitted(inp, event.entry))
        except Exception:
            pass
        self.post_message(self.HistoryEntrySelected(event.entry))

    def on_search_history_dropdown_entry_delete_requested(
        self, event: SearchHistoryDropdown.EntryDeleteRequested,
    ) -> None:
        """Loesch-Anfrage an Host weiterleiten — Persistenz dort."""
        event.stop()
        self.post_message(self.HistoryEntryDeleteRequested(event.entry))
