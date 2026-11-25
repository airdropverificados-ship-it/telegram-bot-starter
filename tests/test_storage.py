"""Tests for SQLite storage (stdlib sqlite3, in-memory DB)."""

import sqlite3
import unittest

from starter import storage


class TestStorage(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.execute(storage._SCHEMA)
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    def test_upsert_new_user(self):
        storage.upsert_user(self.conn, 42, "alice")
        user = storage.get_user(self.conn, 42)
        self.assertEqual(user["user_id"], 42)
        self.assertEqual(user["username"], "alice")
        self.assertEqual(user["counter"], 0)
        self.assertTrue(user["first_seen"])

    def test_upsert_updates_username_but_keeps_first_seen(self):
        storage.upsert_user(self.conn, 42, "alice")
        first_seen = storage.get_user(self.conn, 42)["first_seen"]
        storage.upsert_user(self.conn, 42, "alice2")
        user = storage.get_user(self.conn, 42)
        self.assertEqual(user["username"], "alice2")
        self.assertEqual(user["first_seen"], first_seen)
        # Still exactly one row.
        count = self.conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        self.assertEqual(count, 1)

    def test_upsert_without_username(self):
        storage.upsert_user(self.conn, 7, None)
        self.assertIsNone(storage.get_user(self.conn, 7)["username"])

    def test_counter_starts_at_zero_and_increments(self):
        self.assertEqual(storage.get_counter(self.conn, 99), 0)
        storage.upsert_user(self.conn, 99, None)
        self.assertEqual(storage.increment_counter(self.conn, 99), 1)
        self.assertEqual(storage.increment_counter(self.conn, 99), 2)
        self.assertEqual(storage.get_counter(self.conn, 99), 2)

    def test_counters_are_per_user(self):
        storage.upsert_user(self.conn, 1, None)
        storage.upsert_user(self.conn, 2, None)
        storage.increment_counter(self.conn, 1)
        storage.increment_counter(self.conn, 1)
        storage.increment_counter(self.conn, 2)
        self.assertEqual(storage.get_counter(self.conn, 1), 2)
        self.assertEqual(storage.get_counter(self.conn, 2), 1)

    def test_unknown_user_returns_none(self):
        self.assertIsNone(storage.get_user(self.conn, 12345))


if __name__ == "__main__":
    unittest.main()
