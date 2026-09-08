"""Umschaltbare Tastenbelegung fuer Textual-Apps.

Die Belegung hat zwei unabhaengige Achsen:

1. **Stil** - `classic` (Buchstaben, der gewachsene Bestand) oder `function_keys`
   (allgemeine Funktionen auf F-Tasten, damit die Buchstaben fuer die fachlichen
   Aktionen frei werden). Betrifft nur die Aktionen der Anwendung.
2. **Vim-Navigation** - ein Zusatz, kein eigener Stil. Er belegt ausschliesslich
   `DataTable` und Scroll-Bereiche und laesst die Aktionsebene unangetastet,
   laesst sich also mit beiden Stilen kombinieren.

Warum kein drittes Stil-Tabellenpaar fuer vim: Die Navigationstasten haengen am
Widget, die Aktionstasten an der App. Beides in eine Tabelle zu giessen wuerde
jede Aktion doppelt fuehren, ohne dass sich etwas daran unterscheidet.

Die `classic`-Tabelle liefert **die Anwendung**, nicht diese Bibliothek - sie ist
per Definition das, was die Anwendung heute schon bindet, und das ist ueberall
anders. Gemeinsam ist nur die neue Konvention (`COMMON_FUNCTION_KEYS`), die
Vim-Ebene und die Mechanik zum Zusammenfuehren und Pruefen.

Public API:
    - `KeymapStyle` - die beiden Stile.
    - `KeyBinding` - Tastenliste, Footer-Sichtbarkeit und Prioritaet einer Aktion.
    - `COMMON_FUNCTION_KEYS` - die anwendungsuebergreifende F-Tasten-Konvention.
    - `VIM_NAVIGATION` - die Navigationstasten fuer Tabellen und Scroll-Bereiche.
    - `resolve_keymap()` - Grundtabelle, Ergaenzungen und Anwenderkorrekturen
      zu einer geprueften Belegung zusammenfuehren.
    - `ResolvedKeymap` / `KeymapProblem` - Ergebnis und Beanstandungen.
    - `parse_overrides()` - Anwenderkorrekturen aus der Einstellungsdatei lesen.
    - `find_collisions()` - Doppelbelegungen einer fertigen Tabelle finden.
    - `default_style_for_platform()` - Startwert je Betriebssystem.

Usage:
    from textual_widgets import KeymapStyle, resolve_keymap

    CLASSIC = {"quit": KeyBinding(("q", "Q")), "settings": KeyBinding(("s", "S"))}

    resolved = resolve_keymap(
        style=KeymapStyle.FUNCTION_KEYS,
        classic=CLASSIC,
        app_bindings=MY_APP_BINDINGS,
        overrides=user_overrides,
    )
    for problem in resolved.problems:
        self.log_warning(problem.message)
    for action, binding in resolved.bindings.items():
        self._bindings.bind(
            ",".join(binding.keys),
            action,
            t(f"binding.{action}"),
            key_display=binding.keys[0],
            show=binding.show,
        )

Zwei Dinge, die beim Binden leicht Zeit kosten:

- **Eine Bindung am Widget schlaegt die gleichnamige an der App**, und die
  App-Aktion feuert dann gar nicht - ohne Fehler und ohne Hinweis im Footer.
  Deshalb darf keine Aktion der App auf einer Taste aus `VIM_NAVIGATION` liegen,
  solange die Vim-Ebene aktiv ist. `resolve_keymap()` prueft das.
- **`ctrl+h` kommt in Textual nicht an**, `alt+h` dagegen schon. Ebenso sind
  `alt+f` und `alt+b` belegt (sie sind `ctrl+right` und `ctrl+left`). Erhoben in
  https://github.com/whyisdifficult/jiratui/pull/327 - dort im selben Zug geloest.
"""

from __future__ import annotations

import sys
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from enum import StrEnum

__all__ = [
    "COMMON_FUNCTION_KEYS",
    "PROTECTED_ACTIONS",
    "VIM_NAVIGATION",
    "KeyBinding",
    "KeymapProblem",
    "KeymapStyle",
    "ResolvedKeymap",
    "default_style_for_platform",
    "find_collisions",
    "parse_overrides",
    "resolve_keymap",
]


class KeymapStyle(StrEnum):
    """Die ausgelieferten Belegungsstile."""

    CLASSIC = "classic"
    """Der gewachsene Bestand - allgemeine Funktionen auf Buchstaben."""

    FUNCTION_KEYS = "function_keys"
    """Allgemeine Funktionen auf F-Tasten, Buchstaben bleiben den fachlichen."""


