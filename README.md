# portfolio-terminal

SSH-native portfolio built with Python, AsyncSSH, and Textual.
Visitors connect with one command and land directly in an interactive terminal
UI:

```bash
ssh ssh.athxrvc.co.uk
```

## Why this exists

Most portfolios are websites and I can't make good websites. This one is a terminal product experience:

- Connect over SSH
- See ASCII branding + profile content
- Navigate sections with arrow keys
- Never get shell or command execution access


## Quick start (local)

Requirements:

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)

Run the TUI directly:

```bash
uv sync
uv run portfolio-tui
```

Run the SSH server locally:

```bash
uv sync
uv run portfolio-ssh
ssh -p 2222 127.0.0.1
```

By default, local SSH mode listens on `127.0.0.1:2222`.

## Architecture

```text
SSH client
  -> AsyncSSH server (src/portfolio/server.py)
  -> PTY per connection
  -> Textual app process (python -m portfolio.tui)
  -> Rendered interactive UI back to client terminal
```

Key design choice: each connection gets an isolated TUI session in its own
pseudo-terminal.

## Tech stack

| Piece | Tool | Why |
|-------|------|-----|
| Language | Python | Single runtime for server + UI |
| SSH server | [AsyncSSH](https://asyncssh.readthedocs.io/) | Async SSH server with PTY support |
| Terminal UI | [Textual](https://textual.textualize.io/) | Rich terminal UI screens + styling |
| Environment/tooling | [uv](https://docs.astral.sh/uv/) | Fast dependency and run workflow |
| Content format | TOML | Content managed outside code |

## Project layout

```text
src/portfolio/
  server.py        AsyncSSH server + PTY bridge
  app.py           Textual App root
  tui.py           TUI launcher
  content.py       TOML content loading
  screens/         Screen views (home/listing/detail/contacts)
  data/            Portfolio content files
  art/             ASCII assets
  theme.py         Theme constants
  theme.tcss       Textual stylesheet
```

Primary content editing happens in `src/portfolio/data` and
`src/portfolio/art`.

## Production deployment (current live setup)

Infra overview:

- VPS provider: FastHost (Ubuntu)
- Domain: `athxrvc.co.uk`
- DNS record: `ssh.athxrvc.co.uk -> 77.68.125.29`

Port split:

- `22`: portfolio SSH app (public)
- `22222`: OpenSSH admin access (private maintenance)

Systemd service (`/etc/systemd/system/portfolio-ssh.service`):



