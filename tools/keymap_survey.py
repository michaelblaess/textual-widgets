"""Erhebt die Tastenbelegung aller TUI-Anwendungen und stellt sie gegenueber.

Liest die Aufrufe von `_bindings.bind(...)` und `Binding(...)` aus dem Quelltext
und baut daraus eine Kreuztabelle Taste -> Anwendung -> Aktion.
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

REPOS = Path(r"C:\Users\Michael\Repos")

APPS = [
    "buildrunner-tui",
    "c2pa-scanner",
    "console-error-scanner",
    "form-breaker",
    "inspectcode-tui",
    "sitemap-tracker",
    "visual-regression-scanner",
    "jira-timesheet",
]

# bind("q,Q", "quit", ...) und Binding("q,Q", "quit", ...)
MUSTER = re.compile(r'(?:_bindings\.bind|Binding)\(\s*"([^"]+)"\s*,\s*"([^"]+)"')

# Aktionen, die nur einen Dialog schliessen - die sagen nichts ueber die
# Hauptbelegung aus und wuerden die Tabelle zumuellen.
DIALOG_AKTIONEN = {"close", "cancel", "select", "confirm", "save", "unfocus_filter", "clear_filter"}


def sammle(app: str) -> dict[str, set[str]]:
    """Liest die Bindungen einer Anwendung.

    Args:
        app: Der Repo-Name der Anwendung.

    Returns:
        Taste auf die Menge der Aktionen, die sie in dieser Anwendung ausloest.
    """

    wurzel = REPOS / app / "src"
    treffer: dict[str, set[str]] = defaultdict(set)
    if not wurzel.is_dir():
        return treffer

    for datei in wurzel.rglob("*.py"):
        for tasten, aktion in MUSTER.findall(datei.read_text(encoding="utf-8", errors="replace")):
            if aktion in DIALOG_AKTIONEN:
                continue
            for taste in tasten.split(","):
                taste = taste.strip()
                # Grossbuchstaben sind nur die Zweitschreibung derselben Taste.
                if len(taste) == 1 and taste.isupper():
                    taste = taste.lower()
                if taste:
                    treffer[taste].add(aktion)
    return treffer


def main() -> None:
    je_app = {app: sammle(app) for app in APPS}

    kreuz: dict[str, dict[str, str]] = defaultdict(dict)
    for app, bindungen in je_app.items():
        for taste, aktionen in bindungen.items():
            kreuz[taste][app] = " / ".join(sorted(aktionen))

    def sortierschluessel(taste: str) -> tuple[int, str]:
        return (0, taste) if len(taste) == 1 else (1, taste)

    print(f"{'Taste':<14} {'Apps':<5} Bedeutungen")
    print("-" * 100)
    for taste in sorted(kreuz, key=sortierschluessel):
        zeilen = kreuz[taste]
        bedeutungen: dict[str, list[str]] = defaultdict(list)
        for app, aktion in zeilen.items():
            bedeutungen[aktion].append(app)
        teile = [f"{aktion} ({len(apps)})" for aktion, apps in sorted(bedeutungen.items(), key=lambda p: -len(p[1]))]
        marke = "  <-- EINHEITLICH" if len(bedeutungen) == 1 and len(zeilen) >= 4 else ""
        print(f"{taste:<14} {len(zeilen):<5} {', '.join(teile)}{marke}")


if __name__ == "__main__":
    main()
