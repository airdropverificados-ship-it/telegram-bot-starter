"""Tests for command routing and /echo behaviour (no network)."""

import unittest

from starter.commands import COMMANDS, Context, dispatch, parse_command


def _ctx(args: str = "") -> Context:
    return Context(user_id=1, username="tester", chat_id=1, args=args, conn=None)


class TestParseCommand(unittest.TestCase):
    def test_plain_command(self):
        self.assertEqual(parse_command("/echo hello"), ("echo", "hello"))

    def test_command_without_args(self):
        self.assertEqual(parse_command("/ping"), ("ping", ""))

    def test_bot_mention_suffix_is_stripped(self):
        self.assertEqual(parse_command("/start@MyBot"), ("start", ""))

    def test_not_a_command(self):
        self.assertIsNone(parse_command("hello"))
        self.assertIsNone(parse_command(""))
        self.assertIsNone(parse_command("/"))

    def test_command_is_case_insensitive(self):
        self.assertEqual(parse_command("/ECHO hi"), ("echo", "hi"))


class TestDispatch(unittest.TestCase):
    def test_start_returns_greeting(self):
        reply = dispatch("/start", _ctx())
        self.assertIn("Hello", reply)

    def test_help_lists_all_commands(self):
        reply = dispatch("/help", _ctx())
        for name in COMMANDS:
            self.assertIn(f"/{name}", reply)

    def test_echo_repeats_text(self):
        self.assertEqual(dispatch("/echo hello world", _ctx()), "hello world")

    def test_echo_without_text_shows_usage(self):
        reply = dispatch("/echo", _ctx())
        self.assertIn("Usage", reply)

    def test_echo_with_only_spaces_shows_usage(self):
        self.assertIn("Usage", dispatch("/echo   ", _ctx()))

    def test_ping_without_storage(self):
        self.assertTrue(dispatch("/ping", _ctx()).startswith("pong"))

    def test_unknown_command(self):
        reply = dispatch("/nope", _ctx())
        self.assertIn("Unknown command", reply)
        self.assertIn("/help", reply)

    def test_non_command_returns_none(self):
        self.assertIsNone(dispatch("just chatting", _ctx()))

    def test_registry_is_extensible(self):
        COMMANDS["shout"] = lambda ctx: ctx.args.upper()
        try:
            self.assertEqual(dispatch("/shout hello", _ctx()), "HELLO")
        finally:
            del COMMANDS["shout"]


if __name__ == "__main__":
    unittest.main()
