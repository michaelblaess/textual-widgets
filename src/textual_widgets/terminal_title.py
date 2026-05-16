"""Setzt den Terminal-Fenster-/Tab-Titel via OSC-Escape-Sequenz.

Textual setzt den OS-Terminal-Titel nicht selbst — `App.TITLE` fuettert nur
das interne Header-Widget. Diese Helfer schreiben die OSC-Sequenz direkt auf
die Konsole, damit Windows Terminal, mintty, xterm, GNOME Terminal, Konsole,
iTerm2, Terminal.app, Alacritty, kitty und WezTerm den Tab-Text anzeigen.

Geschrieben wird ueber `sys.__stdout__`: das ist Pythons Unicode-Konsolen-
Writer (auf Windows `WriteConsoleW`), der die aktive Code-Page umgeht — sonst
wuerden UTF-8-Bytes auf einer cp1252-Konsole als Mojibake ankommen. `sys.stdout`
selbst kapert Textual waehrend der Laufzeit, `sys.__stdout__` bleibt aber
unangetastet und zeigt weiter auf die echte Konsole.

Tipp fuer ein "Icon" im Tab: ein monochromes Text-Symbol an den Titelanfang
stellen (z.B. ``♬`` Doppelnote). Es uebernimmt die Tab-Textfarbe. Color-
Emoji (``\U0001f3b5``) lassen sich nicht umfaerben, weil OSC-Titel kein Styling
erlauben. Das echte Tab-Icon kann eine Konsolen-App nicht aendern — es kommt
ausschliesslich aus dem Terminal-Profil.

Usage:

    from textual_widgets import reset_terminal_title, set_terminal_title

    def main() -> None:
        set_terminal_title("♬ my-app v1.0.0")
        try:
            MyApp().run()
        finally:
            reset_terminal_title()
"""

from __future__ import annotations

import sys

# OSC 0 = setzt Icon-Name UND Fenstertitel, BEL (\x07) als Terminator
_OSC_TITLE = "\x1b]0;{title}\x07"


def set_terminal_title(title: str) -> None:
    """Setzt den Terminal-Titel (Icon-Name und Fenstertitel).

    :param title:
        Anzuzeigender Text im Tab/Fenster.
    """
    _write_osc(title)


def reset_terminal_title() -> None:
    """Loescht den von der App gesetzten Titel.

    Die Shell (z.B. der PowerShell-Prompt) setzt den Titel beim naechsten
    Prompt ohnehin neu — dieser Aufruf raeumt nur sauber auf.
    """
    _write_osc("")


def _write_osc(title: str) -> None:
    """Schreibt die OSC-Titel-Sequenz auf die Konsole.

    :param title:
        Titeltext (leer = Titel loeschen).
    """
    stream = sys.__stdout__
    if stream is None:
        return
    try:
        if not stream.isatty():
            return
        stream.write(_OSC_TITLE.format(title=title))
        stream.flush()
    except (OSError, ValueError):
        # Geschlossener oder umgeleiteter Stream — der Titel ist optional.
        pass
