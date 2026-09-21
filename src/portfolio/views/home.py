"""Home: gradient wordmark, typed tagline, and a "whoami" fact card."""

from __future__ import annotations

from rich.style import Style
from rich.table import Table
from rich.text import Text
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static

from ..content import Profile
from ..theme import ACCENT, ACCENT_2, BG, DIM, FG, MUTED, TITLE, mix

TICK = 0.03            # seconds per animation frame
TYPE_SPEED = 2         # tagline characters revealed per frame
ROW_FRAMES = 4         # frames between fact rows appearing
BLINK_FRAMES = 16      # frames per cursor blink half-cycle
SWEEP_WIDTH = 7        # half-width of the shimmer band, in columns
SWEEP_SPEED = 2        # columns the shimmer moves per frame
IDLE_FRAMES = 300      # ~9s of stillness between shimmer sweeps
SOLID = set("█▀▄")  # block glyphs get the gradient; the rest are shadow
BIG_MIN_WIDTH = 62     # below this (or when short) use the compact wordmark
BIG_MIN_HEIGHT = 15
KEY_WIDTH = 11


class HomeView(Widget):
    HINTS = [("←→", "tabs"), ("1-6", "jump")]

    def __init__(self, profile: Profile, **kwargs) -> None:
        super().__init__(**kwargs)
        self.profile = profile
        self._chars = 0
        self._rows = 0
        self._row_clock = 0
        self._cursor_on = True
        self._blink_clock = 0
        self._sweep: int | None = -SWEEP_WIDTH
        self._idle = 0

    def compose(self) -> ComposeResult:
        yield Static(id="wordmark")
        yield Static(id="tagline")
        yield Static(id="facts")

    def on_mount(self) -> None:
        # Reserve the card's height up front so rows appearing don't shift the layout.
        self.query_one("#facts", Static).styles.min_height = max(1, len(self.profile.facts))
        self._paint_all()
        self.set_interval(TICK, self._tick)

    def on_resize(self) -> None:
        self._paint_wordmark()

    def skip_intro(self) -> None:
        """Jump to the finished state (the shell calls this on any keypress)."""
        self._chars = len(self.profile.tagline)
        self._rows = len(self.profile.facts)
        self._paint_tagline()
        self._paint_facts()

    # -- animation ---------------------------------------------------------

    @property
    def _intro_done(self) -> bool:
        return self._chars >= len(self.profile.tagline) and self._rows >= len(self.profile.facts)

    def _tick(self) -> None:
        if not self.display:
            return

        tagline_dirty = facts_dirty = False
        if self._chars < len(self.profile.tagline):
            self._chars = min(len(self.profile.tagline), self._chars + TYPE_SPEED)
            tagline_dirty = True
        elif self._rows < len(self.profile.facts):
            self._row_clock += 1
            if self._row_clock % ROW_FRAMES == 0:
                self._rows += 1
                facts_dirty = True
        else:
            self._blink_clock += 1
            if self._blink_clock % BLINK_FRAMES == 0:
                self._cursor_on = not self._cursor_on
                tagline_dirty = True

        wordmark_dirty = False
        if self._sweep is not None:
            self._sweep += SWEEP_SPEED
            wordmark_dirty = True
            if self._sweep > self._wordmark_width() + SWEEP_WIDTH:
                self._sweep = None
                self._idle = 0
        elif self._intro_done:
            self._idle += 1
            if self._idle >= IDLE_FRAMES:
                self._sweep = -SWEEP_WIDTH

        if wordmark_dirty:
            self._paint_wordmark()
        if tagline_dirty:
            self._paint_tagline()
        if facts_dirty:
            self._paint_facts()

    # -- painting ----------------------------------------------------------

    def _paint_all(self) -> None:
        self._paint_wordmark()
        self._paint_tagline()
        self._paint_facts()

    def _art(self) -> list[str]:
        big = self.size.width == 0 or (
            self.size.width >= BIG_MIN_WIDTH and self.size.height >= BIG_MIN_HEIGHT
        )
        art = self.profile.name_art if big else self.profile.name_compact
        return art.split("\n")

    def _wordmark_width(self) -> int:
        return max((len(line) for line in self._art()), default=0)

    def _paint_wordmark(self) -> None:
        lines = self._art()
        width = max((len(line) for line in lines), default=1)
        span = max(1, width - 1)
        base = [mix(ACCENT, ACCENT_2, col / span) for col in range(width)]

        out = Text(no_wrap=True)
        for row, line in enumerate(lines):
            for col, ch in enumerate(line):
                if ch == " ":
                    out.append(" ")
                    continue
                color = base[col]
                if self._sweep is not None:
                    d = abs(col - self._sweep)
                    if d < SWEEP_WIDTH:
                        color = mix(color, "#ffffff", 0.8 * (1 - d / SWEEP_WIDTH))
                if ch not in SOLID:
                    color = mix(color, BG, 0.62)
                out.append(ch, style=Style(color=color))
            if row < len(lines) - 1:
                out.append("\n")
        self.query_one("#wordmark", Static).update(out)

    def _paint_tagline(self) -> None:
        tagline = self.profile.tagline
        t = Text(tagline[: self._chars], style=f"bold {TITLE}")
        typing = self._chars < len(tagline)
        t.append("▌" if typing or self._cursor_on else " ", style=ACCENT)
        # The untyped rest is painted in the background colour so the tagline
        # claims its final (possibly wrapped) height from the first frame.
        t.append(tagline[self._chars :], style=Style(color=BG))
        self.query_one("#tagline", Static).update(t)

    def _paint_facts(self) -> None:
        # A grid keeps wrapped values aligned under their own column.
        grid = Table.grid(padding=(0, 2, 0, 0))
        grid.add_column(width=KEY_WIDTH, no_wrap=True)
        grid.add_column(ratio=1)
        for fact in self.profile.facts[: self._rows]:
            value = Text()
            for j, part in enumerate(fact.value.split(" · ")):
                if j:
                    value.append(" · ", style=MUTED)
                value.append(part, style=FG)
            grid.add_row(Text(fact.key, style=DIM), value)
        self.query_one("#facts", Static).update(grid)
