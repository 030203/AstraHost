import unittest
from types import SimpleNamespace

from services.chat_service import ChatService
from services.skill_service import SkillRoute


class ChatServicePromptTest(unittest.TestCase):
    def test_system_prompt_includes_action_confirmation_guidance(self):
        service = ChatService(
            model_client=None,
            tool_service=None,
            skill_service=None,
            default_system_prompt="Base prompt.",
            config=None,
        )

        prompt = service._build_system_prompt(
            user_context={"id": 12, "username": "demo", "role": "USER"},
            skill_route=SkillRoute(
                active_skill_names=("booking_support",),
                tool_names=("cancel_booking",),
                system_prompt="Booking skill prompt.",
            ),
        )

        self.assertIn("pending_confirmation", prompt)
        self.assertIn("has NOT been executed", prompt)
        self.assertIn("confirmation_token", prompt)
        self.assertIn("Never say the action succeeded", prompt)
        self.assertIn("Booking skill prompt.", prompt)

    def test_build_recommendation_update_extracts_property_cards(self):
        service = ChatService(
            model_client=None,
            tool_service=None,
            skill_service=None,
            default_system_prompt="Base prompt.",
            config=None,
        )

        tool_result = {
            "ok": True,
            "tool": "search_properties",
            "result": {
                "query": {
                    "city": "深圳",
                    "district": "南山",
                    "minPrice": 500,
                    "maxPrice": 1000,
                    "facilities": ["含早餐", "双床房"],
                },
                "items": [
                    {
                        "id": 101,
                        "name": "深圳湾观海酒店",
                        "city": "深圳",
                        "district": "南山",
                        "address": "深圳市南山区后海大道 18 号",
                        "type": "高端精选",
                        "featured": True,
                        "rating": 4.8,
                        "reviewCount": 268,
                        "minPrice": 799,
                        "summary": "临海景观房，适合商务和休闲入住。",
                        "facilities": ["含早餐", "双床房", "停车场"],
                        "imageUrl": "https://example.com/hotel-1.jpg",
                        "detailUrl": "https://example.com/hotel/101",
                        "bookingUrl": "https://example.com/hotel/101/book",
                    }
                ],
            },
        }

        update = service._build_recommendation_update("search_properties", tool_result)

        self.assertTrue(update["reset"])
        self.assertEqual(update["title"], "为你找到的酒店推荐 (1)")
        self.assertIn("深圳", update["subtitle"])
        self.assertIn("500-1000 元", update["subtitle"])
        self.assertEqual(len(update["cards"]), 1)
        card = update["cards"][0]
        self.assertEqual(card["id"], "101")
        self.assertEqual(card["name"], "深圳湾观海酒店")
        self.assertEqual(card["priceLabel"], "¥799 起/晚")
        self.assertEqual(card["rating"], "4.8")
        self.assertIn("含早餐", card["highlights"])
        self.assertEqual(card["detailUrl"], "https://example.com/hotel/101")
        self.assertEqual(card["bookingUrl"], "https://example.com/hotel/101/book")

    def test_recommendation_state_merges_detail_into_existing_card(self):
        service = ChatService(
            model_client=None,
            tool_service=None,
            skill_service=None,
            default_system_prompt="Base prompt.",
            config=None,
        )

        state = service._new_recommendation_state()
        service._merge_recommendation_state(
            state,
            {
                "reset": True,
                "title": "为你找到的酒店推荐 (1)",
                "subtitle": "深圳 · 商务出行",
                "cards": [
                    {
                        "id": "101",
                        "name": "深圳湾观海酒店",
                        "summary": "",
                        "highlights": ["含早餐"],
                        "detailUrl": "",
                    }
                ],
            },
        )
        service._merge_recommendation_state(
            state,
            {
                "reset": False,
                "title": "酒店详情",
                "subtitle": "",
                "cards": [
                    {
                        "id": "101",
                        "name": "深圳湾观海酒店",
                        "summary": "临海景观房，适合商务和休闲入住。",
                        "highlights": ["双床房", "停车场"],
                        "detailUrl": "https://example.com/hotel/101",
                    }
                ],
            },
        )

        recommendations = service._finalize_recommendation_state(
            state,
            user_message="推荐一家深圳南山高分酒店",
            skill_route=SkillRoute(
                active_skill_names=("property_support",),
                tool_names=("search_properties",),
                system_prompt="",
            ),
        )

        self.assertEqual(recommendations["count"], 1)
        card = recommendations["cards"][0]
        self.assertEqual(card["summary"], "临海景观房，适合商务和休闲入住。")
        self.assertEqual(card["detailUrl"], "https://example.com/hotel/101")
        self.assertEqual(card["highlights"], ["含早餐", "双床房", "停车场"])


    def test_build_property_card_falls_back_to_frontend_detail_url(self):
        class ConfigStub:
            @staticmethod
            def frontend_base_url():
                return "http://localhost:5400"

        service = ChatService(
            model_client=None,
            tool_service=None,
            skill_service=None,
            default_system_prompt="Base prompt.",
            config=ConfigStub(),
        )

        card = service._build_property_card(
            {
                "id": 192,
                "name": "测试民宿",
                "city": "上海",
                "district": "浦东",
            }
        )

        self.assertEqual(card["detailUrl"], "http://localhost:5400/property/192")

    def test_chat_uses_conversation_history_and_stores_completed_turn(self):
        class ModelClientStub:
            def __init__(self):
                self.calls = []

            def create_message(self, messages, tools, system_prompt=None):
                self.calls.append(
                    {
                        "messages": messages,
                        "tools": tools,
                        "system_prompt": system_prompt,
                    }
                )
                return SimpleNamespace(
                    stop_reason="end_turn",
                    content=[SimpleNamespace(type="text", text="这是基于上下文的回答")],
                )

        class ToolServiceStub:
            def get_tool_definitions(self, allowed_tool_names=None, user_context=None):
                return []

        class SkillServiceStub:
            def resolve(self, message, user_context=None):
                return SkillRoute(
                    active_skill_names=(),
                    tool_names=(),
                    system_prompt="",
                )

        class ConversationStoreStub:
            def __init__(self):
                self.saved = []

            def get_messages(self, conversation_id):
                return [
                    {"role": "user", "content": "之前问过的问题"},
                    {"role": "assistant", "content": "之前给过的回答"},
                ]

            def append_messages(self, conversation_id, new_messages):
                self.saved.append((conversation_id, new_messages))

        model_client = ModelClientStub()
        conversation_store = ConversationStoreStub()
        service = ChatService(
            model_client=model_client,
            tool_service=ToolServiceStub(),
            skill_service=SkillServiceStub(),
            default_system_prompt="Base prompt.",
            config=SimpleNamespace(tool_call_max_steps=lambda: 3),
            conversation_store=conversation_store,
        )

        result = service.chat(
            "继续说下第二个方案",
            user_context={"id": 12, "username": "alice", "role": "USER"},
            conversation_id="conv-001",
        )

        self.assertEqual(result["answer"], "这是基于上下文的回答")
        self.assertEqual(
            model_client.calls[0]["messages"],
            [
                {"role": "user", "content": "之前问过的问题"},
                {"role": "assistant", "content": "之前给过的回答"},
                {"role": "user", "content": "继续说下第二个方案"},
            ],
        )
        self.assertEqual(
            conversation_store.saved,
            [
                (
                    "conv-001",
                    [
                        {"role": "user", "content": "继续说下第二个方案"},
                        {"role": "assistant", "content": "这是基于上下文的回答"},
                    ],
                )
            ],
        )

    def test_recommendations_are_hidden_for_non_recommendation_property_requests(self):
        service = ChatService(
            model_client=None,
            tool_service=None,
            skill_service=None,
            default_system_prompt="Base prompt.",
            config=None,
        )

        state = service._new_recommendation_state()
        service._merge_recommendation_state(
            state,
            {
                "reset": True,
                "title": "酒店推荐",
                "subtitle": "北京",
                "cards": [
                    {
                        "id": "632",
                        "name": "北京远航国际酒店",
                        "detailUrl": "http://localhost:5400/property/632",
                    }
                ],
            },
        )

        recommendations = service._finalize_recommendation_state(
            state,
            user_message="2026.6.9号入住，6月10日退房，住1晚，先查一下库存再预订",
            skill_route=SkillRoute(
                active_skill_names=("property_support",),
                tool_names=("search_properties", "get_property_detail"),
                system_prompt="",
            ),
        )

        self.assertIsNone(recommendations)


if __name__ == "__main__":
    unittest.main()
