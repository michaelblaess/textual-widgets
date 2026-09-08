"""Tests fuer die umschaltbare Tastenbelegung."""

from __future__ import annotations

import pytest

from textual_widgets.keymap import (
    COMMON_FUNCTION_KEYS,
    VIM_NAVIGATION,
    KeyBinding,
    KeymapStyle,
    default_style_for_platform,
    find_collisions,
    parse_overrides,
    resolve_keymap,
    vim_navigation_bindings,
)

# Eine Beispielanwendung im Bestandsstil - bewusst nah an jira-timesheet.
CLASSIC: dict[str, KeyBinding] = {
    "quit": KeyBinding(("q", "Q")),
    "show_about": KeyBinding(("i", "I")),
    "show_settings": KeyBinding(("s", "S")),
    "toggle_log": KeyBinding(("l", "L")),
    "refresh": KeyBinding(("f5",)),
    "focus_filter": KeyBinding(("slash",), show=False),
    "export_excel": KeyBinding(("e", "E")),
}


# --- Die ausgelieferten Tabellen ------------------------------------------------


def test_common_function_keys_sind_kollisionsfrei() -> None:
    assert find_collisions(COMMON_FUNCTION_KEYS) == ()


def test_vim_navigation_ist_kollisionsfrei() -> None:
    assert find_collisions(VIM_NAVIGATION) == ()


def test_show_settings_behaelt_s_als_zweitbelegung() -> None:
    # Gewachsene Konvention aus vier Anwendungen - die F-Taste tritt daneben,
    # sie ersetzt den Buchstaben nicht.
    assert "s" in COMMON_FUNCTION_KEYS["show_settings"].keys


def test_toggle_log_liegt_nicht_mehr_auf_l() -> None:
    # l ist in der Vim-Ebene "nach rechts" und wuerde die App-Aktion verdecken.
    assert "l" not in COMMON_FUNCTION_KEYS["toggle_log"].keys


def test_keine_gemeinsame_aktion_liegt_auf_einer_vim_taste() -> None:
    vim_keys = {key for binding in VIM_NAVIGATION.values() for key in binding.keys}
    vim_keys -= {"up", "down", "left", "right", "pageup", "pagedown"}
    belegt = {
        action: [key for key in binding.keys if key in vim_keys] for action, binding in COMMON_FUNCTION_KEYS.items()
    }
    assert {action: keys for action, keys in belegt.items() if keys} == {}


def test_find_collisions_meldet_eine_doppelbelegung() -> None:
    # Gegenprobe: der Kollisionssucher muss ueberhaupt anschlagen koennen.
    problems = find_collisions({"a": KeyBinding(("x",)), "b": KeyBinding(("x",))})
    assert len(problems) == 1
    assert problems[0].key == "x"


# --- Stile ----------------------------------------------------------------------


def test_classic_ignoriert_die_f_tasten_tabelle() -> None:
    resolved = resolve_keymap(KeymapStyle.CLASSIC, CLASSIC, function_keys=COMMON_FUNCTION_KEYS)
    assert resolved.bindings["show_settings"].keys == ("s", "S")
    assert resolved.problems == ()


def test_function_keys_ueberschreibt_die_gemeinsamen_aktionen() -> None:
    resolved = resolve_keymap(KeymapStyle.FUNCTION_KEYS, CLASSIC, function_keys=COMMON_FUNCTION_KEYS)
    assert resolved.bindings["show_settings"].keys == ("f2", "s", "S")
    assert resolved.bindings["toggle_log"].keys == ("f4", "alt+l")
    assert resolved.bindings["quit"].keys == ("q", "Q")
    assert resolved.problems == ()


def test_function_keys_laesst_fachliche_aktionen_in_ruhe() -> None:
    resolved = resolve_keymap(KeymapStyle.FUNCTION_KEYS, CLASSIC, function_keys=COMMON_FUNCTION_KEYS)
    assert resolved.bindings["export_excel"].keys == ("e", "E")