@dataclass(frozen=True, slots=True)
class KeyBinding:
    """Die Tasten einer Aktion samt Darstellung im Footer.

    Args:
        keys: Alle Tasten, die die Aktion ausloesen. Die erste ist die, die im
            Footer steht. Mehrere sind ausdruecklich erwuenscht - eine F-Taste
            und eine Ausweichtaste nebeneinander federt Terminals ab, die die
            F-Reihe selbst abfangen.
        show: Ob die Aktion im Footer erscheint.
        priority: Ob die Bindung Vorrang vor der des fokussierten Widgets hat.
    """

    keys: tuple[str, ...]
    show: bool = True
    priority: bool = False

    def __post_init__(self) -> None:
        if not self.keys:
            raise ValueError("Eine Bindung braucht mindestens eine Taste.")


@dataclass(frozen=True, slots=True)
class KeymapProblem:
    """Eine Beanstandung beim Zusammenfuehren der Belegung.

    Args:
        action: Die betroffene Aktion.
        message: Der Text fuer das Log. Deutsch, an den Anwender gerichtet.
        key: Die ausloesende Taste, falls es um eine bestimmte geht.
    """

    action: str
    message: str
    key: str | None = None


@dataclass(frozen=True, slots=True)
class ResolvedKeymap:
    """Die fertige Belegung und alles, was dabei auffiel.

    Args:
        bindings: Aktion auf Bindung, in der Reihenfolge der Grundtabelle.
        problems: Was verworfen oder zurechtgebogen wurde. Leer heisst sauber.
    """

    bindings: Mapping[str, KeyBinding]
    problems: tuple[KeymapProblem, ...]


COMMON_FUNCTION_KEYS: Mapping[str, KeyBinding] = {
    "about": KeyBinding(("f1", "i", "I")),
    "settings": KeyBinding(("f2",)),
    "search": KeyBinding(("f3", "slash"), show=False),
    "log": KeyBinding(("f4", "alt+l")),
    "refresh": KeyBinding(("f5",)),
    "quit": KeyBinding(("f10", "q", "Q")),
}
"""Die anwendungsuebergreifende Konvention aus `SHORTCUTS.md`.

`settings` bekommt bewusst **keinen** Buchstaben als Zweitbelegung: Der ganze
Zweck der Umstellung ist, dass `s` fuer "Start" frei wird. `log` zieht von `l`
weg, weil `l` in der Vim-Ebene "nach rechts" ist und eine Widget-Bindung die
der App verdeckt.

Nicht enthalten sind die fachlichen Tasten (`s` Start, `x` Abbrechen, `c`
Kopieren, `e` Exportieren, `d` Details) - die haengen daran, was die jeweilige
Anwendung ueberhaupt kann, und stehen deshalb in ihrer eigenen Tabelle.
"""

VIM_NAVIGATION: Mapping[str, KeyBinding] = {
    "cursor_up": KeyBinding(("up", "k"), show=False),
    "cursor_down": KeyBinding(("down", "j"), show=False),
    "cursor_left": KeyBinding(("left", "h"), show=False),
    "cursor_right": KeyBinding(("right", "l"), show=False),
    "scroll_top": KeyBinding(("g",), show=False),
    "scroll_bottom": KeyBinding(("G",), show=False),
    "page_up": KeyBinding(("pageup", "ctrl+u"), show=False),
    "page_down": KeyBinding(("pagedown", "ctrl+d"), show=False),
}
"""Die Vim-Ebene fuer `DataTable` und Scroll-Bereiche.

Wird am **Widget** gebunden, nicht an der App. Textual bringt davon nichts mit:
`DataTable.BINDINGS` kennt in 8.2.8 nur `enter`, die Pfeiltasten, `pageup`,
`pagedown`, `home`, `end`, `ctrl+home` und `ctrl+end`.
"""

PROTECTED_ACTIONS: frozenset[str] = frozenset({"quit"})
"""Aktionen, die niemals ohne Taste dastehen duerfen.

Eine Anwenderkorrektur, die `quit` die letzte Taste nimmt, wird verworfen statt
uebernommen - sonst haengt die Anwendung ohne sichtbaren Ausweg.
"""


def default_style_for_platform(platform_name: str = sys.platform) -> KeymapStyle:
    """Ermittelt den Stil, mit dem eine frische Installation starten sollte.

    Auf macOS senden die F-Tasten ab Werk Systemfunktionen, und F3, F4 und F11
    holt sich das Betriebssystem ganz (Mission Control, Spotlight, Schreibtisch).
    Dort ist der Bestandsstil die freundlichere Vorgabe. Umschalten kann der
    Anwender ueberall.

    Args:
        platform_name: Der zu pruefende Plattformname, per Vorgabe `sys.platform`.

    Returns:
        Der vorzuschlagende Stil.
    """

    return KeymapStyle.CLASSIC if platform_name == "darwin" else KeymapStyle.FUNCTION_KEYS


