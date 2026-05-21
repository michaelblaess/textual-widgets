"""Basis-Settings-Dialog fuer Textual-Apps.

Public API:
    - `BaseSettingsScreen` — ModalScreen-Basisklasse fuer App-Settings.
      Liefert einheitlichen Look, einen Sprach-Tab (de/en), Save/Cancel-Buttons
      und Esc/Ctrl+S-Bindings. Apps erben und ueberschreiben zwei Hooks.

Usage:
    from textual.widgets import Checkbox, TabPane
    from textual_widgets import BaseSettingsScreen

    class MySettingsScreen(BaseSettingsScreen):
        def app_tabs(self) -> ComposeResult:           # Hook 1: eigene Tabs
            with TabPane("Crawl", id="tab-crawl"):
                yield Checkbox("robots.txt", value=..., id="set-robots")

        def collect_app_settings(self, settings: dict[str, object]) -> None:
            # Hook 2: Widget-Werte ins Ergebnis-Dict schreiben
            settings["respect_robots"] = self.query_one("#set-robots", Checkbox).value

    # In der App:
    def action_show_settings(self) -> None:
        self.push_screen(
            MySettingsScreen(self._settings_store.load(), lang=current_language()),
            callback=self._on_settings_closed,
        )

Der Dialog gibt das geaenderte Settings-Dict zurueck (oder `None` bei Abbruch).
Beim Speichern postet er ein `LogMessage` — laeuft via `LogRouter` ins LogPanel.
"""

from __future__ import annotations

import contextlib
import os
import platform
import subprocess
from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.events import Click
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Select, Static, TabbedContent, TabPane

from textual_widgets.log_panel import LogMessage


def _reveal_path(path: Path) -> None:
    """Oeffnet den Eltern-Ordner einer Datei (bzw. das Verzeichnis selbst).

    Versucht die Datei im Datei-Manager zu markieren - auf Windows via
    ``explorer /select``, auf macOS via ``open -R``. Linux unterstuetzt das
    nicht generisch und faellt auf ``xdg-open <dir>`` zurueck.
    """
    with contextlib.suppress(Exception):
        if not path.exists():
            # Pfad existiert noch nicht - Eltern-Ordner oeffnen, sofern es
            # ihn gibt. Sonst gibt es nichts sinnvoll zu zeigen.
            parent = path.parent
            if parent.exists():
                _open_directory(parent)
            return
        if path.is_dir():
            _open_directory(path)
            return
        system = platform.system()
        if system == "Windows":
            # Quotes um den Pfad, weil explorer sonst an Leerzeichen scheitert.
            subprocess.Popen(f'explorer /select,"{path}"')
        elif system == "Darwin":
            subprocess.Popen(["open", "-R", str(path)])
        else:
            _open_directory(path.parent)


def _open_directory(path: Path) -> None:
    """Oeffnet ein Verzeichnis im Standard-Datei-Manager."""
    with contextlib.suppress(Exception):
        system = platform.system()
        if system == "Windows":
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif system == "Darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])


# Dialog-Texte pro Sprache. Andere Sprachen fallen auf Englisch zurueck.
_TEXT: dict[str, dict[str, str]] = {
    "de": {
        "title": "Einstellungen",
        "save": "Speichern (Ctrl+S)",
        "cancel": "Abbrechen (Esc)",
        "tab_language": "Sprache",
        "language_label": "Sprache:",
        "language_hint": "Die Sprachänderung wird erst nach einem Neustart der Anwendung aktiv.",
        "saved": "Einstellungen gespeichert",
        "tab_storage": "Speicherort",
        "storage_hint": (
            "Klick auf einen Pfad öffnet den Ordner im Datei-Manager. "
            "Die Anwendung überschreibt diese Dateien beim Speichern — "
            "schließe sie, bevor du sie manuell editierst."
        ),
    },
    "en": {
        "title": "Settings",
        "save": "Save (Ctrl+S)",
        "cancel": "Cancel (Esc)",
        "tab_language": "Language",
        "language_label": "Language:",
        "language_hint": "The language change takes effect only after restarting the application.",
        "saved": "Settings saved",
        "tab_storage": "Storage",
        "storage_hint": (
            "Clicking a path opens the folder in your file manager. "
            "The application overwrites these files when saving — "
            "close it before editing them manually."
        ),
    },
}


