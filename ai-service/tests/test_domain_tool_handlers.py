import unittest

from services.domain_tool_handlers import (
    BookingToolHandler,
    NotificationToolHandler,
    PaymentToolHandler,
)
from services.tool_access_policy import ToolAccessPolicy


class FakeBackend:
    def __init__(self):
        self.calls = []
        self.bookings = [
            {"id": 1, "user": {"id": 12}, "property": {"merchantId": 34}},
            {"id": 2, "user": {"id": 13}, "property": {"merchantId": 35}},
        ]
        self.payments = [
            {
                "id": 10,
                "booking": {
                    "user": {"id": 12},
                    "property": {"merchantId": 34},
                },
            },
            {
                "id": 11,
                "booking": {
                    "user": {"id": 13},
                    "property": {"merchantId": 35},
                },
            },
        ]
        self.notifications = [
            {"id": 20, "user": {"id": 12}},
            {"id": 21, "user": {"id": 13}},
        ]

    def list_bookings(self, **kwargs):
        self.calls.append(("list_bookings", kwargs))
        return {
            "items": [
                item
                for item in self.bookings
                if kwargs.get("user_id") in (None, item["user"]["id"])
                and kwargs.get("merchant_id") in (None, item["property"]["merchantId"])
            ],
            "count": len(self.bookings),
        }

    def get_booking_detail(self, booking_id):
        self.calls.append(("get_booking_detail", {"booking_id": booking_id}))
        return {"item": next(item for item in self.bookings if item["id"] == booking_id)}

    def cancel_booking(self, booking_id, reason):
        self.calls.append(("cancel_booking", {"booking_id": booking_id, "reason": reason}))
        return {"id": booking_id, "status": "cancelled"}

    def create_booking(self, **kwargs):
        self.calls.append(("create_booking", kwargs))
        return {"id": 88, "status": "PENDING", "bookingNumber": "BKNEW001"}

    def list_payments(self, **kwargs):
        self.calls.append(("list_payments", kwargs))
        return {
            "items": [
                item
                for item in self.payments
                if kwargs.get("user_id") in (None, item["booking"]["user"]["id"])
                and kwargs.get("merchant_id")
                in (None, item["booking"]["property"]["merchantId"])
            ],
            "count": len(self.payments),
        }

    def get_payment_detail(self, payment_id):
        self.calls.append(("get_payment_detail", {"payment_id": payment_id}))
        return {"item": next(item for item in self.payments if item["id"] == payment_id)}

    def create_payment(self, **kwargs):
        self.calls.append(("create_payment", kwargs))
        return {"id": 66, "status": "PENDING", "paymentNumber": "PAYNEW001"}

    def process_payment(self, payment_id, transaction_id):
        self.calls.append(("process_payment", {"payment_id": payment_id, "transaction_id": transaction_id}))
        return {"id": payment_id, "status": "SUCCESS", "transactionId": transaction_id}

    def list_notifications(self, user_id=None, unread_only=False):
        self.calls.append(
            ("list_notifications", {"user_id": user_id, "unread_only": unread_only})
        )
        return {
            "items": [
                item
                for item in self.notifications
                if user_id is None or item["user"]["id"] == user_id
            ],
            "count": len(self.notifications),
        }

    def get_unread_notification_count(self, user_id):
        self.calls.append(("get_unread_notification_count", {"user_id": user_id}))
        return {"count": 3}

    def mark_notification_read(self, notification_id):
        self.calls.append(("mark_notification_read", {"notification_id": notification_id}))
        return {"id": notification_id, "read": True}

    def mark_all_notifications_read(self, user_id):
        self.calls.append(("mark_all_notifications_read", {"user_id": user_id}))
        return {"updated": 3}


