"""Home screen: ASCII portrait, bio, and the section menu."""

from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Static

from ..content import get_content
from ..theme import ACCENT, DIM, FG
from .contacts import ContactsScreen
from .listing import ListingScreen


class HomeScreen(Screen):
    BINDINGS = [
        Binding("left,up", "move(-1)", "prev", show=False),
        Binding("right,down", "move(1)", "next", show=False),
        Binding("enter", "open", "open", show=False),
    ]

    selected: reactive[int] = reactive(0)

    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal(id="columns"):
                yield Static(Text(get_content().profile.portrait, style=DIM), id="portrait")
                yield Static(id="info")
            yield Static(
                Text("[\u2190 \u2192 to select \u00b7 enter to open \u00b7 q to quit]", style=DIM),
                classes="hint",
            )

    def on_mount(self) -> None:
        self._render_info()

    def watch_selected(self) -> None:
        self._render_info()

    def _render_info(self) -> None:
        c = get_content()
        p = c.profile
        t = Text()
        t.append(p.name_art + "\n", style=f"bold {ACCENT}")
        t.append("\n")
        for line in p.intro:
            t.append(line + "\n", style=FG)
        if p.about:
            t.append("\n")
            for line in p.about:
                t.append(line + "\n", style=DIM)
        if p.closing:
            t.append("\n")
            for line in p.closing:
                t.append(line + "\n", style=DIM)
        t.append("\n")

        menu = Text()
        for i, entry in enumerate(c.menu):
            if i:
                menu.append("   ")
            if i == self.selected:
                menu.append(f"+ {entry.label}", style=f"bold {ACCENT}")
            else:
                menu.append(entry.label, style=DIM)
        t.append(menu)

        self.query_one("#info", Static).update(t)

    def action_move(self, delta: int) -> None:
        count = len(get_content().menu)
        if count:
            self.selected = max(0, min(count - 1, self.selected + delta))

    def action_open(self) -> None:
        c = get_content()
        entry = c.menu[self.selected]
        if entry.kind == "contacts":
            self.app.push_screen(ContactsScreen())
            return
        section = c.sections.get(entry.key)
        if section is not None:
            self.app.push_screen(ListingScreen(section))
