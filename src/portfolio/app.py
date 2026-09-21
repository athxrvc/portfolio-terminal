"""The root Textual application."""

from __future__ import annotations

from textual.app import App
from textual.binding import Binding

from .shell import Shell
from .theme import THEME


class PortfolioApp(App):
    """An SSH-served terminal portfolio."""

    CSS_PATH = "theme.tcss"
    TITLE = "athxrvc"
    # The command palette exposes app-level commands (e.g. saving a screenshot
    # to disk) that anonymous visitors have no business running on the server.
    ENABLE_COMMAND_PALETTE = False
    BINDINGS = [
        Binding("q", "quit", "quit", show=False),
        Binding("ctrl+c", "quit", "quit", show=False, priority=True),
    ]

    def on_mount(self) -> None:
        self.register_theme(THEME)
        self.theme = THEME.name
        self.push_screen(Shell())
