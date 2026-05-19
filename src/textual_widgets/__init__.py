"""Wiederverwendbare Textual-Widgets."""

__version__ = "0.15.0"
__author__ = "Michael Blaess"

from textual_widgets.about_screen import AboutScreen, Quote, load_quotes
from textual_widgets.context_menu import ContextMenuItem, ContextMenuScreen
from textual_widgets.crash_guard import CrashGuard, ErrorScreen
from textual_widgets.date_picker import CalendarGrid, DatePicker, DatePickerScreen
from textual_widgets.hamburger_menu import HamburgerItem, HamburgerMenu
from textual_widgets.log_panel import LogMessage, LogPanel, LogRouter
from textual_widgets.search_history_dropdown import (
    SearchHistoryDropdown,
    SearchInputWithHistory,
)
from textual_widgets.settings_screen import BaseSettingsScreen
from textual_widgets.splitter import HorizontalSplitter, VerticalSplitter
from textual_widgets.terminal_title import reset_terminal_title, set_terminal_title
from textual_widgets.url_input_screen import UrlInputScreen

__all__ = [
    "AboutScreen",
    "BaseSettingsScreen",
    "CalendarGrid",
    "ContextMenuItem",
    "ContextMenuScreen",
    "CrashGuard",
    "DatePicker",
    "DatePickerScreen",
    "ErrorScreen",
    "HamburgerItem",
    "HamburgerMenu",
    "HorizontalSplitter",
    "LogMessage",
    "LogPanel",
    "LogRouter",
    "Quote",
    "SearchHistoryDropdown",
    "SearchInputWithHistory",
    "UrlInputScreen",
    "VerticalSplitter",
    "load_quotes",
    "reset_terminal_title",
    "set_terminal_title",
]