class DomainToolHandlersTest(unittest.TestCase):
    def setUp(self):
        self.backend = FakeBackend()
        self.policy = ToolAccessPolicy(self.backend)
        self.booking_handler = BookingToolHandler(self.backend, self.policy)
        self.payment_handler = PaymentToolHandler(self.backend, self.policy)
        self.notification_handler = NotificationToolHandler(self.backend, self.policy)

    def test_user_booking_list_is_scoped_to_current_user(self):
        result = self.booking_handler.list_bookings(
            user_context={"role": "USER", "id": 12},
            user_id=13,
            merchant_id=35,
        )

        self.assertEqual([item["id"] for item in result["items"]], [1])
        self.assertEqual(
            self.backend.calls[-1],
            ("list_bookings", {"user_id": 12}),
        )

    def test_merchant_booking_list_is_scoped_to_current_merchant(self):
        result = self.booking_handler.list_bookings(
            user_context={"role": "MERCHANT", "merchantId": 34},
            user_id=13,
        )

        self.assertEqual([item["id"] for item in result["items"]], [1])
        self.assertEqual(
            self.backend.calls[-1],
            ("list_bookings", {"merchant_id": 34}),
        )

    def test_booking_detail_rejects_wrong_user(self):
        with self.assertRaises(ValueError):
            self.booking_handler.get_booking_detail(
                2, user_context={"role": "USER", "id": 12}
            )

    def test_booking_action_checks_access_before_mutation(self):
        result = self.booking_handler.cancel_booking(
            1,
            "changed plan",
            user_context={"role": "USER", "id": 12},
        )

        self.assertEqual(result["status"], "cancelled")
        self.assertIn(
            ("cancel_booking", {"booking_id": 1, "reason": "changed plan"}),
            self.backend.calls,
        )

        with self.assertRaises(ValueError):
            self.booking_handler.cancel_booking(
                2,
                "changed plan",
                user_context={"role": "USER", "id": 12},
            )

    def test_create_booking_uses_current_user_scope(self):
        result = self.booking_handler.create_booking(
            room_type_id=1093,
            check_in_date="2026-06-20",
            check_out_date="2026-06-22",
            number_of_guests=2,
            contact_name="Alice",
            contact_phone="13800138000",
            user_context={"role": "USER", "id": 12},
        )

        self.assertEqual(result["bookingNumber"], "BKNEW001")
        self.assertIn(
            (
                "create_booking",
                {
                    "user_id": 12,
                    "room_type_id": 1093,
                    "check_in_date": "2026-06-20",
                    "check_out_date": "2026-06-22",
                    "number_of_guests": 2,
                    "contact_name": "Alice",
                    "contact_phone": "13800138000",
                    "adult_count": 1,
                    "child_count": 0,
                    "room_id": None,
                    "coupon_id": None,
                    "special_requests": None,
                    "contact_email": None,
                },
            ),
            self.backend.calls,
        )

    def test_payment_list_and_detail_are_scoped(self):
        result = self.payment_handler.list_payments(
            user_context={"role": "MERCHANT", "merchantId": 34},
            user_id=13,
        )

        self.assertEqual([item["id"] for item in result["items"]], [10])
        self.assertEqual(
            self.backend.calls[-1],
            ("list_payments", {"merchant_id": 34}),
        )

        with self.assertRaises(ValueError):
            self.payment_handler.get_payment_detail(
                11, user_context={"role": "USER", "id": 12}
            )

    def test_payment_actions_check_access_before_mutation(self):
        result = self.payment_handler.create_payment(
            booking_id=1,
            payment_method="ALIPAY",
            payment_type="FULL",
            amount=299.0,
            user_context={"role": "USER", "id": 12},
        )

        self.assertEqual(result["paymentNumber"], "PAYNEW001")
        self.assertIn(
            (
                "create_payment",
                {
                    "booking_id": 1,
                    "payment_method": "ALIPAY",
                    "payment_type": "FULL",
                    "amount": 299.0,
                    "remark": None,
                    "status": None,
                },
            ),
            self.backend.calls,
        )

        processed = self.payment_handler.process_payment(
            payment_id=10,
            transaction_id="TXN-001",
            user_context={"role": "USER", "id": 12},
        )

        self.assertEqual(processed["status"], "SUCCESS")
        self.assertIn(
            ("process_payment", {"payment_id": 10, "transaction_id": "TXN-001"}),
            self.backend.calls,
        )

        with self.assertRaises(ValueError):
            self.payment_handler.create_payment(
                booking_id=2,
                payment_method="ALIPAY",
                payment_type="FULL",
                amount=199.0,
                user_context={"role": "USER", "id": 12},
            )

    def test_notifications_are_scoped_to_current_user(self):
        result = self.notification_handler.list_notifications(
            user_context={"role": "USER", "id": 12},
            user_id=13,
            unread_only=True,
        )

        self.assertEqual([item["id"] for item in result["items"]], [20])
        self.assertEqual(
            self.backend.calls[-1],
            ("list_notifications", {"user_id": 12, "unread_only": True}),
        )

    def test_notification_actions_use_current_user_scope(self):
        self.notification_handler.mark_notification_read(
            20,
            user_context={"role": "USER", "id": 12},
        )
        self.assertIn(
            ("mark_notification_read", {"notification_id": 20}),
            self.backend.calls,
        )

        with self.assertRaises(ValueError):
            self.notification_handler.mark_notification_read(
                21,
                user_context={"role": "USER", "id": 12},
            )

        self.notification_handler.mark_all_notifications_read(
            13,
            user_context={"role": "USER", "id": 12},
        )
        self.assertEqual(
            self.backend.calls[-1],
            ("mark_all_notifications_read", {"user_id": 12}),
        )


if __name__ == "__main__":
    unittest.main()
