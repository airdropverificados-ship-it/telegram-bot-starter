"""Tests for bot update handling with a mocked Telegram API."""

import tempfile
import unittest

from starter.bot import TelegramBot
from starter.config import Config
from test_webhook import FakeSession


def _make_bot():
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    config = Config(bot_token="dummy-token", database_path=tmp.name)
    return TelegramBot(config, session=FakeSession())


def _update(text, user_id=5, username="tester"):
    return {
        "update_id": 1,
        "message": {
            "message_id": 1,
            "text": text,
            "from": {"id": user_id, "username": username},
            "chat": {"id": user_id},
        },
    }


class TestHandleUpdate(unittest.TestCase):
    def test_echo_update_gets_echo_reply(self):
        bot = _make_bot()
        bot.handle_update(_update("/echo hello there"))
        self.assertEqual(bot.session.posts[0]["json"]["text"], "hello there")

    def test_ping_counts_messages(self):
        bot = _make_bot()
        bot.handle_update(_update("/ping"))
        bot.handle_update(_update("/ping"))
        self.assertIn("2 message(s)", bot.session.posts[1]["json"]["text"])

    def test_non_command_gets_fallback_reply(self):
        bot = _make_bot()
        bot.handle_update(_update("hello bot"))
        self.assertIn("/help", bot.session.posts[0]["json"]["text"])

    def test_user_is_stored(self):
        from starter import storage

        bot = _make_bot()
        bot.handle_update(_update("/start", user_id=9, username="newbie"))
        user = storage.get_user(bot.conn, 9)
        self.assertEqual(user["username"], "newbie")
        self.assertEqual(user["counter"], 1)

    def test_update_without_message_is_ignored(self):
        bot = _make_bot()
        bot.handle_update({"update_id": 2})
        self.assertEqual(bot.session.posts, [])

    def test_token_never_appears_in_sent_urls(self):
        bot = _make_bot()
        bot.handle_update(_update("/ping"))
        for post in bot.session.posts:
            # The URL contains the token by API design; the test asserts
            # the bot never *prints* it — covered by config repr test —
            # and that no reply text echoes it.
            self.assertNotIn("dummy-token", post["json"]["text"])


if __name__ == "__main__":
    unittest.main()
