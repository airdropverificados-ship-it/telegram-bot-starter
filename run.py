#!/usr/bin/env python3
"""Entry point for telegram-bot-starter.

Usage:
    python run.py --mode polling
    python run.py --mode webhook

Configuration comes from environment variables (see .env.example).
The bot token is never printed or logged.
"""

from __future__ import annotations

import argparse
import logging
import sys

from starter.bot import TelegramBot
from starter.config import ConfigError, load_config
from starter.webhook import run_webhook


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="run.py",
        description="Run the telegram-bot-starter bot.",
    )
    parser.add_argument(
        "--mode",
        choices=["polling", "webhook"],
        default="polling",
        help="how Telegram delivers updates: polling (default) or webhook",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    try:
        config = load_config()
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    bot = TelegramBot(config)
    if args.mode == "webhook":
        run_webhook(bot)
    else:
        bot.run_polling()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
