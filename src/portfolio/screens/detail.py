"""Detail screen for a single item."""

from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Static

from ..content import Item
from ..theme import ACCENT, DIM, TITLE


class DetailScreen(Screen):
    BINDINGS = [
        Binding("escape", "back", "back", show=False),
    ]

    def __init__(self, item: Item, section_title: str = "") -> None:
        super().__init__()
        self.item = item
        self.section_title = section_title

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(self._body(), id="body")
            yield Static(Text("[esc] back", style=DIM), classes="hint")

    def _body(self) -> Text:
        t = Text()
        if self.section_title:
            t.append(self.section_title + "\n", style=f"bold {ACCENT}")
            t.append("\u2500" * max(8, len(self.section_title)) + "\n\n", style=DIM)

        t.append(self.item.title + "\n", style=f"bold {TITLE}")
        if self.item.meta:
            t.append(self.item.meta + "\n", style=DIM)
        t.append("\n")

        for paragraph in self.item.body:
            t.append(paragraph + "\n\n", style=DIM)

        if self.item.url:
            t.append("View \u2192 ", style=f"bold {ACCENT}")
            t.append(self.item.url + "\n", style=ACCENT)
        return t

    def action_back(self) -> None:
        self.app.pop_screen()
