"""SSH front-end: serve the Textual portfolio TUI to anyone who connects.

Each SSH session launches the TUI (``python -m portfolio.tui``) inside a pseudo
terminal and bridges raw bytes between the SSH channel and the PTY. No shell,
no command execution, and no file transfer is ever exposed to the client.

Run locally:

    uv run portfolio-ssh
    ssh -p 2222 127.0.0.1
"""

from __future__ import annotations

import asyncio
import contextlib
import fcntl
import os
import pty
import signal
import struct
import sys
import termios
from pathlib import Path

import asyncssh

PKG_DIR = Path(__file__).resolve().parent
SRC_DIR = PKG_DIR.parent
PROJECT_DIR = SRC_DIR.parent

HOST = os.environ.get("PORTFOLIO_HOST", "127.0.0.1")
PORT = int(os.environ.get("PORTFOLIO_PORT", "2222"))
HOST_KEY_PATH = Path(
    os.environ.get("PORTFOLIO_HOST_KEY", PROJECT_DIR / "keys" / "ssh_host_key")
)

_BUFFER = 65536


def _set_winsize(fd: int, rows: int, cols: int) -> None:
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))


def ensure_host_key(path: Path = HOST_KEY_PATH) -> None:
    """Create a persistent Ed25519 host key on first run."""
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    key = asyncssh.generate_private_key("ssh-ed25519", comment="portfolio-terminal")
    key.write_private_key(str(path))
    with contextlib.suppress(OSError):
        os.chmod(path, 0o600)


class PortfolioSSHServer(asyncssh.SSHServer):
    """Accept everyone anonymously; never grant a shell or exec."""

    def begin_auth(self, username: str) -> bool:
        # Returning False means "no authentication required".
        return False

    def password_auth_supported(self) -> bool:
        return False

    def public_key_auth_supported(self) -> bool:
        return False


async def handle_session(process: asyncssh.SSHServerProcess) -> None:
    term_type = process.get_terminal_type()
    if not term_type:
        process.stdout.write(
            b"This portfolio needs an interactive terminal "
            b"(your client did not request a PTY).\r\n"
        )
        process.exit(1)
        return

    width, height, _pw, _ph = process.get_terminal_size()
    cols, rows = width or 80, height or 24

    master, slave = pty.openpty()
    _set_winsize(master, rows, cols)

    env = dict(os.environ)
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(SRC_DIR) + (os.pathsep + existing if existing else "")
    env["TERM"] = term_type
    env["COLUMNS"] = str(cols)
    env["LINES"] = str(rows)
    env["PYTHONUNBUFFERED"] = "1"

    child = await asyncio.create_subprocess_exec(
        sys.executable,
        "-u",
        "-m",
        "portfolio.tui",
        stdin=slave,
        stdout=slave,
        stderr=slave,
        env=env,
        start_new_session=True,
    )
    os.close(slave)

    loop = asyncio.get_running_loop()

    def forward_output() -> None:
        try:
            data = os.read(master, _BUFFER)
        except OSError:
            data = b""
        if not data:
            loop.remove_reader(master)
            return
        try:
            process.stdout.write(data)
        except (BrokenPipeError, ConnectionResetError, asyncssh.Error):
            loop.remove_reader(master)

    loop.add_reader(master, forward_output)

    async def forward_input() -> None:
        while True:
            try:
                data = await process.stdin.read(_BUFFER)
            except asyncssh.TerminalSizeChanged as exc:
                _set_winsize(master, exc.height, exc.width)
                with contextlib.suppress(ProcessLookupError):
                    child.send_signal(signal.SIGWINCH)
                continue
            except (asyncssh.BreakReceived, asyncssh.SignalReceived):
                continue
            except (asyncssh.Error, ConnectionResetError, BrokenPipeError):
                break
            if not data:
                break
            try:
                os.write(master, data)
            except OSError:
                break

    input_task = asyncio.create_task(forward_input())

    try:
        await child.wait()
    finally:
        loop.remove_reader(master)
        input_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await input_task
        if child.returncode is None:
            with contextlib.suppress(ProcessLookupError):
                child.terminate()
            with contextlib.suppress(asyncio.TimeoutError):
                await asyncio.wait_for(child.wait(), timeout=3)
        with contextlib.suppress(OSError):
            os.close(master)
        with contextlib.suppress(Exception):
            process.exit(child.returncode or 0)


async def start() -> None:
    ensure_host_key()
    server = await asyncssh.create_server(
        PortfolioSSHServer,
        HOST,
        PORT,
        server_host_keys=[str(HOST_KEY_PATH)],
        process_factory=handle_session,
        encoding=None,  # raw bytes between channel and PTY
        keepalive_interval=30,
        login_timeout=20,
    )
    print(f"portfolio-terminal listening on {HOST}:{PORT}")
    print(f"connect with:  ssh -p {PORT} {HOST}")
    async with server:
        await asyncio.Future()


def main() -> None:
    try:
        asyncio.run(start())
    except (OSError, asyncssh.Error) as exc:
        sys.exit(f"portfolio-terminal: failed to start: {exc}")
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
