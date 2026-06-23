import unittest
from types import SimpleNamespace

from services.tool_access_policy import ToolAccessPolicy


class FakeBackend:
    def __init__(self):
        self.notifications = [
            {"id": 7, "user": {"id": 12}},
            {"id": 8, "user": {"id": 13}},
        ]
        self.properties = {
            21: {"property": {"id": 21, "merchantId": 34}},
            22: {"property": {"id": 22, "merchantId": 35}},
        }

    def list_notifications(self, user_id=None, unread_only=False):
        return {
            "items": [
                item
                for item in self.notifications
                if user_id is None or item["user"]["id"] == user_id
            ]
        }

    def get_property_detail(self, property_id):
        return {"item": self.properties[property_id]}

    def list_properties(self, merchant_id=None):
        return {
            "items": [
                {"id": payload["property"]["id"]}
                for payload in self.properties.values()
                if merchant_id is None or payload["property"]["merchantId"] == merchant_id
            ]
        }


class ToolAccessPolicyTest(unittest.TestCase):
    def setUp(self):
        self.policy = ToolAccessPolicy(FakeBackend())

    def test_resolve_role_normalizes_input(self):
        self.assertEqual(self.policy.resolve_role({"role": " merchant "}), "MERCHANT")
        self.assertEqual(self.policy.resolve_role({}), "")
        self.assertEqual(self.policy.resolve_role(None), "")

    def test_is_role_allowed_requires_matching_role(self):
        spec = SimpleNamespace(allowed_roles=("USER", "ADMIN"))

        self.assertTrue(self.policy.is_role_allowed(spec, {"role": "USER"}))
        self.assertFalse(self.policy.is_role_allowed(spec, {"role": "MERCHANT"}))
        self.assertFalse(self.policy.is_role_allowed(spec, None))

    def test_current_ids_require_numeric_values(self):
        self.assertEqual(self.policy.current_user_id({"id": "12"}), 12)
        self.assertEqual(self.policy.current_merchant_id({"merchantId": "34"}), 34)

        with self.assertRaises(ValueError):
            self.policy.current_user_id({"id": "guest_10001"})
        with self.assertRaises(ValueError):
            self.policy.current_merchant_id({})

    def test_booking_access_by_role(self):
        booking = {"user": {"id": 12}, "property": {"merchantId": 34}}

        self.assertTrue(self.policy.can_access_booking(booking, {"role": "ADMIN"}))
        self.assertTrue(self.policy.can_access_booking(booking, {"role": "USER", "id": 12}))
        self.assertFalse(self.policy.can_access_booking(booking, {"role": "USER", "id": 13}))
        self.assertTrue(
            self.policy.can_access_booking(
                booking, {"role": "MERCHANT", "merchantId": 34}
            )
        )
        self.assertFalse(
            self.policy.can_access_booking(
                booking, {"role": "MERCHANT", "merchantId": 35}
            )
        )
        self.assertFalse(self.policy.can_access_booking(booking, None))

    def test_payment_access_by_role(self):
        payment = {
            "booking": {
                "user": {"id": 12},
                "property": {"merchantId": 34},
            }
        }

        self.assertTrue(self.policy.can_access_payment(payment, {"role": "ADMIN"}))
        self.assertTrue(self.policy.can_access_payment(payment, {"role": "USER", "id": 12}))
        self.assertFalse(self.policy.can_access_payment(payment, {"role": "USER", "id": 13}))
        self.assertTrue(
            self.policy.can_access_payment(
                payment, {"role": "MERCHANT", "merchantId": 34}
            )
        )
        self.assertFalse(self.policy.can_access_payment(payment, None))

    def test_notification_access_and_ownership(self):
        notification = {"id": 7, "user": {"id": 12}}

        self.assertTrue(self.policy.can_access_notification(notification, {"role": "ADMIN"}))
        self.assertTrue(
            self.policy.can_access_notification(notification, {"role": "USER", "id": 12})
        )
        self.assertFalse(
            self.policy.can_access_notification(notification, {"role": "USER", "id": 13})
        )
        self.assertFalse(self.policy.can_access_notification(notification, None))

        self.policy.ensure_notification_owned(7, {"role": "USER", "id": 12})
        with self.assertRaises(ValueError):
            self.policy.ensure_notification_owned(8, {"role": "USER", "id": 12})

    def test_property_ownership_helpers(self):
        self.policy.ensure_property_owned_by_current_merchant(
            21, {"role": "MERCHANT", "merchantId": 34}
        )
        with self.assertRaises(ValueError):
            self.policy.ensure_property_owned_by_current_merchant(
                22, {"role": "MERCHANT", "merchantId": 34}
            )

        self.assertEqual(
            self.policy.list_current_merchant_property_ids(
                {"role": "MERCHANT", "merchantId": 34}
            ),
            [21],
        )


if __name__ == "__main__":
    unittest.main()

