import unittest
from unittest.mock import patch


class ChatApiTest(unittest.TestCase):
    def test_get_conversation_messages_endpoint_returns_store_messages(self):
        import app as app_module

        with patch.object(
            app_module.conversation_store,
            "get_messages",
            return_value=[
                {"role": "user", "content": "你好"},
                {"role": "assistant", "content": "您好，请问需要什么帮助？"},
            ],
        ) as mocked_get_messages:
            client = app_module.app.test_client()
            response = client.get("/conversations/conv-123/messages")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["conversationId"], "conv-123")
        self.assertEqual(payload["count"], 2)
        self.assertEqual(payload["messages"][0]["role"], "user")
        mocked_get_messages.assert_called_once_with("conv-123")

    def test_chat_endpoint_returns_recommendations(self):
        import app as app_module

        expected = {
            "answer": "已找到推荐",
            "source": "anthropic+tools",
            "route": {"skills": ["property_support"], "tools": ["search_properties"], "systemPrompt": None},
            "recommendations": {
                "title": "酒店推荐",
                "subtitle": "上海",
                "count": 1,
                "cards": [
                    {
                        "id": "192",
                        "name": "测试民宿",
                        "detailUrl": "http://localhost:5400/property/192",
                    }
                ],
            },
        }

        with patch.object(app_module.chat_service, "chat", return_value=expected):
            client = app_module.app.test_client()
            response = client.post(
                "/chat",
                json={"message": "推荐上海高分酒店"},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["answer"], "已找到推荐")
        self.assertEqual(payload["source"], "anthropic+tools")
        self.assertEqual(payload["recommendations"], expected["recommendations"])
        self.assertTrue(payload["conversationId"])

    def test_chat_endpoint_resolves_user_context_from_authorization_header(self):
        import app as app_module

        expected = {
            "answer": "已找到推荐",
            "source": "anthropic+tools",
            "route": {"skills": [], "tools": [], "systemPrompt": None},
            "recommendations": None,
        }

        with patch.object(
            app_module.auth_identity_service,
            "resolve_user_context",
            return_value={"id": 12, "username": "alice", "role": "USER"},
        ) as mocked_identity:
            with patch.object(app_module.chat_service, "chat", return_value=expected):
                client = app_module.app.test_client()
                response = client.post(
                    "/chat",
                    headers={"Authorization": "Bearer dev-token-12"},
                    json={
                        "message": "查一下我的订单",
                        "userContext": {"id": 999, "username": "fake", "role": "ADMIN"},
                    },
                )

        self.assertEqual(response.status_code, 200)
        mocked_identity.assert_called_once()
        args, kwargs = mocked_identity.call_args
        self.assertEqual(args[0], "Bearer dev-token-12")
        self.assertEqual(
            kwargs["fallback_user_context"],
            {"id": 999, "username": "fake", "role": "ADMIN"},
        )


if __name__ == "__main__":
    unittest.main()
