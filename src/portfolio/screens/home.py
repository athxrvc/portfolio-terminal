"""Home screen: ASCII portrait, bio, and the section menu."""

from __future__ import annotations

import random

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Static

from ..content import get_content
from ..theme import ACCENT, DIM, FG, TITLE
from .contacts import ContactsScreen
from .listing import ListingScreen

# Glitter that twinkles around the name banner.
SPARKLES = ["\u2726", "\u2727", "\u22c6", "\u00b7", "+", "*", "\u2735"]
SPARKLE_STYLES = [f"bold {TITLE}", f"bold {ACCENT}", ACCENT, DIM]
GLITTER_INTERVAL = 0.45  # seconds between twinkles


class HomeScreen(Screen):
    BINDINGS = [
        Binding("left,up", "move(-1)", "prev", show=False),
        Binding("right,down", "move(1)", "next", show=False),
        Binding("enter", "open", "open", show=False),
    ]

    selected: reactive[int] = reactive(0)

    _glitter_frame = 0
    _glitter_timer = None

    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal(id="columns"):
                yield Static(Text(get_content().profile.portrait, style=DIM), id="portrait")
                with Vertical(id="info"):
                    yield Static(id="name")
                    yield Static(id="bio")
            yield Static(
                Text("[\u2190 \u2192 to select \u00b7 enter to open \u00b7 q to quit]", style=DIM),
                classes="hint",
            )

    def on_mount(self) -> None:
        self._render_name()
        self._render_bio()
        self._glitter_timer = self.set_interval(GLITTER_INTERVAL, self._twinkle)

    def on_screen_suspend(self) -> None:
        if self._glitter_timer is not None:
            self._glitter_timer.pause()

    def on_screen_resume(self) -> None:
        if self._glitter_timer is not None:
            self._glitter_timer.resume()

    def watch_selected(self) -> None:
        self._render_bio()

    def _twinkle(self) -> None:
        self._glitter_frame += 1
        self._render_name()

    def _render_name(self) -> None:
        self.query_one("#name", Static).update(
            self._glitter(get_content().profile.name_art, self._glitter_frame)
        )

    @staticmethod
    def _glitter(name_art: str, frame: int) -> Text:
        """Render the name banner with sparkles scattered in the surrounding air."""
        lines = name_art.split("\n")
        while lines and not lines[-1].strip():
            lines.pop()
        max_w = max((len(ln) for ln in lines), default=0)

        left, right, sky_top, sky_bottom = 3, 6, 1, 1
        width = left + max_w + right
        rows = sky_top + len(lines) + sky_bottom

        chars = [[" "] * width for _ in range(rows)]
        styles: list[list[str | None]] = [[None] * width for _ in range(rows)]

        # Place the name strokes, leaving its internal spaces blank.
        for r, ln in enumerate(lines):
            for c, ch in enumerate(ln):
                if ch != " ":
                    chars[sky_top + r][left + c] = ch
                    styles[sky_top + r][left + c] = f"bold {ACCENT}"

        # Candidate sparkle cells: the sky rows and the left/right margins only,
        # so glitter floats around the name rather than inside the letters.
        candidates: list[tuple[int, int]] = []
        for r in range(rows):
            in_name_row = sky_top <= r < sky_top + len(lines)
            for c in range(width):
                if in_name_row and left <= c < left + max_w:
                    continue
                candidates.append((r, c))

        rng = random.Random(frame)
        rng.shuffle(candidates)
        count = max(8, len(candidates) // 9)
        for r, c in candidates[:count]:
            chars[r][c] = rng.choice(SPARKLES)
            styles[r][c] = rng.choice(SPARKLE_STYLES)

        out = Text()
        for r in range(rows):
            for c in range(width):
                out.append(chars[r][c], style=styles[r][c] or "")
            out.append("\n")
        return out

    def _render_bio(self) -> None:
        c = get_content()
        p = c.profile
        t = Text()
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

        self.query_one("#bio", Static).update(t)

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
