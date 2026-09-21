"""Palette and small rendering helpers shared by every view.

The same hex values are declared as variables at the top of ``theme.tcss``;
keep the two in sync.
"""

from __future__ import annotations

from rich.cells import cell_len
from rich.console import Console, ConsoleOptions, RenderResult
from rich.style import Style
from rich.text import Text
from textual.theme import Theme

BG = "#0a0c10"       # page background
SURFACE = "#10141b"  # bars and panels
RAISED = "#171d27"   # highlighted row, chips
LINE = "#222a35"     # borders and rules
FG = "#c9d1d9"       # primary text
DIM = "#7d8794"      # secondary text
MUTED = "#4b5563"    # separators, hints of structure
ACCENT = "#7ad1c0"   # teal
ACCENT_2 = "#8ab4f8" # blue, paired with the teal in gradients
TITLE = "#eef2f6"    # bright titles
OK = "#7ee787"       # the "online" dot

THEME = Theme(
    name="portfolio",
    primary=ACCENT,
    secondary=ACCENT_2,
    accent=ACCENT,
    foreground=FG,
    background=BG,
    surface=SURFACE,
    panel=RAISED,
    success=OK,
    dark=True,
)


def _rgb(color: str) -> tuple[int, int, int]:
    c = color.lstrip("#")
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


def mix(a: str, b: str, t: float) -> str:
    """Blend colour ``a`` toward ``b`` by ``t`` (0..1)."""
    (ar, ag, ab), (br, bg, bb) = _rgb(a), _rgb(b)
    return "#{:02x}{:02x}{:02x}".format(
        round(ar + (br - ar) * t),
        round(ag + (bg - ag) * t),
        round(ab + (bb - ab) * t),
    )


class Chips:
    """A row of tag chips that wraps at whatever width it is rendered at."""

    def __init__(self, items: list[str]) -> None:
        self.items = items

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        width = options.max_width
        style = Style(color=FG, bgcolor=RAISED)
        line = Text(no_wrap=True)
        used = 0
        first_row = True
        for item in self.items:
            chip = f" {item} "
            w = cell_len(chip)
            if used and used + 1 + w > width:
                yield line
                yield Text("")  # air between rows so the chips don't fuse into a slab
                line, used, first_row = Text(no_wrap=True), 0, False
            if used:
                line.append(" ")
                used += 1
            line.append(chip, style=style)
            used += w
        if used or first_row:
            yield line
