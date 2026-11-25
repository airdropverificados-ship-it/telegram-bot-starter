"""SQLite storage (standard library only).

Stores the minimum data Telegram already sends with every update:
the user's Telegram id, their username (if any) and the first time
the bot saw them, plus a simple per-user message counter.
No other personal data is collected.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id    INTEGER PRIMARY KEY,
    username   TEXT,
    first_seen TEXT NOT NULL DEFAULT (datetime('now')),
    counter    INTEGER NOT NULL DEFAULT 0
);
"""


def init_db(path: str | Path) -> sqlite3.Connection:
    """Open (creating it if needed) and initialise the database.

    ``check_same_thread=False`` because the webhook server handles
    requests on worker threads; callers must serialise access
    (TelegramBot does this with a lock).
    """
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.execute(_SCHEMA)
    conn.commit()
    return conn


def upsert_user(conn: sqlite3.Connection, user_id: int, username: str | None) -> None:
    """Insert a user on first sight, or refresh their username.

    ``first_seen`` is only set on the first insert and never overwritten.
    """
    conn.execute(
        """
        INSERT INTO users (user_id, username)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET username = excluded.username
        """,
        (user_id, username),
    )
    conn.commit()


def increment_counter(conn: sqlite3.Connection, user_id: int) -> int:
    """Add one to the user's counter and return the new value."""
    conn.execute(
        "UPDATE users SET counter = counter + 1 WHERE user_id = ?", (user_id,)
    )
    conn.commit()
    row = conn.execute(
        "SELECT counter FROM users WHERE user_id = ?", (user_id,)
    ).fetchone()
    return row[0] if row else 0


def get_counter(conn: sqlite3.Connection, user_id: int) -> int:
    """Return the user's counter (0 if the user is unknown)."""
    row = conn.execute(
        "SELECT counter FROM users WHERE user_id = ?", (user_id,)
    ).fetchone()
    return row[0] if row else 0


def get_user(conn: sqlite3.Connection, user_id: int) -> dict | None:
    """Return a user's row as a dict, or None if unknown."""
    row = conn.execute(
        "SELECT user_id, username, first_seen, counter FROM users "
        "WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    if row is None:
        return None
    return {
        "user_id": row[0],
        "username": row[1],
        "first_seen": row[2],
        "counter": row[3],
    }
