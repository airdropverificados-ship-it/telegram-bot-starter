"""Tests for environment-based configuration validation."""

import os
import unittest
from unittest import mock

from starter.config import ConfigError, load_config


class TestLoadConfig(unittest.TestCase):
    def _env(self, **overrides):
        env = {
            "BOT_TOKEN": "dummy-token",
            "WEBHOOK_SECRET": "",
            "WEBHOOK_PORT": "",
            "DATABASE_PATH": "",
            "POLLING_TIMEOUT": "",
        }
        env.update(overrides)
        return {k: v for k, v in env.items() if v != ""}

    def test_missing_bot_token_fails_with_clear_error(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ConfigError) as cm:
                load_config()
        self.assertIn("BOT_TOKEN", str(cm.exception))

    def test_empty_bot_token_fails(self):
        with mock.patch.dict(os.environ, {"BOT_TOKEN": "   "}, clear=True):
            with self.assertRaises(ConfigError):
                load_config()

    def test_defaults(self):
        with mock.patch.dict(os.environ, self._env(), clear=True):
            cfg = load_config()
        self.assertEqual(cfg.bot_token, "dummy-token")
        self.assertIsNone(cfg.webhook_secret)
        self.assertEqual(cfg.webhook_port, 8080)
        self.assertEqual(cfg.database_path, "bot.db")
        self.assertEqual(cfg.polling_timeout, 30)
        # The token must never appear in the repr (no leaking into logs).
        self.assertNotIn("dummy-token", repr(cfg))

    def test_explicit_values(self):
        env = self._env(
            WEBHOOK_SECRET="s3cret",
            WEBHOOK_PORT="9000",
            DATABASE_PATH="/tmp/x.db",
            POLLING_TIMEOUT="10",
        )
        with mock.patch.dict(os.environ, env, clear=True):
            cfg = load_config()
        self.assertEqual(cfg.webhook_secret, "s3cret")
        self.assertEqual(cfg.webhook_port, 9000)
        self.assertEqual(cfg.database_path, "/tmp/x.db")
        self.assertEqual(cfg.polling_timeout, 10)

    def test_bad_port_fails(self):
        with mock.patch.dict(os.environ, self._env(WEBHOOK_PORT="abc"), clear=True):
            with self.assertRaises(ConfigError):
                load_config()
        with mock.patch.dict(os.environ, self._env(WEBHOOK_PORT="70000"), clear=True):
            with self.assertRaises(ConfigError):
                load_config()

    def test_negative_timeout_fails(self):
        with mock.patch.dict(os.environ, self._env(POLLING_TIMEOUT="-1"), clear=True):
            with self.assertRaises(ConfigError):
                load_config()


if __name__ == "__main__":
    unittest.main()
