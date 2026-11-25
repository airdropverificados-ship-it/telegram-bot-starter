"""Tests for the webhook server, incl. secret verification.

Runs a real HTTP server on an ephemeral localhost port; no network
access beyond loopback, no real token.
"""

import http.client
import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer

from starter.bot import TelegramBot
from starter.config import Config
from starter.webhook import SECRET_HEADER, make_handler, verify_secret


class FakeResponse:
    def __init__(self):
        self.status_code = 200

    def json(self):
        return {"ok": True, "result": {"message_id": 1}}

    def raise_for_status(self):
        pass


class FakeSession:
    """Records POSTs instead of hitting api.telegram.org."""

    def __init__(self):
        self.posts = []

    def post(self, url, json=None, timeout=None):
        self.posts.append({"url": url, "json": json})
        return FakeResponse()


def _make_bot(secret):
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    config = Config(
        bot_token="dummy-token",
        webhook_secret=secret,
        webhook_port=0,
        database_path=tmp.name,
    )
    return TelegramBot(config, session=FakeSession())


class TestVerifySecret(unittest.TestCase):
    def test_no_secret_configured_allows_anything(self):
        self.assertTrue(verify_secret(None, None))
        self.assertTrue(verify_secret(None, "whatever"))

    def test_correct_secret_accepted(self):
        self.assertTrue(verify_secret("s3cret", "s3cret"))

    def test_wrong_or_missing_secret_rejected(self):
        self.assertFalse(verify_secret("s3cret", "wrong"))
        self.assertFalse(verify_secret("s3cret", None))
        self.assertFalse(verify_secret("s3cret", ""))


class TestWebhookServer(unittest.TestCase):
    def _serve(self, secret):
        self.bot = _make_bot(secret)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(self.bot))
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.bot.conn.close()

    def _post(self, path="/webhook", body=None, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        payload = json.dumps(body if body is not None else {}).encode()
        hdrs = {"Content-Type": "application/json"}
        hdrs.update(headers or {})
        conn.request("POST", path, body=payload, headers=hdrs)
        resp = conn.getresponse()
        data = resp.read()
        conn.close()
        return resp.status, data

    def _update(self, text="/ping"):
        return {
            "update_id": 1,
            "message": {
                "message_id": 1,
                "text": text,
                "from": {"id": 5, "username": "tester"},
                "chat": {"id": 5},
            },
        }

    def test_valid_secret_returns_200_and_bot_replies(self):
        self._serve(secret="s3cret")
        status, _ = self._post(
            body=self._update(),
            headers={SECRET_HEADER: "s3cret"},
        )
        self.assertEqual(status, 200)
        sent = self.bot.session.posts
        self.assertEqual(len(sent), 1)
        self.assertTrue(sent[0]["json"]["text"].startswith("pong"))

    def test_wrong_secret_returns_401_and_bot_does_nothing(self):
        self._serve(secret="s3cret")
        status, _ = self._post(
            body=self._update(),
            headers={SECRET_HEADER: "wrong"},
        )
        self.assertEqual(status, 401)
        self.assertEqual(self.bot.session.posts, [])

    def test_missing_secret_returns_401(self):
        self._serve(secret="s3cret")
        status, _ = self._post(body=self._update())
        self.assertEqual(status, 401)
        self.assertEqual(self.bot.session.posts, [])

    def test_no_secret_configured_accepts_requests(self):
        self._serve(secret=None)
        status, _ = self._post(body=self._update())
        self.assertEqual(status, 200)
        self.assertEqual(len(self.bot.session.posts), 1)

    def test_wrong_path_returns_404(self):
        self._serve(secret=None)
        status, _ = self._post(path="/other", body=self._update())
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
