"""Open a link for the visitor, or put it on their clipboard."""

from __future__ import annotations

import os
import webbrowser

from textual.app import App

# Set by the SSH server: a browser launched here would open on the server, not
# on the visitor's machine, so go straight to the clipboard instead.
REMOTE = bool(os.environ.get("PORTFOLIO_REMOTE"))


def _clipboard_text(url: str) -> str:
    return url.removeprefix("mailto:")


def copy_link(app: App, url: str, label: str) -> None:
    # copy_to_clipboard uses OSC 52, which reaches the visitor's terminal over SSH.
    app.copy_to_clipboard(_clipboard_text(url))
    app.notify(_clipboard_text(url), title=f"Copied {label}", timeout=2.5)


def open_link(app: App, url: str, label: str) -> None:
    if not REMOTE:
        try:
            if webbrowser.open(url, new=2, autoraise=True):
                app.notify(_clipboard_text(url), title=f"Opened {label}", timeout=2.5)
                return
        except Exception:
            pass
    copy_link(app, url, label)
