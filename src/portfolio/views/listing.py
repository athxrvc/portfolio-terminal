"""A master-detail view: a list on the left, the highlighted item on the right."""

from __future__ import annotations

from rich.console import Group, RenderableType
from rich.table import Table
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widget import Widget
from textual.widgets import OptionList, Static
from textual.widgets.option_list import Option

from ..content import Item, Section
from ..theme import ACCENT, DIM, FG, MUTED, Chips
from .links import copy_link, open_link

NARROW_BELOW = 72   # stack the panes vertically under this width
SLIM_BELOW = 100    # give the list a slimmer column under this width
SHORT_BELOW = 22    # tighten the detail pane's padding under this height


def _list_option(item: Item, index: int) -> Option:
    # The title carries no explicit colour so the highlight style can recolour it.
    t = Text(no_wrap=True, overflow="ellipsis")
    t.append(item.title)
    if item.meta:
        t.append("\n" + item.meta, style=DIM)
    return Option(t, id=f"item-{index}")


def _header_option(label: str, first: bool) -> Option:
    text = label if first else "\n" + label
    return Option(Text(text.upper(), style=MUTED), disabled=True)


def _detail(item: Item) -> RenderableType:
    parts: list[RenderableType] = []

    head = Text()
    if item.subtitle:
        head.append(item.subtitle, style=f"bold {ACCENT}")
    if item.info:
        head.append(("\n" if item.subtitle else "") + item.info, style=DIM)
    if head.plain:
        parts.append(head)

    for paragraph in item.body:
        parts += [Text(""), Text(paragraph, style=FG)]

    if item.bullets:
        grid = Table.grid(padding=(0, 1, 0, 0))
        grid.add_column(width=1, no_wrap=True)
        grid.add_column(ratio=1)
        for bullet in item.bullets:
            grid.add_row(Text("▸", style=ACCENT), Text(bullet, style=FG))
        parts += [Text(""), grid]

    if item.tags:
        parts += [Text(""), Chips(item.tags)]

    if item.links:
        links = Table.grid(padding=(0, 2, 0, 0))
        links.add_column(no_wrap=True)
        links.add_column()
        for link in item.links:
            links.add_row(
                Text(link.label, style=DIM),
                Text(link.text + " ↗", style=f"{ACCENT} link {link.url}"),
            )
        parts += [Text(""), links]

    return Group(*parts)


class ListingView(Widget):
    def __init__(self, section: Section, **kwargs) -> None:
        super().__init__(**kwargs)
        self.section = section
        self.items = section.items
        has_links = any(item.links for item in self.items)
        self.HINTS = [("↑↓", "select")]
        if has_links:
            self.HINTS += [("⏎", "open link"), ("c", "copy link")]
        self._option_index: dict[int, int] = {}  # option-list row -> item index

    def compose(self) -> ComposeResult:
        yield OptionList(id="items")
        with VerticalScroll(id="detail"):
            yield Static(id="detail-body")

    def on_mount(self) -> None:
        options: list[Option] = []
        first_item_row: int | None = None
        for group in self.section.groups:
            if group.label:
                options.append(_header_option(group.label, first=not options))
            for item in group.items:
                if first_item_row is None:
                    first_item_row = len(options)
                self._option_index[len(options)] = self.items.index(item)
                options.append(_list_option(item, self.items.index(item)))

        lst = self.query_one("#items", OptionList)
        lst.border_title = self.section.title
        lst.add_options(options)
        if first_item_row is not None:
            lst.highlighted = first_item_row
        self.query_one("#detail", VerticalScroll).can_focus = False

    def on_resize(self) -> None:
        self.set_class(self.size.width < NARROW_BELOW, "-narrow")
        self.set_class(self.size.width < SLIM_BELOW, "-slim")
        self.set_class(self.size.height < SHORT_BELOW, "-short")

    def focus_content(self) -> None:
        self.query_one("#items", OptionList).focus()

    # -- selection ---------------------------------------------------------

    def _selected(self) -> Item | None:
        row = self.query_one("#items", OptionList).highlighted
        idx = self._option_index.get(row) if row is not None else None
        return self.items[idx] if idx is not None else None

    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        item = self.items[self._option_index[event.option_index]]
        detail = self.query_one("#detail", VerticalScroll)
        detail.border_title = item.title
        detail.scroll_home(animate=False)
        self.query_one("#detail-body", Static).update(_detail(item))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        event.stop()
        self.open_link()

    def open_link(self) -> None:
        item = self._selected()
        if item and item.links:
            open_link(self.app, item.links[0].url, item.links[0].label)

    def copy_link(self) -> None:
        item = self._selected()
        if item and item.links:
            copy_link(self.app, item.links[0].url, item.links[0].label)
