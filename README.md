# portfolio-terminal

A personal portfolio that is accessed over **SSH** instead of a browser. Run
`ssh ssh.athxrvc.co.uk` and you land in an interactive terminal UI — an ASCII
image, a short bio, and an arrow-key menu (Creations · Reflections ·
Contacts) you can navigate without ever getting a shell.

## What it is

When someone connects over SSH, the server drops them straight into a
text-based UI (no login, no shell, no file access). They browse with the arrow
keys, press `enter` to open a section, `esc` to go back, and `q` to quit. Every
visitor gets their own isolated session.

## What's being used to build it

| Piece | Tool | Why |
|-------|------|-----|
| Language | **Python** | Single language for both the server and the UI |
| Terminal UI | **[Textual](https://textual.textualize.io/)** | Screens, arrow-key navigation, and CSS-like styling |
| SSH server | **[AsyncSSH](https://asyncssh.readthedocs.io/)** | Pure-Python asyncio SSH server with PTY support |
| Tooling | **[uv](https://docs.astral.sh/uv/)** | Fast environment + dependency management |

**How the two halves connect:** AsyncSSH accepts each connection anonymously and
launches the Textual app inside a pseudo-terminal (PTY), forwarding raw bytes
between the SSH channel and the app. No shell, command execution, or file
transfer is ever exposed to the client.

## Tech stack

**Python (≥ 3.11)** — the single language for everything. Both the SSH server
and the terminal UI are written in Python, so there's no second runtime to
manage. We need 3.11+ for the built-in `tomllib` (reading the content file) and
modern `asyncio`.

**Textual** — the terminal UI framework. It draws everything the visitor sees
and handles interaction:
- *Screens* — each view (home, listing, detail, contacts) is its own screen you
  push and pop like pages.
- *Key bindings* — arrow keys to move, `enter` to open, `esc` to go back, `q` to
  quit.
- *CSS-like styling* — colors, padding, and layout live in
  [theme.tcss](src/portfolio/theme.tcss) instead of being hard-coded.
- *Auto-redraw* when the terminal is resized.

**Rich** — the text-rendering engine underneath Textual (Textual is built on
it). It handles colors, styled text spans, and alignment; we use it directly to
build the styled bio and menu text. It ships with Textual, so there's nothing
separate to install or run.

**AsyncSSH** — the SSH server, and the part that makes `ssh ssh.athxrvc.co.uk`
work. It listens for connections, accepts them anonymously, allocates a
pseudo-terminal (PTY) per visitor, launches the Textual app for that session,
and pipes bytes back and forth — while exposing no shell, command execution, or
file transfer. Being pure Python (no OpenSSH dependency) keeps deployment
simple.

**uv** — the package and environment manager (by Astral). It creates the virtual
environment, installs and locks dependencies, and runs the project
(`uv run portfolio-tui`). It's the fast, modern replacement for
`pip` + `venv`.

**TOML** — the content format. All copy (bio, projects, links) lives in
[src/portfolio/content/portfolio.toml](src/portfolio/content/portfolio.toml) and
is read with Python's built-in `tomllib`, keeping text separate from code so the
portfolio can be edited without touching the UI.

## Project layout

```
src/portfolio/
├── server.py          # AsyncSSH server + per-session PTY bridge
├── app.py / tui.py    # the Textual application
├── screens/           # home, listing, detail, contacts
├── content/           # copy, split by section (data-driven)
│   ├── home.toml          # bio + the home-screen menu
│   ├── creations.toml     # Creations section
│   ├── reflections.toml   # Reflections section
│   └── contacts.toml      # Contacts links
├── art/               # ASCII portrait + name banner
├── theme.py           # color palette
└── theme.tcss         # Textual stylesheet
```

All text content lives in [src/portfolio/content](src/portfolio/content), split
into one file per section, so the site can be updated without touching any UI
code. The menu in [home.toml](src/portfolio/content/home.toml) drives the rest:
each entry loads the matching `content/<key>.toml`, so adding a section is just a
new menu entry plus a new file.

## Running it locally

```bash
cd ~/Desktop/portfolio-terminal

# the UI directly in your terminal
uv run portfolio-tui

# — or the full SSH experience —
uv run portfolio-ssh          # starts the server on 127.0.0.1:2222
ssh -p 2222 127.0.0.1         # connect like a visitor would
```

Navigate with the arrow keys · `enter` to open · `esc` to go back · `q` to quit.


