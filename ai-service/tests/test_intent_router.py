"""Tests for KeyPool and IntentRouter."""
import time
import unittest

from services.intent_router import KeyPool, IntentRouter


class KeyPoolTest(unittest.TestCase):
    def test_single_key_round_robin_returns_same_key(self):
        pool = KeyPool(["key-a"])
        self.assertEqual(pool.get_key(), "key-a")
        self.assertEqual(pool.get_key(), "key-a")
        self.assertEqual(pool.get_key(), "key-a")

    def test_multiple_keys_round_robin(self):
        pool = KeyPool(["key-a", "key-b", "key-c"])
        # First cycle
        self.assertEqual(pool.get_key(), "key-a")
        self.assertEqual(pool.get_key(), "key-b")
        self.assertEqual(pool.get_key(), "key-c")
        # Second cycle
        self.assertEqual(pool.get_key(), "key-a")
        self.assertEqual(pool.get_key(), "key-b")

    def test_cooldown_skips_key(self):
        pool = KeyPool(["key-a", "key-b"], cooldown_seconds=60)
        pool.mark_cooldown("key-a")
        # key-a in cooldown, should skip to key-b
        self.assertEqual(pool.get_key(), "key-b")
        # Next call still returns key-b (key-a still cooling)
        self.assertEqual(pool.get_key(), "key-b")

    def test_cooldown_expires(self):
        pool = KeyPool(["key-a"], cooldown_seconds=0.01)
        pool.mark_cooldown("key-a")
        # key-a in cooldown — still returned (it's the only key)
        self.assertEqual(pool.get_key(), "key-a")
        time.sleep(0.02)
        # After sleep, key-a should be available (cooldown expired)
        self.assertEqual(pool.available_count, 1)

    def test_all_keys_in_cooldown_still_returns_one(self):
        pool = KeyPool(["key-a", "key-b"], cooldown_seconds=60)
        pool.mark_cooldown("key-a")
        pool.mark_cooldown("key-b")
        # All in cooldown, but still hands one out
        got = pool.get_key()
        self.assertIn(got, ["key-a", "key-b"])

    def test_available_count(self):
        pool = KeyPool(["key-a", "key-b", "key-c"], cooldown_seconds=60)
        self.assertEqual(pool.available_count, 3)
        pool.mark_cooldown("key-a")
        self.assertEqual(pool.available_count, 2)
        pool.mark_cooldown("key-b")
        self.assertEqual(pool.available_count, 1)
        pool.mark_cooldown("key-c")
        self.assertEqual(pool.available_count, 0)

    def test_empty_keys_raises(self):
        with self.assertRaises(ValueError):
            KeyPool([])

    def test_intent_router_requires_key_or_pool(self):
        with self.assertRaises(ValueError):
            IntentRouter()


if __name__ == "__main__":
    unittest.main()
