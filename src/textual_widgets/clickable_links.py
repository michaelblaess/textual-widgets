"""Clickable-Links-Mixin fuer Textual-Apps.

Standardisiert klickbare Links in jeder Textual-App: rohe URLs in Rich-Text
werden zu Textual-Action-Markup-Schnipseln umgeschrieben, das Textual ohne
CTRL-Klick aufnimmt und beim Maus-Hover automatisch hervorhebt.

Verwendung:

    class MyApp(ClickableLinksMixin, App):
        ...

    # Irgendwo im Code
    self._log.write(self.linkify_urls("Sitemap geschrieben: https://example.com"))
    self._panel.update(self.link_markup("Dokumentation", "https://docs.example.com"))

Beide Methoden produzieren ein Markup-Snippet vom Format
``[@click=app.open_link({id})]label[/]``. Beim Klick (oder Enter waehrend
Hover) ruft Textual ``action_open_link(id)`` auf, das die Mixin bereitstellt:
http(s)-URLs gehen ueber ``webbrowser.open``, lokale Pfade ueber das jeweilige
Standard-OS-Kommando.

Sonderzeichen in URLs/Pfaden sind unkritisch, weil die Targets in einer
internen Registry liegen und das Markup nur die ID enthaelt.
"""

from __future__ import annotations

import contextlib
import os
import platform
import re
import subprocess
import webbrowser
from typing import Any

# http(s)-URL — vermeidet die Re-Linkifizierung von URLs, die bereits in einem
# ``[link …]``- oder ``[@click=…]``-Markup-Block stecken.
_URL_RE = re.compile(r"(?<!=)(?<!\])(?<!\")(https?://[^\s\[\]<>\"']+)")


class ClickableLinksMixin:
    """Mixin: registriert Klick-Ziele und oeffnet sie auf Klick.

    Verbraucht eine kleine integer-Counter-State, registriert URLs/Pfade
    on demand und stellt die Aktion bereit, die Textual beim Klick aufruft.
    """

    _link_registry: dict[int, str]
    _link_counter: int

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._link_registry = {}
        self._link_counter = 0

    def link_markup(self, text: str, target: str) -> str:
        """Erzeugt Textual-Action-Markup fuer einen klickbaren Link.

        Args:
            text:
                Sichtbarer Linktext.
            target:
                URL (``http://`` / ``https://``) oder lokaler Dateipfad.

        Returns:
            Markup-Snippet, das in beliebigen Rich-Text-Kontexten verwendet
            werden kann. Bei leerem ``target`` wird ``text`` unveraendert
            zurueckgegeben.
        """
        if not target:
            return text
        self._link_counter += 1
        link_id = self._link_counter
        self._link_registry[link_id] = target
        return f"[@click=app.open_link({link_id})]{text}[/]"

    def linkify_urls(self, message: str) -> str:
        """Rewrites jede rohe ``http(s)``-URL in ``message`` zu klickbarem Markup.

        URLs, die bereits in einem ``[link …]``- oder ``[@click=…]``-Markup
        stecken, werden in Ruhe gelassen.

        Args:
            message:
                Beliebige Rich-Text-Nachricht.

        Returns:
            Die Nachricht mit allen rohen URLs als klickbarem Markup.
        """
        return _URL_RE.sub(lambda m: self.link_markup(m.group(1), m.group(1)), message)

    def action_open_link(self, link_id: str) -> None:
        """Oeffnet das zur ID registrierte URL/Datei-Ziel im OS-Standard-Programm.

        Args:
            link_id:
                Die in ``link_markup`` vergebene ID — Textual reicht sie als
                String aus dem Markup durch.
        """
        try:
            key = int(link_id)
        except (TypeError, ValueError):
            return
        target = self._link_registry.get(key, "")
        if not target:
            return
        if target.startswith(("http://", "https://")):
            with contextlib.suppress(Exception):
                webbrowser.open(target)
            return
        with contextlib.suppress(Exception):
            if platform.system() == "Windows":
                os.startfile(target)  # type: ignore[attr-defined]
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", target])
            else:
                subprocess.Popen(["xdg-open", target])
