"""A list screen (Creations, Reflections): pick an item to open its detail."""

from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Static

from ..content import Section
from ..theme import ACCENT, DIM, FG
from .detail import DetailScreen


class ListingScreen(Screen):
    BINDINGS = [
        Binding("up", "move(-1)", "prev", show=False),
        Binding("down", "move(1)", "next", show=False),
        Binding("enter", "open", "open", show=False),
        Binding("escape", "back", "back", show=False),
    ]

    selected: reactive[int] = reactive(0)

    def __init__(self, section: Section) -> None:
        super().__init__()
        self.section = section
        self.items = section.items

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(id="body")
            yield Static(
                Text(
                    "[\u2191 \u2193 to select \u00b7 enter to open \u00b7 esc to go back \u00b7 q to quit]",
                    style=DIM,
                ),
                classes="hint",
            )

    def on_mount(self) -> None:
        self._render_body()

    def watch_selected(self) -> None:
        self._render_body()

    def _render_body(self) -> None:
        t = Text()
        t.append(self.section.title + "\n", style=f"bold {ACCENT}")
        t.append("\u2500" * max(8, len(self.section.title)) + "\n\n", style=DIM)

        index = 0
        for group in self.section.groups:
            if group.label:
                t.append(group.label + "\n", style=DIM)
            for item in group.items:
                is_selected = index == self.selected
                t.append("  + " if is_selected else "    ", style=ACCENT if is_selected else DIM)
                t.append(item.title + "\n", style=f"bold {ACCENT}" if is_selected else FG)
                index += 1
            t.append("\n")

        self.query_one("#body", Static).update(t)

    def action_move(self, delta: int) -> None:
        if self.items:
            self.selected = max(0, min(len(self.items) - 1, self.selected + delta))

    def action_open(self) -> None:
        if self.items:
            self.app.push_screen(DetailScreen(self.items[self.selected], self.section.title))

    def action_back(self) -> None:
        self.app.pop_screen()