def test_function_keys_dichtet_keine_unbekannte_aktion_an() -> None:
    ohne_log = {action: binding for action, binding in CLASSIC.items() if action != "toggle_log"}
    resolved = resolve_keymap(KeymapStyle.FUNCTION_KEYS, ohne_log, function_keys=COMMON_FUNCTION_KEYS)
    assert "toggle_log" not in resolved.bindings


def test_footer_sichtbarkeit_der_anwendung_bleibt_erhalten() -> None:
    # search steht in CLASSIC auf show=False - die Konvention darf das nicht kippen.
    resolved = resolve_keymap(KeymapStyle.FUNCTION_KEYS, CLASSIC, function_keys=COMMON_FUNCTION_KEYS)
    assert resolved.bindings["focus_filter"].show is False


# --- Anwenderkorrekturen --------------------------------------------------------


def test_korrektur_gewinnt_gegen_die_vorgabe() -> None:
    resolved = resolve_keymap(
        KeymapStyle.FUNCTION_KEYS,
        CLASSIC,
        function_keys=COMMON_FUNCTION_KEYS,
        overrides={"show_settings": KeyBinding(("alt+s",))},
    )
    assert resolved.bindings["show_settings"].keys == ("alt+s",)
    assert resolved.problems == ()


def test_korrektur_nimmt_der_anderen_aktion_nur_die_eine_taste() -> None:
    resolved = resolve_keymap(
        KeymapStyle.CLASSIC,
        CLASSIC,
        overrides={"show_settings": KeyBinding(("e",))},
    )
    assert resolved.bindings["show_settings"].keys == ("e",)
    assert resolved.bindings["export_excel"].keys == ("E",)
    assert resolved.problems == ()


def test_verdraengte_aktion_ohne_resttaste_faellt_raus_und_wird_gemeldet() -> None:
    resolved = resolve_keymap(
        KeymapStyle.CLASSIC,
        CLASSIC,
        overrides={"show_settings": KeyBinding(("e", "E"))},
    )
    assert "export_excel" not in resolved.bindings
    assert [problem.action for problem in resolved.problems] == ["export_excel"]


def test_korrektur_darf_quit_nicht_die_letzte_taste_nehmen() -> None:
    resolved = resolve_keymap(
        KeymapStyle.CLASSIC,
        CLASSIC,
        overrides={"show_settings": KeyBinding(("q", "Q"))},
    )
    assert resolved.bindings["quit"].keys == ("q", "Q")
    assert resolved.bindings["show_settings"].keys == ("s", "S")
    assert len(resolved.problems) == 1


def test_korrektur_darf_quit_eine_von_zwei_tasten_nehmen() -> None:
    resolved = resolve_keymap(
        KeymapStyle.CLASSIC,
        CLASSIC,
        overrides={"show_settings": KeyBinding(("Q",))},
    )
    assert resolved.bindings["quit"].keys == ("q",)
    assert resolved.problems == ()


def test_korrektur_auf_unbekannte_aktion_wird_uebergangen() -> None:
    resolved = resolve_keymap(
        KeymapStyle.CLASSIC,
        CLASSIC,
        overrides={"gibtsnicht": KeyBinding(("z",))},
    )
    assert "gibtsnicht" not in resolved.bindings
    assert len(resolved.problems) == 1
    assert resolved.problems[0].action == "gibtsnicht"


# --- Einlesen aus der Einstellungsdatei -----------------------------------------


def test_parse_overrides_liest_liste_und_einzeltaste() -> None:
    parsed, problems = parse_overrides({"show_settings": ["f2", "alt+s"], "toggle_log": "alt+l"})
    assert parsed["show_settings"].keys == ("f2", "alt+s")
    assert parsed["toggle_log"].keys == ("alt+l",)
    assert problems == ()


def test_parse_overrides_uebergeht_einen_leeren_eintrag() -> None:
    parsed, problems = parse_overrides({"show_settings": [], "toggle_log": ["alt+l"]})
    assert "show_settings" not in parsed
    assert "toggle_log" in parsed
    assert len(problems) == 1


