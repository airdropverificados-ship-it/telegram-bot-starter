"""Command registry and built-in commands.

Adding a new command is two steps:

1. Write a function ``def my_command(ctx) -> str``.
2. Register it: ``COMMANDS["mycommand"] = my_command``.

A handler receives a :class:`Context` (the update's user, the raw
arguments after the command name, and the storage connection) and
returns the reply text to send back to the chat.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from . import storage


@dataclass
class Context:
    """Everything a command handler needs."""

    user_id: int
    username: str | None
    chat_id: int
    args: str  # text after the command name, stripped
    conn: sqlite3.Connection | None = None


def cmd_start(ctx: Context) -> str:
    """Say hello and point to /help."""
    return (
        "Hello! I'm a Telegram bot built with the telegram-bot-starter "
        "template.\n\n"
        "Send /help to see what I can do."
    )


def cmd_help(ctx: Context) -> str:
    """List all available commands."""
    lines = ["Available commands:"]
    for name in sorted(COMMANDS):
        lines.append(f"/{name} — {COMMANDS[name].__doc__ or ''}".rstrip())
    return "\n".join(lines)


def cmd_echo(ctx: Context) -> str:
    """Repeat back the text after the command."""
    if not ctx.args:
        return "Usage: /echo <text>\nExample: /echo hello world"
    return ctx.args


def cmd_ping(ctx: Context) -> str:
    """Reply with pong, and your message count if storage is available."""
    if ctx.conn is not None:
        count = storage.get_counter(ctx.conn, ctx.user_id)
        return f"pong 🏓\nYou've sent {count} message(s) so far."
    return "pong 🏓"


# The registry: command name (without the leading slash) -> handler.
COMMANDS: dict[str, object] = {
    "start": cmd_start,
    "help": cmd_help,
    "echo": cmd_echo,
    "ping": cmd_ping,
}


def parse_command(text: str) -> tuple[str, str] | None:
    """Split ``/command args`` into (command, args).

    Returns None when the text is not a command. A ``@BotName`` suffix
    (``/start@MyBot``) is stripped, as Telegram sends it in groups.
    """
    if not text or not text.startswith("/"):
        return None
    first, _, rest = text[1:].partition(" ")
    name = first.split("@", 1)[0].lower()
    if not name:
        return None
    return name, rest.strip()


def dispatch(text: str, ctx: Context) -> str | None:
    """Route a message to its command handler.

    Returns the reply text, or None when the message is not a
    recognised command.
    """
    parsed = parse_command(text)
    if parsed is None:
        return None
    name, args = parsed
    handler = COMMANDS.get(name)
    if handler is None:
        return f"Unknown command: /{name}\nSend /help to see what I can do."
    ctx.args = args
    return handler(ctx)  # type: ignore[operator]
