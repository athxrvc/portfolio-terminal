"""Contacts screen: a selectable list of links you can open."""

from __future__ import annotations

import webbrowser

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Static

from ..content import get_content
from ..theme import ACCENT, DIM, FG

HINT = "[\u2191 \u2193 to select \u00b7 enter to open \u00b7 esc to go back \u00b7 q to quit]"


class ContactsScreen(Screen):
    BINDINGS = [
        Binding("up", "move(-1)", "prev", show=False),
        Binding("down", "move(1)", "next", show=False),
        Binding("enter", "open", "open", show=False),
        Binding("escape", "back", "back", show=False),
    ]

    selected: reactive[int] = reactive(0)
    status_msg: reactive[str] = reactive("")

    def __init__(self) -> None:
        super().__init__()
        self.contacts = get_content().contacts

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(id="body")
            yield Static(id="hint", classes="hint")

    def on_mount(self) -> None:
        self._render_body()

    def watch_selected(self) -> None:
        self._render_body()

    def watch_status_msg(self) -> None:
        self._render_body()

    def _render_body(self) -> None:
        t = Text()
        t.append("Contacts\n", style=f"bold {ACCENT}")
        t.append("\u2500" * 8 + "\n\n", style=DIM)

        width = max((len(c.label) for c in self.contacts), default=2)
        for i, c in enumerate(self.contacts):
            is_selected = i == self.selected
            t.append("+ " if is_selected else "  ", style=ACCENT if is_selected else DIM)
            t.append(c.label.ljust(width + 2), style=f"bold {ACCENT}")
            value_style = f"bold {ACCENT}" if is_selected else FG
            if c.url:
                # OSC 8 hyperlink: clickable in terminals that support it.
                t.append(c.value, style=f"{value_style} link {c.url}")
            else:
                t.append(c.value, style=value_style)
            t.append("\n")
        self.query_one("#body", Static).update(t)

        hint = Text()
        if self.status_msg:
            hint.append(self.status_msg + "   ", style=ACCENT)
        hint.append(HINT, style=DIM)
        self.query_one("#hint", Static).update(hint)

    def action_move(self, delta: int) -> None:
        if self.contacts:
            self.selected = max(0, min(len(self.contacts) - 1, self.selected + delta))
            self.status_msg = ""

    def action_open(self) -> None:
        if not self.contacts:
            return
        contact = self.contacts[self.selected]
        if not contact.url:
            return
        try:
            opened = webbrowser.open(contact.url, new=2, autoraise=True)
        except Exception:
            opened = False
        if opened:
            self.status_msg = f"\u2192 {contact.value} (opened)"
            return
        # copy_to_clipboard uses OSC 52, which reaches the user's terminal over SSH.
        self.app.copy_to_clipboard(contact.url)
        self.status_msg = f"\u2192 {contact.value} (copied)"

    def action_back(self) -> None:
        self.app.pop_screen()

