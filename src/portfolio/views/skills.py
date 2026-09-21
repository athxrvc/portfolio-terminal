"""Skills: labelled groups of chips."""

from __future__ import annotations

from rich.table import Table
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static

from ..content import Section
from ..theme import DIM, Chips

LABEL_WIDTH = 18


class SkillsView(VerticalScroll, can_focus=False):
    HINTS: list[tuple[str, str]] = []

    def __init__(self, section: Section, **kwargs) -> None:
        super().__init__(**kwargs)
        self.section = section

    def compose(self) -> ComposeResult:
        # collapse_padding=False keeps the blank line between groups.
        grid = Table.grid(padding=(0, 2, 1, 0), collapse_padding=False, expand=True)
        grid.add_column(width=LABEL_WIDTH, no_wrap=True)
        grid.add_column(ratio=1)
        for group in self.section.skills:
            grid.add_row(Text(group.label, style=DIM), Chips(group.items))
        yield Static(grid)

    def on_mount(self) -> None:
        self.border_title = self.section.title
