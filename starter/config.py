"""Configuration for telegram-bot-starter.

All settings come from environment variables. Nothing secret is ever
printed or logged by this module.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


class ConfigError(ValueError):
    """Raised when the environment configuration is invalid."""


@dataclass(frozen=True)
class Config:
    """Runtime configuration, loaded once at startup."""

    bot_token: str
    webhook_secret: str | None = None
    webhook_port: int = 8080
    database_path: str = "bot.db"
    polling_timeout: int = 30

    def __repr__(self) -> str:
        # Never include the token in a repr / log line.
        return (
            f"Config(webhook_secret={'set' if self.webhook_secret else 'unset'}, "
            f"webhook_port={self.webhook_port}, "
            f"database_path={self.database_path!r}, "
            f"polling_timeout={self.polling_timeout})"
        )


def _read_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer, got {raw!r}") from exc


def load_config() -> Config:
    """Load configuration from the environment.

    Raises:
        ConfigError: if BOT_TOKEN is missing/empty or a numeric
            setting cannot be parsed.
    """
    token = os.environ.get("BOT_TOKEN", "").strip()
    if not token:
        raise ConfigError(
            "BOT_TOKEN is not set. Copy .env.example to .env and set "
            "BOT_TOKEN to the token you got from @BotFather, "
            "or export BOT_TOKEN in your shell."
        )

    secret = os.environ.get("WEBHOOK_SECRET", "").strip() or None
    port = _read_int("WEBHOOK_PORT", 8080)
    if not 1 <= port <= 65535:
        raise ConfigError(f"WEBHOOK_PORT must be between 1 and 65535, got {port}")
    timeout = _read_int("POLLING_TIMEOUT", 30)
    if timeout < 0:
        raise ConfigError(f"POLLING_TIMEOUT must be >= 0, got {timeout}")

    return Config(
        bot_token=token,
        webhook_secret=secret,
        webhook_port=port,
        database_path=os.environ.get("DATABASE_PATH", "").strip() or "bot.db",
        polling_timeout=timeout,
    )