class BaseSettingsScreen(ModalScreen[dict[str, object] | None]):
    """Basisklasse fuer App-Settings-Dialoge.

    Liefert einheitlichen Look (Titel, Tabs, Save/Cancel-Leiste), einen
    Sprach-Tab und die Standard-Bindings. Apps erben davon und ueberschreiben
    `app_tabs()` (eigene TabPanes) sowie `collect_app_settings()` (Werte
    einsammeln).

    Gibt das geaenderte Settings-Dict zurueck oder `None` bei Abbruch.

    Attributes:
        SETTINGS_TITLE:
            Optionaler fester Titel. Leer = sprachabhaengiger Default
            ("Einstellungen" / "Settings").
    """

    SETTINGS_TITLE: str = ""

    DEFAULT_CSS = """
    BaseSettingsScreen {
        align: center middle;
    }

    BaseSettingsScreen > Vertical {
        width: 90%;
        max-width: 100;
        height: 80%;
        max-height: 32;
        background: $surface;
        border: thick $accent;
        padding: 1 2;
    }

    BaseSettingsScreen #settings-title {
        width: 1fr;
        height: 3;
        content-align: center middle;
        text-style: bold;
        background: $accent;
        color: auto;
        margin-bottom: 1;
    }

    BaseSettingsScreen TabbedContent {
        height: 1fr;
    }

    BaseSettingsScreen TabPane {
        padding: 0 1;
    }

    BaseSettingsScreen .settings-row {
        height: auto;
        margin-bottom: 1;
    }

    BaseSettingsScreen .settings-row Label {
        width: 24;
        padding: 1 1;
    }

    BaseSettingsScreen .settings-hint {
        color: $text-muted;
        padding: 1 2;
        margin-top: 1;
        border: round $surface-lighten-2;
    }

    BaseSettingsScreen #settings-buttons {
        height: 3;
        align: center middle;
        margin-top: 1;
        dock: bottom;
    }

    BaseSettingsScreen #settings-buttons Button {
        margin: 0 1;
    }

    BaseSettingsScreen .storage-row {
        height: 1;
        layout: horizontal;
    }

    BaseSettingsScreen .storage-label {
        width: 22;
        color: $text-muted;
        padding: 0 1 0 0;
    }

    BaseSettingsScreen .storage-path {
        width: 1fr;
        height: 1;
        color: $accent;
        text-style: underline;
    }

    BaseSettingsScreen .storage-path:hover {
        background: $accent 20%;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Esc"),
        Binding("ctrl+s", "save", "Ctrl+S"),
    ]

    def __init__(self, settings: dict[str, object], lang: str = "en") -> None:
        """Erstellt den Settings-Dialog.

        Args:
            settings:
                Das aktuelle Settings-Dict. Wird kopiert; das Original bleibt
                unangetastet (Abbruch verwirft alle Aenderungen).
            lang:
                Sprachkuerzel ('de' oder 'en') fuer die Dialogtexte.
        """
        super().__init__()
        self._settings = dict(settings)
        self._lang = lang if lang in _TEXT else "en"
        # Widget-ID -> Pfad fuer Klick-Aufloesung im Storage-Tab.
        self._storage_click_map: dict[str, Path] = {}

    def compose(self) -> ComposeResult:
        """Erstellt das Dialog-Layout: Titel, Tabs (Sprache + App + Storage), Buttons."""
        with Vertical():
            title = self.SETTINGS_TITLE or self._t("title")
            yield Static(title, id="settings-title")
            with TabbedContent():
                yield from self._language_tab()
                yield from self.app_tabs()
                yield from self._storage_tab()
            with Horizontal(id="settings-buttons"):
                yield Button(self._t("save"), variant="primary", id="settings-save")
                yield Button(self._t("cancel"), id="settings-cancel")

    def _language_tab(self) -> ComposeResult:
        """Baut den Sprach-Tab — kommt in jeder App."""
        current = str(self._settings.get("language", self._lang))
        if current not in ("de", "en"):
            current = "de"
        with TabPane(self._t("tab_language"), id="settings-tab-language"):
            with Horizontal(classes="settings-row"):
                yield Label(self._t("language_label"))
                yield Select[str](
                    [("Deutsch", "de"), ("English", "en")],
                    value=current,
                    allow_blank=False,
                    id="settings-language",
                )
            yield Static(self._t("language_hint"), classes="settings-hint")

    def app_tabs(self) -> ComposeResult:
        """Hook: app-spezifische `TabPane`s. Standard: keine.

        Ueberschreiben, um eigene Tabs zu ergaenzen.
        """
        return ()

    def storage_paths(self) -> list[tuple[str, Path]]:
        """Hook: (Label, Pfad)-Tupel fuer den Speicherort-Tab.

        Standard: leere Liste — kein Tab. Apps mit Persistenz ueberschreiben,
        um auf JSON/SQLite/Cache-Pfade zu verweisen::

            def storage_paths(self):
                return [
                    ("Einstellungen", Path.home() / ".my-tool" / "settings.json"),
                    ("Cache", Path.home() / ".my-tool" / "cache"),
                ]

        Pfade duerfen Verzeichnisse oder Dateien sein und muessen nicht
        existieren — fehlende Pfade werden trotzdem als Hinweis angezeigt.
        """
        return []

    def _storage_tab(self) -> ComposeResult:
        """Baut den Speicherort-Tab (nur, wenn `storage_paths()` Eintraege liefert)."""
        paths = self.storage_paths()
        if not paths:
            return
        self._storage_click_map = {}
        with TabPane(self._t("tab_storage"), id="settings-tab-storage"), VerticalScroll():
            for index, (label, path) in enumerate(paths):
                widget_id = f"settings-storage-{index}"
                self._storage_click_map[widget_id] = path
                with Horizontal(classes="storage-row"):
                    yield Label(f"{label}:", classes="storage-label")
                    yield Static(str(path), classes="storage-path", id=widget_id)
            yield Static(self._t("storage_hint"), classes="settings-hint")

    def collect_app_settings(self, settings: dict[str, object]) -> None:
        """Hook: app-spezifische Widget-Werte ins Ergebnis-Dict schreiben.

        Standard: nichts. Ueberschreiben, um die eigenen Felder einzusammeln.

        Args:
            settings:
                Das Ergebnis-Dict, in das die App ihre Werte schreibt.
        """

    def action_save(self) -> None:
        """Sammelt alle Werte ein, postet ein LogMessage und schliesst."""
        result = dict(self._settings)

        lang_value = self.query_one("#settings-language", Select).value
        if isinstance(lang_value, str):
            result["language"] = lang_value

        self.collect_app_settings(result)
        # Direkt an die App posten (nicht self.post_message): der Screen wird
        # gleich per dismiss() entfernt — ein ueber den Screen bubbelndes
        # Message koennte sonst mit dem Screen-Teardown kollidieren.
        self.app.post_message(LogMessage.info(self._t("saved")))
        self.dismiss(result)

    def action_cancel(self) -> None:
        """Schliesst den Dialog ohne Aenderungen."""
        self.dismiss(None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Verarbeitet Klicks auf Save / Cancel."""
        if event.button.id == "settings-save":
            self.action_save()
        else:
            self.action_cancel()

    def on_click(self, event: Click) -> None:
        """Klick auf einen Pfad im Speicherort-Tab oeffnet den Ordner."""
        widget = event.widget
        if widget is None or not widget.id:
            return
        path = self._storage_click_map.get(widget.id)
        if path is None:
            return
        event.stop()
        _reveal_path(path)

    def _t(self, key: str) -> str:
        """Uebersetzt einen Text-Schluessel."""
        return _TEXT[self._lang].get(key, key)