def find_collisions(bindings: Mapping[str, KeyBinding]) -> tuple[KeymapProblem, ...]:
    """Sucht Tasten, die auf mehr als einer Aktion liegen.

    Args:
        bindings: Die zu pruefende Belegung.

    Returns:
        Je doppelt belegter Taste eine Beanstandung, sonst ein leeres Tupel.
    """

    owners: dict[str, list[str]] = {}
    for action, binding in bindings.items():
        for key in binding.keys:
            owners.setdefault(key, []).append(action)

    problems: list[KeymapProblem] = []
    for key, actions in owners.items():
        if len(actions) > 1:
            beteiligte = ", ".join(actions)
            problems.append(
                KeymapProblem(
                    action=actions[0],
                    key=key,
                    message=f"Die Taste {key} liegt auf mehreren Aktionen: {beteiligte}.",
                )
            )
    return tuple(problems)


def parse_overrides(raw: object) -> tuple[dict[str, KeyBinding], tuple[KeymapProblem, ...]]:
    """Liest die Anwenderkorrekturen aus der Einstellungsdatei.

    Erwartet wird eine Zuordnung Aktion auf Tastenliste, also
    `{"settings": ["f2", "alt+s"], "log": ["alt+l"]}`. Ein einzelner String
    wird als eine Taste genommen. Alles andere wird beanstandet und uebergangen,
    damit ein Tippfehler nicht die ganze Datei unbrauchbar macht.

    Args:
        raw: Der rohe Wert aus der Einstellungsdatei.

    Returns:
        Die gelesenen Korrekturen und die Beanstandungen dazu.
    """

    problems: list[KeymapProblem] = []
    parsed: dict[str, KeyBinding] = {}

    if raw is None:
        return parsed, ()
    if not isinstance(raw, Mapping):
        return parsed, (
            KeymapProblem(
                action="",
                message="Die eigenen Tastenbelegungen muessen eine Zuordnung Aktion auf Tasten sein.",
            ),
        )

    for action, value in raw.items():
        if not isinstance(action, str) or not action:
            problems.append(KeymapProblem(action=str(action), message=f"Ungueltiger Aktionsname: {action!r}."))
            continue
        if isinstance(value, str):
            keys: list[str] = [value]
        elif isinstance(value, Iterable):
            keys = [entry for entry in value if isinstance(entry, str) and entry]
        else:
            problems.append(
                KeymapProblem(action=action, message=f"Die Tasten fuer {action} muessen eine Liste von Texten sein.")
            )
            continue

        keys = [key.strip() for key in keys if key.strip()]
        if not keys:
            problems.append(KeymapProblem(action=action, message=f"Fuer {action} ist keine Taste angegeben."))
            continue
        parsed[action] = KeyBinding(tuple(keys))

    return parsed, tuple(problems)


def resolve_keymap(
    style: KeymapStyle,
    classic: Mapping[str, KeyBinding],
    *,
    function_keys: Mapping[str, KeyBinding] | None = None,
    overrides: Mapping[str, KeyBinding] | None = None,
    vim_navigation: bool = False,
) -> ResolvedKeymap:
    """Fuehrt Stil, Ergaenzungen und Anwenderkorrekturen zu einer Belegung zusammen.

    Die Reihenfolge ist: `classic` als Grundlage, im Stil `function_keys` darueber
    die abweichenden Eintraege, ganz oben die Korrekturen des Anwenders. Eine
    Korrektur gewinnt immer - nimmt sie einer anderen Aktion deren Taste weg,
    verliert die andere Aktion genau diese Taste, und wenn ihr danach keine mehr
    bleibt, steht das als Beanstandung im Ergebnis.

    Ausnahme sind `PROTECTED_ACTIONS`: Eine Korrektur, die dort die letzte Taste
    nehmen wuerde, wird verworfen statt uebernommen.

    Args:
        style: Der gewaehlte Stil.
        classic: Die Belegung der Anwendung im Bestandsstil. Bestimmt zugleich,
            welche Aktionen es ueberhaupt gibt und in welcher Reihenfolge sie im
            Footer stehen.
        function_keys: Die im F-Tasten-Stil abweichenden Eintraege. Ueblicherweise
            `COMMON_FUNCTION_KEYS` plus das, was die Anwendung ergaenzt. Wird im
            Stil `classic` nicht angesehen.
        overrides: Die Korrekturen des Anwenders, aus `parse_overrides()`.
        vim_navigation: Ob die Vim-Ebene aktiv ist. Dann wird zusaetzlich geprueft,
            ob eine Aktion auf einer Navigationstaste liegt und dort verdeckt wuerde.

    Returns:
        Die fertige Belegung und alle Beanstandungen.
    """

    problems: list[KeymapProblem] = []
    bindings: dict[str, KeyBinding] = dict(classic)

    if style is KeymapStyle.FUNCTION_KEYS and function_keys:
        for action, binding in function_keys.items():
            # Nur Aktionen ueberschreiben, die die Anwendung auch kennt - eine
            # gemeinsame Konvention darf ihr keine Aktion andichten, die es
            # in ihr gar nicht gibt.
            if action in bindings:
                bindings[action] = replace(binding, show=bindings[action].show, priority=bindings[action].priority)

    for problem in find_collisions(bindings):
        problems.append(
            replace(problem, message=f"{problem.message} Das ist ein Fehler in der ausgelieferten Belegung.")
        )

    if overrides:
        bindings, override_problems = _apply_overrides(bindings, overrides)
        problems.extend(override_problems)

    if vim_navigation:
        problems.extend(_check_vim_shadowing(bindings))

    return ResolvedKeymap(bindings=bindings, problems=tuple(problems))


