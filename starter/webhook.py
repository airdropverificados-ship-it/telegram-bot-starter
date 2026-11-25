"""Webhook server (standard library http.server only).

Listens for POST /webhook with a Telegram update as JSON.

If WEBHOOK_SECRET is configured, Telegram must send it in the
``X-Telegram-Bot-Api-Secret-Token`` header (set it when you call
``setWebhook`` with ``secret_token``). Requests with a missing or
wrong secret are rejected with 401 and never reach the bot.
"""

from __future__ import annotations

import json
import logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .bot import TelegramBot

log = logging.getLogger(__name__)

SECRET_HEADER = "X-Telegram-Bot-Api-Secret-Token"


def verify_secret(configured_secret: str | None, provided: str | None) -> bool:
    """True when the request is allowed.

    - No secret configured -> any request is allowed (Telegram sends
      updates only to the URL you registered with setWebhook).
    - Secret configured -> the header must match it exactly.
    """
    if not configured_secret:
        return True
    return provided == configured_secret


def make_handler(bot: TelegramBot):
    """Build a request-handler class bound to one bot instance."""

    class WebhookHandler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, fmt, *args):  # keep stdout clean
            log.debug("%s - %s", self.address_string(), fmt % args)

        def _reply(self, status: int, body: bytes = b"") -> None:
            self.send_response(status)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if body:
                self.wfile.write(body)

        def do_GET(self):  # health check
            if self.path in ("/", "/health"):
                self._reply(200, b"ok")
            else:
                self._reply(404, b"not found")

        def do_POST(self):
            if self.path != "/webhook":
                self._reply(404, b"not found")
                return
            if not verify_secret(
                bot.config.webhook_secret,
                self.headers.get(SECRET_HEADER),
            ):
                self._reply(401, b"unauthorized")
                return
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b"{}"
            try:
                update = json.loads(raw.decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                self._reply(400, b"invalid json")
                return
            try:
                bot.handle_update(update)
            except Exception:
                log.exception("Failed to handle webhook update")
            self._reply(200, b"ok")

    return WebhookHandler


def run_webhook(bot: TelegramBot) -> None:
    """Serve webhooks forever (until Ctrl-C)."""
    server = ThreadingHTTPServer(
        ("0.0.0.0", bot.config.webhook_port), make_handler(bot)
    )
    log.info(
        "Webhook server listening on 0.0.0.0:%d (POST /webhook)",
        bot.config.webhook_port,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
