import unittest

from services.auth_identity_service import AuthIdentityService


class StubBackendAPIService:
    def __init__(self, user_payload=None, merchant_payload=None):
        self.user_payload = user_payload or {}
        self.merchant_payload = merchant_payload or {}
        self.calls = []

    def get_user_detail(self, user_id):
        self.calls.append(("get_user_detail", user_id))
        return {"item": self.user_payload}

    def get_merchant_by_user_id(self, user_id):
        self.calls.append(("get_merchant_by_user_id", user_id))
        return {"item": self.merchant_payload}


class AuthIdentityServiceTest(unittest.TestCase):
    def test_resolves_user_context_from_dev_token(self):
        backend = StubBackendAPIService(
            user_payload={"id": 12, "username": "alice", "role": "USER"}
        )
        service = AuthIdentityService(backend)

        context = service.resolve_user_context("Bearer dev-token-12")

        self.assertEqual(
            context,
            {
                "id": 12,
                "username": "alice",
                "role": "USER",
            },
        )
        self.assertEqual(backend.calls, [("get_user_detail", 12)])

    def test_resolves_merchant_context_and_merchant_id_from_dev_token(self):
        backend = StubBackendAPIService(
            user_payload={"id": 7, "username": "merchant1", "role": "MERCHANT"},
            merchant_payload={"id": 3, "merchantName": "Demo Merchant"},
        )
        service = AuthIdentityService(backend)

        context = service.resolve_user_context("Bearer dev-token-7")

        self.assertEqual(
            context,
            {
                "id": 7,
                "username": "merchant1",
                "role": "MERCHANT",
                "merchantId": 3,
            },
        )
        self.assertEqual(
            backend.calls,
            [
                ("get_user_detail", 7),
                ("get_merchant_by_user_id", 7),
            ],
        )

    def test_falls_back_to_normalized_user_context_without_token(self):
        backend = StubBackendAPIService()
        service = AuthIdentityService(backend)

        context = service.resolve_user_context(
            None,
            fallback_user_context={
                "id": "99",
                "username": "demo_user",
                "role": "user",
                "merchantId": "",
            },
        )

        self.assertEqual(
            context,
            {
                "id": "99",
                "username": "demo_user",
                "role": "USER",
            },
        )
        self.assertEqual(backend.calls, [])


if __name__ == "__main__":
    unittest.main()