def _apply_overrides(
    bindings: Mapping[str, KeyBinding],
    overrides: Mapping[str, KeyBinding],
) -> tuple[dict[str, KeyBinding], list[KeymapProblem]]:
    """Legt die Anwenderkorrekturen ueber die ausgelieferte Belegung.

    Args:
        bindings: Die ausgelieferte Belegung.
        overrides: Die Korrekturen des Anwenders.

    Returns:
        Die korrigierte Belegung und die Beanstandungen.
    """

    problems: list[KeymapProblem] = []
    result: dict[str, KeyBinding] = dict(bindings)

    for action, override in overrides.items():
        if action not in result:
            problems.append(
                KeymapProblem(action=action, message=f"Die Anwendung kennt keine Aktion namens {action} - uebergangen.")
            )
            continue

        # Die Tasten, die diese Korrektur anderen Aktionen wegnimmt.
        verdraengt = {
            other: [key for key in binding.keys if key in override.keys]
            for other, binding in result.items()
            if other != action
        }
        geschuetzt = [
            other
            for other, keys in verdraengt.items()
            if keys and other in PROTECTED_ACTIONS and len(result[other].keys) == len(keys)
        ]
        if geschuetzt:
            betroffen = ", ".join(geschuetzt)
            problems.append(
                KeymapProblem(
                    action=action,
                    message=(
                        f"Die eigene Belegung fuer {action} wuerde {betroffen} die letzte Taste nehmen - verworfen."
                    ),
                )
            )
            continue

        result[action] = replace(override, show=result[action].show, priority=result[action].priority)
        for other, keys in verdraengt.items():
            if not keys:
                continue
            rest = tuple(key for key in result[other].keys if key not in override.keys)
            if rest:
                result[other] = replace(result[other], keys=rest)
                continue
            del result[other]
            problems.append(
                KeymapProblem(
                    action=other,
                    message=(
                        f"{other} hat keine Taste mehr, weil die eigene Belegung fuer {action} sie belegt - "
                        f"die Aktion ist nur noch ueber die Oberflaeche erreichbar."
                    ),
                )
            )

    return result, problems


def _check_vim_shadowing(bindings: Mapping[str, KeyBinding]) -> list[KeymapProblem]:
    """Findet Aktionen, die von der Vim-Ebene verdeckt werden.

    Eine Bindung am Widget schlaegt die gleichnamige an der App. Liegt eine
    Aktion auf `j`, `k`, `h`, `l`, `g` oder `G`, ist sie stumm, sobald eine
    Tabelle den Fokus hat - ohne Fehler und ohne Hinweis.

    Args:
        bindings: Die fertige Belegung der Anwendung.

    Returns:
        Je verdeckter Taste eine Beanstandung.
    """

    vim_keys = {key for binding in VIM_NAVIGATION.values() for key in binding.keys}
    # Pfeiltasten und Bild-auf/ab sind in beiden Ebenen dasselbe und stoeren nicht.
    vim_keys -= {"up", "down", "left", "right", "pageup", "pagedown"}

    problems: list[KeymapProblem] = []
    for action, binding in bindings.items():
        for key in binding.keys:
            if key in vim_keys:
                problems.append(
                    KeymapProblem(
                        action=action,
                        key=key,
                        message=(
                            f"{action} liegt auf {key} und ist bei aktiver Vim-Navigation stumm, "
                            f"solange eine Tabelle den Fokus hat."
                        ),
                    )
                )
    return problems
