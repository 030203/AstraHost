import unittest
from datetime import datetime, timedelta, timezone

from services.conversation_store import ConversationStore


class ConversationStoreTest(unittest.TestCase):
    def test_append_and_get_recent_messages(self):
        store = ConversationStore(ttl_seconds=60, max_messages=3)

        store.append_messages(
            "conv-1",
            [
                {"role": "user", "content": "m1"},
                {"role": "assistant", "content": "m2"},
                {"role": "user", "content": "m3"},
                {"role": "assistant", "content": "m4"},
            ],
        )

        self.assertEqual(
            store.get_messages("conv-1"),
            [
                {"role": "assistant", "content": "m2"},
                {"role": "user", "content": "m3"},
                {"role": "assistant", "content": "m4"},
            ],
        )

    def test_expired_conversation_is_removed(self):
        current = datetime(2026, 6, 2, tzinfo=timezone.utc)

        class Clock:
            def __init__(self):
                self.value = current

            def now(self):
                return self.value

        clock = Clock()
        store = ConversationStore(ttl_seconds=30, max_messages=5, clock=clock.now)
        store.append_messages("conv-2", [{"role": "user", "content": "hello"}])

        clock.value = current + timedelta(seconds=31)

        self.assertEqual(store.get_messages("conv-2"), [])


if __name__ == "__main__":
    unittest.main()
