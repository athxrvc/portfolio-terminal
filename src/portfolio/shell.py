"""The persistent frame around every view: prompt, tab bar, content, key hints."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from rich.style import Style
from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.events import Key
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import ContentSwitcher, OptionList, Static

from .content import Content, get_content
from .theme import ACCENT, ACCENT_2, DIM, FG, LINE, MUTED, OK, TITLE
from .views.contacts import ContactsView
from .views.home import HomeView
from .views.links import open_link
from .views.listing import ListingView
from .views.skills import SkillsView

TAB_GAP = 3
TAB_INDENT = 2


class Shell(Screen):
    BINDINGS = [
        Binding("left,shift+tab", "step(-1)", "prev tab", show=False),
        Binding("right,tab", "step(1)", "next tab", show=False),
        Binding("escape", "goto(0)", "home", show=False),
        Binding("j", "cursor(1)", "down", show=False),
        Binding("k", "cursor(-1)", "up", show=False),
        Binding("c", "copy", "copy", show=False),
        *[Binding(str(n), f"goto({n - 1})", show=False) for n in range(1, 10)],
    ]

    index: reactive[int] = reactive(0)

    def __init__(self) -> None:
        super().__init__()
        self.content: Content = get_content()
        self.labels = ["home"] + [m.label for m in self.content.menu]
        self.paths = ["~"] + [f"~/{m.key}" for m in self.content.menu]
        self._tz = self._load_timezone()
        self._clock = ""

    # -- layout ------------------------------------------------------------

    def compose(self) -> ComposeResult:
        with Horizontal(id="topbar"):
            yield Static(id="prompt")
            yield Static(id="status")
        yield Static(id="tabs")
        yield Static(id="rule")
        with ContentSwitcher(id="switcher", initial="view-0"):
            yield HomeView(self.content.profile, id="view-0")
            for i, entry in enumerate(self.content.menu, start=1):
                section = self.content.sections[entry.key]
                if entry.kind == "skills":
                    yield SkillsView(section, id=f"view-{i}")
                elif entry.kind == "contacts":
                    yield ContactsView(section, id=f"view-{i}")
                else:
                    yield ListingView(section, id=f"view-{i}")
        with Horizontal(id="footer"):
            yield Static(id="hints")
            yield Static(id="address")

    def on_mount(self) -> None:
        self._render_chrome()
        self._update_clock()
        self.set_interval(1, self._update_clock)

    def on_resize(self) -> None:
        self._render_chrome()

    def on_key(self, event: Key) -> None:
        if self.index == 0:
            self.query_one("#view-0", HomeView).skip_intro()

    # -- navigation --------------------------------------------------------

    def watch_index(self) -> None:
        self.query_one(ContentSwitcher).current = f"view-{self.index}"
        self._render_chrome()
        self.call_after_refresh(self._focus_view)

    def _view(self):
        return self.query_one(f"#view-{self.index}")

    def _focus_view(self) -> None:
        focus = getattr(self._view(), "focus_content", None)
        if focus:
            focus()
        else:
            self.set_focus(None)

    def action_goto(self, index: int) -> None:
        if 0 <= index < len(self.labels):
            self.index = index

    def action_step(self, delta: int) -> None:
        self.index = (self.index + delta) % len(self.labels)

    def action_cursor(self, delta: int) -> None:
        focused = self.focused
        if isinstance(focused, OptionList):
            focused.action_cursor_down() if delta > 0 else focused.action_cursor_up()

    def action_open_link(self, url: str, label: str) -> None:
        """Target of clickable links in the views (see views/links.py)."""
        open_link(self.app, url, label)

    def action_copy(self) -> None:
        copy = getattr(self._view(), "copy_link", None)
        if copy:
            copy()

    # -- chrome ------------------------------------------------------------

    def _render_chrome(self) -> None:
        if not self.is_mounted:
            return
        width = self.size.width
        self._render_prompt()
        self._render_tabs(width)
        self._render_footer(width)
        self._render_status()

    def _render_prompt(self) -> None:
        p = self.content.profile
        t = Text(no_wrap=True)
        t.append("◆ ", style=ACCENT)
        t.append(f"{p.handle}@{p.host}", style=f"bold {ACCENT}")
        t.append(":", style=MUTED)
        t.append(self.paths[self.index], style=ACCENT_2)
        t.append(" $", style=MUTED)
        self.query_one("#prompt", Static).update(t)

    def _render_tabs(self, width: int) -> None:
        # Labels shrink to bare numbers on inactive tabs when the bar won't fit.
        full = TAB_INDENT + sum(len(f"{i + 1} {lab}") for i, lab in enumerate(self.labels))
        full += TAB_GAP * (len(self.labels) - 1)
        compact = full > width

        tabs = Text(" " * TAB_INDENT, no_wrap=True)
        rule = Text(" " * TAB_INDENT, no_wrap=True)
        rule_style = Style(color=LINE)
        for i, label in enumerate(self.labels):
            active = i == self.index
            shown = f"{i + 1} {label}" if (active or not compact) else str(i + 1)
            if i:
                tabs.append(" " * TAB_GAP)
                rule.append("─" * TAB_GAP, style=rule_style)
            action = Style(meta={"@click": f"screen.goto({i})"})
            tabs.append(f"{i + 1}", style=(Style(color=ACCENT, bold=True) if active else Style(color=MUTED)) + action)
            if shown != str(i + 1):
                tabs.append(
                    f" {label}",
                    style=(Style(color=TITLE, bold=True) if active else Style(color=DIM)) + action,
                )
            rule.append(
                ("━" if active else "─") * len(shown),
                style=Style(color=ACCENT) if active else rule_style,
            )
        # Carry the rule to the right edge.
        rule.append("─" * max(0, width - len(rule.plain)), style=rule_style)
        self.query_one("#tabs", Static).update(tabs)
        self.query_one("#rule", Static).update(rule)

    def _render_footer(self, width: int) -> None:
        view_hints = list(getattr(self._view(), "HINTS", []))
        tabs = [("←→", "tabs")] if self.index else []
        home = [("esc", "home")] if self.index else []
        quit_ = [("q", "quit")]
        address = self.content.profile.ssh
        show_address = width >= 90
        room = width - 4 - (len(address) + 2 if show_address else 0)

        # Drop the least important hints first until the rest fit.
        for hints in (
            view_hints + tabs + home + quit_,
            view_hints + home + quit_,
            view_hints + quit_,
            quit_,
        ):
            if sum(len(k) + len(lbl) + 4 for k, lbl in hints) - 3 <= room:
                break
        t = Text(no_wrap=True)
        for i, (key, label) in enumerate(hints):
            if i:
                t.append("   ")
            t.append(key, style=f"bold {FG}")
            t.append(f" {label}", style=DIM)
        self.query_one("#hints", Static).update(t)
        self.query_one("#address", Static).display = show_address
        self.query_one("#address", Static).update(Text(address, style=MUTED, no_wrap=True))

    def _render_status(self) -> None:
        p = self.content.profile
        t = Text(no_wrap=True)
        t.append("● ", style=OK)
        if self._clock:
            t.append(f"{p.city} {self._clock}" if p.city else self._clock, style=DIM)
        else:
            t.append("online", style=DIM)
        self.query_one("#status", Static).update(t)

    # -- clock -------------------------------------------------------------

    def _load_timezone(self) -> ZoneInfo | None:
        name = self.content.profile.timezone
        if not name:
            return None
        try:
            return ZoneInfo(name)
        except (ZoneInfoNotFoundError, ValueError):
            return None

    def _update_clock(self) -> None:
        if self._tz is None:
            return
        now = datetime.now(self._tz).strftime("%H:%M")
        if now != self._clock:
            self._clock = now
            self._render_status()
