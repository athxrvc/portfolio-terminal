"""Contacts: a selectable list of links to open or copy."""

from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import OptionList, Static
from textual.widgets.option_list import Option

from ..content import Section
from ..theme import ACCENT, DIM
from .links import copy_link, open_link


class ContactsView(Vertical):
    HINTS = [("↑↓", "select"), ("⏎", "open"), ("c", "copy")]

    def __init__(self, section: Section, **kwargs) -> None:
        super().__init__(**kwargs)
        self.section = section
        self.contacts = section.contacts

    def compose(self) -> ComposeResult:
        if self.section.intro:
            yield Static(Text(self.section.intro, style=DIM), id="intro")
        yield OptionList(id="contacts")

    def on_mount(self) -> None:
        self.border_title = self.section.title
        width = max((len(c.label) for c in self.contacts), default=0) + 3
        options = []
        for i, c in enumerate(self.contacts):
            t = Text(no_wrap=True, overflow="ellipsis")
            t.append(c.label.ljust(width), style=f"bold {ACCENT}")
            # Unstyled so the highlight can recolour it; OSC 8 makes it clickable
            # in terminals that support hyperlinks.
            t.append(c.value, style=f"link {c.url}")
            t.append("  ↗", style=DIM)
            options.append(Option(t, id=f"contact-{i}"))
        lst = self.query_one("#contacts", OptionList)
        lst.add_options(options)
        if options:
            lst.highlighted = 0

    def focus_content(self) -> None:
        self.query_one("#contacts", OptionList).focus()

    def _selected(self):
        row = self.query_one("#contacts", OptionList).highlighted
        return self.contacts[row] if row is not None else None

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        event.stop()
        self.open_link()

    def open_link(self) -> None:
        c = self._selected()
        if c:
            open_link(self.app, c.url, c.label)

    def copy_link(self) -> None:
        c = self._selected()
        if c:
            copy_link(self.app, c.url, c.label)
