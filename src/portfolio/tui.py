"""Run the portfolio TUI directly in the current terminal.

Used both for local development (`uv run portfolio-tui`) and as the program the
SSH server launches for each connection (`python -m portfolio.tui`).
"""

from __future__ import annotations

from .app import PortfolioApp


def main() -> None:
    PortfolioApp().run()


if __name__ == "__main__":
    main()
