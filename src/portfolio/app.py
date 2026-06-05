"""The root Textual application."""

from __future__ import annotations

from textual.app import App

from .screens.home import HomeScreen


class PortfolioApp(App):
    """An SSH-served terminal portfolio."""

    CSS_PATH = "theme.tcss"
    TITLE = "athxrvc"

    def on_mount(self) -> None:
        self.push_screen(HomeScreen())
