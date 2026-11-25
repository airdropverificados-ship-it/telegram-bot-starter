"""Telegram Bot API client + long-polling loop.

Uses ``requests`` only. The token is never logged or printed.
"""

from __future__ import annotations

import logging
import sqlite3
import threading
import time

import requests

from . import commands, storage
from .config import Config

log = logging.getLogger(__name__)

API_BASE = "https://api.telegram.org/bot"


class TelegramBot:
    """A minimal bot: polling, sending, and dispatching updates."""

    def __init__(self, config: Config, session: requests.Session | None = None):
        self.config = config
        self.session = session or requests.Session()
        self.conn: sqlite3.Connection = storage.init_db(config.database_path)
        # The webhook server handles requests on worker threads, so
        # all DB access through handle_update is serialised here.
        self._lock = threading.Lock()

    def _api_url(self, method: str) -> str:
        return f"{API_BASE}{self.config.bot_token}/{method}"

    def api_call(self, method: str, **params) -> dict:
        """Call a Bot API method and return its ``result`` field."""
        resp = self.session.post(self._api_url(method), json=params, timeout=60)
        resp.raise_for_status()
        payload = resp.json()
        if not payload.get("ok"):
            raise RuntimeError(f"Telegram API error for {method}: {payload}")
        return payload["result"]

    def send_message(self, chat_id: int, text: str) -> dict:
        return self.api_call("sendMessage", chat_id=chat_id, text=text)

    def get_updates(self, offset: int | None = None) -> list[dict]:
        params: dict = {"timeout": self.config.polling_timeout}
        if offset is not None:
            params["offset"] = offset
        return self.api_call("getUpdates", **params)

    def handle_update(self, update: dict) -> None:
        """Process one update: record the user, count the message, reply."""
        with self._lock:
            self._handle_update_locked(update)

    def _handle_update_locked(self, update: dict) -> None:
        message = update.get("message") or update.get("edited_message")
        if not message:
            return
        text = message.get("text", "")
        sender = message.get("from", {})
        chat = message.get("chat", {})
        user_id = sender.get("id")
        chat_id = chat.get("id")
        if user_id is None or chat_id is None:
            return

        storage.upsert_user(self.conn, user_id, sender.get("username"))
        storage.increment_counter(self.conn, user_id)

        ctx = commands.Context(
            user_id=user_id,
            username=sender.get("username"),
            chat_id=chat_id,
            args="",
            conn=self.conn,
        )
        reply = commands.dispatch(text, ctx)
        if reply is None:
            reply = (
                "I only understand commands. "
                "Send /help to see what I can do."
            )
        self.send_message(chat_id, reply)

    def run_polling(self) -> None:
        """Long-poll getUpdates forever (until Ctrl-C)."""
        log.info("Polling for updates (timeout=%ss)...", self.config.polling_timeout)
        offset: int | None = None
        while True:
            try:
                updates = self.get_updates(offset)
            except requests.RequestException as exc:
                log.warning("getUpdates failed (%s); retrying in 5s", exc)
                time.sleep(5)
                continue
            for update in updates:
                offset = update["update_id"] + 1
                try:
                    self.handle_update(update)
                except Exception:  # keep polling even if one update fails
                    log.exception("Failed to handle update %s", update.get("update_id"))
