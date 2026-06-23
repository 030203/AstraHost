import unittest

from services.action_confirmation_service import ActionConfirmationService
from services.tool_service import ToolService, ToolSpec


class AllowAllPolicy:
    def is_role_allowed(self, spec, user_context):
        return True


class ToolServiceActionConfirmationTest(unittest.TestCase):
    def build_service(self, handler):
        service = object.__new__(ToolService)
        service.access_policy = AllowAllPolicy()
        service.action_confirmation_service = ActionConfirmationService(
            token_factory=lambda: "act_tool_test"
        )
        service._tool_registry = {
            "danger_action": ToolSpec(
                name="danger_action",
                description="Dangerous test action.",
                properties={"item_id": {"type": "integer"}},
                handler=handler,
                required=("item_id",),
                mode="action",
                allowed_roles=None,
            )
        }
        return service

    def test_action_pending_response_can_include_business_confirmation_summary(self):
        calls = []

        def handler(user_context=None, **kwargs):
            calls.append(kwargs)
            return {"executed": True}

        service = self.build_service(handler)
        service._build_pending_action_summary = lambda tool_name, arguments, user_context=None: {
            "action": tool_name,
            "target_label": f"项目 {arguments['item_id']}",
            "message": "已创建确认动作。",
            "confirmation_text": f"确认执行项目 {arguments['item_id']}",
        }

        result = service.execute(
            "danger_action",
            {"item_id": 1},
            user_context={"id": 12, "role": "USER"},
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["result"]["status"], "pending_confirmation")
        self.assertEqual(result["result"]["message"], "已创建确认动作。")
        self.assertEqual(
            result["result"]["pending_action"]["confirmation_text"],
            "确认执行项目 1",
        )
        self.assertEqual(
            result["result"]["pending_action"]["summary"]["target_label"],
            "项目 1",
        )
        self.assertEqual(calls, [])

    def test_action_without_token_creates_pending_action_without_executing(self):
        calls = []

        def handler(user_context=None, **kwargs):
            calls.append(kwargs)
            return {"executed": True}

        service = self.build_service(handler)

        result = service.execute(
            "danger_action",
            {"item_id": 1},
            user_context={"id": 12, "role": "USER"},
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["result"]["status"], "pending_confirmation")
        self.assertEqual(
            result["result"]["pending_action"]["token"],
            "act_tool_test",
        )
        self.assertEqual(calls, [])

    def test_action_with_matching_token_executes_handler(self):
        calls = []

        def handler(user_context=None, **kwargs):
            calls.append(kwargs)
            return {"executed": True, "arguments": kwargs}

        service = self.build_service(handler)
        pending = service.execute(
            "danger_action",
            {"item_id": 1},
            user_context={"id": 12, "role": "USER"},
        )
        token = pending["result"]["pending_action"]["token"]

        result = service.execute(
            "danger_action",
            {"item_id": 1, "confirmation_token": token},
            user_context={"id": 12, "role": "USER"},
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["result"], {"executed": True, "arguments": {"item_id": 1}})
        self.assertEqual(calls, [{"item_id": 1}])

    def test_action_with_token_only_reuses_pending_arguments(self):
        calls = []

        def handler(user_context=None, **kwargs):
            calls.append(kwargs)
            return {"executed": True, "arguments": kwargs}

        service = self.build_service(handler)
        pending = service.execute(
            "danger_action",
            {"item_id": 1},
            user_context={"id": 12, "role": "USER"},
        )
        token = pending["result"]["pending_action"]["token"]

        result = service.execute(
            "danger_action",
            {"confirmation_token": token},
            user_context={"id": 12, "role": "USER"},
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["result"], {"executed": True, "arguments": {"item_id": 1}})
        self.assertEqual(calls, [{"item_id": 1}])

    def test_action_with_mismatched_token_arguments_is_rejected(self):
        calls = []

        def handler(user_context=None, **kwargs):
            calls.append(kwargs)
            return {"executed": True}

        service = self.build_service(handler)
        pending = service.execute(
            "danger_action",
            {"item_id": 1},
            user_context={"id": 12, "role": "USER"},
        )
        token = pending["result"]["pending_action"]["token"]

        result = service.execute(
            "danger_action",
            {"item_id": 2, "confirmation_token": token},
            user_context={"id": 12, "role": "USER"},
        )

        self.assertFalse(result["ok"])
        self.assertIn("不匹配", result["error"])
        self.assertEqual(calls, [])

    def test_action_tool_definition_includes_confirmation_token(self):
        service = self.build_service(lambda user_context=None, **kwargs: {})

        definition = service.get_tool_definitions()[0]

        self.assertIn("confirmation_token", definition["input_schema"]["properties"])
        self.assertEqual(definition["input_schema"]["required"], [])
        self.assertIn("写操作", definition["description"])

    def test_action_without_token_still_requires_original_arguments(self):
        calls = []

        def handler(user_context=None, **kwargs):
            calls.append(kwargs)
            return {"executed": True}

        service = self.build_service(handler)

        result = service.execute(
            "danger_action",
            {},
            user_context={"id": 12, "role": "USER"},
        )

        self.assertFalse(result["ok"])
        self.assertIn("缺少必填参数", result["error"])
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