def test_parse_overrides_meldet_falschen_dateityp() -> None:
    parsed, problems = parse_overrides(["f2", "f3"])
    assert parsed == {}
    assert len(problems) == 1


def test_parse_overrides_vertraegt_none() -> None:
    parsed, problems = parse_overrides(None)
    assert parsed == {}
    assert problems == ()


def test_parse_overrides_meldet_zahl_statt_taste() -> None:
    parsed, problems = parse_overrides({"show_settings": 42})
    assert parsed == {}
    assert len(problems) == 1


# --- Vim-Ebene ------------------------------------------------------------------


def test_vim_meldet_eine_verdeckte_aktion() -> None:
    resolved = resolve_keymap(KeymapStyle.CLASSIC, CLASSIC, vim_navigation=True)
    verdeckt = {problem.action: problem.key for problem in resolved.problems}
    assert verdeckt == {"toggle_log": "l"}


def test_vim_meldet_nichts_im_f_tasten_stil() -> None:
    resolved = resolve_keymap(
        KeymapStyle.FUNCTION_KEYS,
        CLASSIC,
        function_keys=COMMON_FUNCTION_KEYS,
        vim_navigation=True,
    )
    assert resolved.problems == ()


def test_vim_stoert_sich_nicht_an_pfeiltasten() -> None:
    resolved = resolve_keymap(
        KeymapStyle.CLASSIC,
        {"quit": KeyBinding(("q",)), "hoch": KeyBinding(("up",))},
        vim_navigation=True,
    )
    assert resolved.problems == ()


def test_ohne_vim_wird_nichts_gemeldet() -> None:
    resolved = resolve_keymap(KeymapStyle.CLASSIC, CLASSIC, vim_navigation=False)
    assert resolved.problems == ()


# --- Plattform-Vorgabe ----------------------------------------------------------


@pytest.mark.parametrize(
    ("platform_name", "erwartet"),
    [
        ("darwin", KeymapStyle.CLASSIC),
        ("win32", KeymapStyle.FUNCTION_KEYS),
        ("linux", KeymapStyle.FUNCTION_KEYS),
    ],
)
def test_plattform_vorgabe(platform_name: str, erwartet: KeymapStyle) -> None:
    assert default_style_for_platform(platform_name) is erwartet


# --- Sonstiges ------------------------------------------------------------------


def test_bindung_ohne_taste_ist_ein_fehler() -> None:
    with pytest.raises(ValueError):
        KeyBinding(())


# --- Vim-Bindungen fuers Widget --------------------------------------------------


def test_vim_navigation_bindings_laesst_die_pfeiltasten_weg() -> None:
    tasten = {key for key, _ in vim_navigation_bindings()}
    assert tasten == {"j", "k", "h", "l", "g", "G", "ctrl+u", "ctrl+d"}


def test_vim_navigation_bindings_zeigt_auf_die_aktionen_der_datatable() -> None:
    # Alle Ziele muessen Aktionen sein, die Textuals DataTable von Haus aus hat.
    aktionen = {action for _, action in vim_navigation_bindings()}
    assert aktionen == {
        "cursor_up",
        "cursor_down",
        "cursor_left",
        "cursor_right",
        "scroll_top",
        "scroll_bottom",
        "page_up",
        "page_down",
    }


def test_plattform_wird_erst_beim_aufruf_gelesen(monkeypatch: pytest.MonkeyPatch) -> None:
    # Gegenprobe zur eingefrorenen Vorgabe: stuende sys.platform als
    # Default im Funktionskopf, waere er beim Import ausgewertet und dieser
    # monkeypatch wirkungslos - der Test waere gruen, ohne etwas zu pruefen.
    monkeypatch.setattr("textual_widgets.keymap.sys.platform", "darwin")
    assert default_style_for_platform() is KeymapStyle.CLASSIC
    monkeypatch.setattr("textual_widgets.keymap.sys.platform", "win32")
    assert default_style_for_platform() is KeymapStyle.FUNCTION_KEYS
