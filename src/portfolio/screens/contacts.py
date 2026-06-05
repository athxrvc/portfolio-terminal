"""Contacts screen: a simple aligned list of links."""

from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Static

from ..content import get_content
from ..theme import ACCENT, DIM, FG


class ContactsScreen(Screen):
    BINDINGS = [
        Binding("escape", "back", "back", show=False),
    ]

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(self._body(), id="body")
            yield Static(Text("[esc] back", style=DIM), classes="hint")

    def _body(self) -> Text:
        contacts = get_content().contacts
        t = Text()
        t.append("Contacts\n", style=f"bold {ACCENT}")
        t.append("\u2500" * 8 + "\n\n", style=DIM)

        width = max((len(c.label) for c in contacts), default=2)
        for c in contacts:
            t.append(c.label.ljust(width + 3), style=f"bold {ACCENT}")
            t.append(c.value + "\n", style=FG)
        return t

    def action_back(self) -> None:
        self.app.pop_screen()
