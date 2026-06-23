import unittest
from datetime import datetime, timedelta, timezone

from services.action_confirmation_service import ActionConfirmationService


class ActionConfirmationServiceTest(unittest.TestCase):
    def test_create_and_consume_pending_action(self):
        current_time = datetime(2026, 6, 1, tzinfo=timezone.utc)
        service = ActionConfirmationService(
            ttl_seconds=300,
            token_factory=lambda: "act_test",
            clock=lambda: current_time,
        )

        pending_action = service.create(
            "cancel_booking",
            {"booking_id": 1, "reason": "change of plans"},
            user_context={"id": 12, "role": "USER"},
            summary={"confirmation_text": "确认取消订单 BOOK20250401001"},
        )
        consumed = service.consume(
            pending_action.token,
            "cancel_booking",
            {"booking_id": 1, "reason": "change of plans"},
            user_context={"id": 12, "role": "USER"},
        )

        self.assertEqual(consumed.token, "act_test")
        self.assertEqual(
            pending_action.to_response()["confirmation_text"],
            "确认取消订单 BOOK20250401001",
        )
        with self.assertRaises(ValueError):
            service.consume(
                pending_action.token,
                "cancel_booking",
                {"booking_id": 1, "reason": "change of plans"},
                user_context={"id": 12, "role": "USER"},
            )

    def test_rejects_different_user(self):
        service = ActionConfirmationService(
            ttl_seconds=300,
            token_factory=lambda: "act_user",
        )
        pending_action = service.create(
            "mark_notification_read",
            {"notification_id": 7},
            user_context={"id": 12, "role": "USER"},
        )

        with self.assertRaises(ValueError):
            service.consume(
                pending_action.token,
                "mark_notification_read",
                {"notification_id": 7},
                user_context={"id": 13, "role": "USER"},
            )

    def test_rejects_different_arguments(self):
        service = ActionConfirmationService(
            ttl_seconds=300,
            token_factory=lambda: "act_args",
        )
        pending_action = service.create(
            "check_in_booking",
            {"booking_id": 1},
            user_context={"id": 12, "role": "USER"},
        )

        with self.assertRaises(ValueError):
            service.consume(
                pending_action.token,
                "check_in_booking",
                {"booking_id": 2},
                user_context={"id": 12, "role": "USER"},
            )

    def test_allows_token_only_confirmation_to_reuse_stored_arguments(self):
        service = ActionConfirmationService(
            ttl_seconds=300,
            token_factory=lambda: "act_token_only",
        )
        pending_action = service.create(
            "check_in_booking",
            {"booking_id": 1},
            user_context={"id": 12, "role": "USER"},
        )

        consumed = service.consume(
            pending_action.token,
            "check_in_booking",
            {},
            user_context={"id": 12, "role": "USER"},
        )

        self.assertEqual(consumed.arguments, {"booking_id": 1})

    def test_rejects_expired_token(self):
        current_time = datetime(2026, 6, 1, tzinfo=timezone.utc)

        def clock():
            return current_time

        service = ActionConfirmationService(
            ttl_seconds=1,
            token_factory=lambda: "act_expired",
            clock=clock,
        )
        pending_action = service.create(
            "check_out_booking",
            {"booking_id": 1},
            user_context={"id": 12, "role": "USER"},
        )

        current_time += timedelta(seconds=2)
        with self.assertRaises(ValueError):
            service.consume(
                pending_action.token,
                "check_out_booking",
                {"booking_id": 1},
                user_context={"id": 12, "role": "USER"},
            )


if __name__ == "__main__":
    unittest.main()
